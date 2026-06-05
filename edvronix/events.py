import re
import random

import frappe
from frappe.utils import flt



def override_invoice_rates(doc, method=None):
	"""
	Before a Sales Invoice is saved, override tuition fee rates from the student's
	latest Program Enrollment, and optionally assign a gender-based cost center
	configured in Edvronix Settings.

	Works for any school — no hardcoded values. Cost centers are optional; if not
	configured in Edvronix Settings the invoice uses item defaults as-is.
	"""
	if not doc.student:
		return

	# Read gender-based cost centers from settings (fully configurable per school)
	settings = frappe.get_cached_doc("Edvronix Settings")
	gender = frappe.db.get_value("Student", doc.student, "gender")

	cost_center = None
	if gender == "Male" and settings.get("male_cost_center"):
		cost_center = settings.male_cost_center
	elif gender == "Female" and settings.get("female_cost_center"):
		cost_center = settings.female_cost_center

	# Safety guard: only apply cost center if it belongs to this invoice's company
	if cost_center:
		cc_company = frappe.db.get_value("Cost Center", cost_center, "company")
		if cc_company != doc.company:
			cost_center = None

	# Get tuition fee from the student's latest submitted Program Enrollment
	enrollment = frappe.get_all(
		"Program Enrollment",
		filters={"student": doc.student, "docstatus": 1},
		fields=["custom_tuition_fee"],
		order_by="creation desc",
		limit=1,
	)

	if not enrollment:
		return

	tuition_fee = enrollment[0].custom_tuition_fee

	# Override tuition item rate and optionally set cost center
	for item in doc.items:
		name = (item.item_name or "").lower()
		code = (item.item_code or "").lower()

		if "tuition" in name or "tuition" in code:
			val = flt(tuition_fee)
			item.rate = val
			item.amount = flt(item.qty) * val
			item.price_list_rate = val
			item.base_price_list_rate = val
			if cost_center:
				item.cost_center = cost_center

	# Prevent Frappe from re-running price list calculations
	doc.ignore_pricing_rule = 1
	doc.calculate_taxes_and_totals()


def generate_student_email(doc, method=None):
	"""
	Auto-generate student_email_id on first insert only.
	Format: {firstname}{lastname}{number}@{schooldomain}.{email_domain}
	Domain = first word of Edvronix Settings.school_name, fallback to company name.
	TLD = Edvronix Settings.email_domain (default: edu.pk).
	Example: "Al-Noor High School", email_domain="edu.pk" → ahmadali32@alnoor.edu.pk
	"""
	if doc.student_email_id:
		return  # Never overwrite an existing email

	school_domain = _get_school_domain()
	email_tld = _get_email_domain()

	first = re.sub(r'[^a-z]', '', (doc.first_name or "").lower())
	last  = re.sub(r'[^a-z]', '', (doc.last_name  or "").lower())
	base  = (first + last) or "student"

	for _ in range(50):
		number = random.randint(10, 9999)
		email  = f"{base}{number}@{school_domain}.{email_tld}"
		if not frappe.db.exists("Student Applicant", {"student_email_id": email}):
			doc.student_email_id = email
			return
	frappe.log_error(
		f"Could not generate unique email for {doc.first_name} {doc.last_name}",
		"Edvronix: student email generation failed"
	)


def _get_email_domain():
	"""Return the email TLD from Edvronix Settings (default: edu.pk)."""
	try:
		tld = frappe.db.get_single_value("Edvronix Settings", "email_domain")
		if tld:
			return tld.strip().lstrip(".")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Edvronix: could not read email_domain from settings")
	return "edu.pk"


def _get_school_domain():
	"""
	Return cleaned first-word domain for email generation.
	Priority: Edvronix Settings.school_name → default company name → "school"
	Takes only the first word, strips non-alphanumeric, lowercases.
	"""
	school_name = None

	try:
		school_name = frappe.db.get_single_value("Edvronix Settings", "school_name")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Edvronix: could not read school_name from settings")

	if not school_name:
		school_name = frappe.defaults.get_global_default("company") or ""

	if not school_name:
		return "school"

	first_word = school_name.strip().split()[0] if school_name.strip() else "school"
	domain = re.sub(r'[^a-z0-9]', '', first_word.lower())
	return domain or "school"


def prevent_enabling_graduated_student(doc, method=None):
	"""
	Block re-enabling a graduated student directly via the Student form.
	The only proper way to reverse a graduation is to cancel the Student Graduation document.
	"""
	if not doc.enabled:
		return  # Student is being disabled — always allowed

	# Check if the student was previously graduated (DB value enabled=0 + reason=Graduated)
	db_values = frappe.db.get_value(
		"Student", doc.name, ["enabled", "reason_for_leaving"], as_dict=True
	)
	if not db_values:
		return  # New student — no check needed

	was_disabled = not db_values.get("enabled")
	was_graduated = db_values.get("reason_for_leaving") == "Graduated"

	if was_disabled and was_graduated:
		# Find the graduation document that graduated this student
		grad_doc = frappe.db.sql(
			"""
			SELECT sg.name
			FROM `tabStudent Graduation` sg
			INNER JOIN `tabGraduation Student Detail` gsd ON gsd.parent = sg.name
			WHERE gsd.student = %s AND sg.docstatus = 1
			ORDER BY sg.graduation_date DESC
			LIMIT 1
			""",
			(doc.name,),
			as_dict=True,
		)

		if grad_doc:
			grad_name = grad_doc[0]["name"]
			frappe.throw(
				f"<b>{doc.student_name}</b> is a graduated student and cannot be re-enabled directly.<br><br>"
				f"To restore this student, please cancel the graduation document: "
				f"<a href='/app/student-graduation/{grad_name}'><b>{grad_name}</b></a>",
				title="Cannot Enable Graduated Student"
			)
		else:
			frappe.throw(
				f"<b>{doc.student_name}</b> is marked as graduated and cannot be re-enabled directly. "
				f"Please find and cancel the related Student Graduation document first.",
				title="Cannot Enable Graduated Student"
			)
