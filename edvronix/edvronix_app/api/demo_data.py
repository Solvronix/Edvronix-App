import frappe
from frappe.utils import today, flt, get_first_day, getdate, add_days
import random

PROGRAMS = [
	"Nursery", "Prep", "Class 1", "Class 2", "Class 3",
	"Class 4", "Class 5", "Class 6", "Class 7", "Class 8"
]

MALE_NAMES = [
	"Ahmed Ali", "Muhammad Hassan", "Usman Khan", "Bilal Ahmed", "Zain Malik",
	"Omar Farooq", "Hamza Sheikh", "Tariq Mehmood", "Asad Iqbal", "Faisal Raza"
]

FEMALE_NAMES = [
	"Fatima Zahra", "Ayesha Siddiqui", "Maryam Noor", "Zainab Khan", "Sara Malik",
	"Hira Ahmed", "Nadia Hassan", "Amna Riaz", "Sana Butt", "Rabia Qureshi"
]

GUARDIAN_NAMES = [
	"Ali Hassan", "Muhammad Farooq", "Khalid Mehmood", "Imran Khan", "Tariq Aziz",
	"Nasir Ahmed", "Shahid Iqbal", "Javed Malik", "Rizwan Sheikh", "Arif Raza",
	"Saeed Butt", "Zahid Hussain", "Adnan Qureshi", "Wasim Baig", "Naveed Aslam"
]

APPLICANT_NAMES = [
	("Hassan", "Raza"), ("Zara", "Khan"), ("Bilal", "Sheikh"), ("Noor", "Ahmed"),
	("Saad", "Malik"), ("Hina", "Butt"), ("Kamran", "Iqbal"), ("Sobia", "Farooq"),
	("Waqar", "Mehmood"), ("Maira", "Hussain"),
]

FEE_ITEMS = [
	("Monthly Tuition Fee", 3500),
	("Examination Fee", 500),
	("Activity Fee", 300),
]


@frappe.whitelist()
def create_demo_data():
	frappe.only_for("System Manager")
	if not frappe.conf.get("allow_demo_data"):
		frappe.throw(
			"Demo data can only be created on development/demo sites. "
			"Add `allow_demo_data: true` to site_config.json to enable."
		)
	results = {}

	results["academic_year"] = _ensure_academic_year()
	results["programs"] = _ensure_programs()
	results["students"] = _ensure_students()
	results["guardians"] = _ensure_guardians()
	results["enrollments"] = _ensure_enrollments()
	results["student_guardians"] = _ensure_student_guardian_links()
	results["invoices"] = _ensure_invoices()
	results["patch_invoice_students"] = _patch_invoice_student_field()
	results["attendance"] = _ensure_attendance()
	results["student_applicants"] = _ensure_student_applicants()
	results["disabled_students"] = _ensure_disabled_demo_students()

	frappe.db.commit()
	return results


# ── Core Records ──────────────────────────────────────────────────────────────

def _ensure_academic_year():
	if frappe.db.exists("Academic Year", "2026-2027"):
		return "exists"
	doc = frappe.get_doc({
		"doctype": "Academic Year",
		"academic_year_name": "2026-2027",
		"year_start_date": "2026-04-01",
		"year_end_date": "2027-03-31",
	})
	doc.insert(ignore_permissions=True)
	return "created"


def _ensure_programs():
	created = []
	for prog in PROGRAMS:
		if not frappe.db.exists("Program", prog):
			doc = frappe.get_doc({
				"doctype": "Program",
				"program_name": prog,
				"program_abbreviation": prog[:4].upper(),
			})
			doc.insert(ignore_permissions=True)
			created.append(prog)
	return {"created": len(created), "skipped": len(PROGRAMS) - len(created)}


def _ensure_students():
	existing = frappe.db.count("Student")
	if existing >= 20:
		return {"created": 0, "skipped": existing}

	created = 0
	all_names = MALE_NAMES + FEMALE_NAMES
	genders = ["Male"] * 10 + ["Female"] * 10

	for i, (name, gender) in enumerate(zip(all_names, genders)):
		parts = name.split(" ", 1)
		first, last = parts[0], (parts[1] if len(parts) > 1 else "")
		email = f"student{i+1}@demo.edvronix.com"

		if frappe.db.exists("Student", {"student_email_id": email}):
			continue

		doc = frappe.get_doc({
			"doctype": "Student",
			"first_name": first,
			"last_name": last,
			"student_email_id": email,
			"gender": gender,
			"date_of_birth": f"201{random.randint(0, 5)}-0{random.randint(1, 9)}-{random.randint(10, 28)}",
			"enabled": 1,
		})
		doc.insert(ignore_permissions=True)
		created += 1

	return {"created": created, "skipped": existing}


def _ensure_guardians():
	existing = frappe.db.count("Guardian")
	if existing >= 15:
		return {"created": 0, "skipped": existing}

	created = 0
	for i, name in enumerate(GUARDIAN_NAMES):
		parts = name.split(" ", 1)
		first, last = parts[0], (parts[1] if len(parts) > 1 else "")
		email = f"guardian{i+1}@demo.edvronix.com"

		if frappe.db.exists("Guardian", {"email_address": email}):
			continue

		doc = frappe.get_doc({
			"doctype": "Guardian",
			"guardian_name": name,
			"first_name": first,
			"last_name": last,
			"email_address": email,
			"mobile_number": f"03{random.randint(10, 49)}{random.randint(1000000, 9999999)}",
		})
		doc.insert(ignore_permissions=True)
		created += 1

	return {"created": created, "skipped": existing}


def _ensure_enrollments():
	existing = frappe.db.count("Program Enrollment", {"docstatus": 1})
	if existing >= 20:
		return {"created": 0, "skipped": existing}

	students = frappe.get_all("Student", filters={"enabled": 1}, fields=["name"], limit=20)
	programs = frappe.get_all("Program", fields=["name"], limit=10)
	if not programs:
		return {"error": "No programs found"}

	created = 0
	for i, student in enumerate(students):
		prog = programs[i % len(programs)]["name"]
		if frappe.db.exists("Program Enrollment", {"student": student["name"], "academic_year": "2026-2027"}):
			continue

		doc = frappe.get_doc({
			"doctype": "Program Enrollment",
			"student": student["name"],
			"academic_year": "2026-2027",
			"program": prog,
			"enrollment_date": "2026-04-01",
			"custom_tuition_fee": 3500,
			"custom_monthy_fee_": 3500,
		})
		doc.insert(ignore_permissions=True)
		doc.submit()
		created += 1

	return {"created": created, "skipped": existing}


# ── Student–Guardian Links ────────────────────────────────────────────────────

def _ensure_student_guardian_links():
	"""Link demo guardians to demo students via the Student.guardians child table."""
	students = frappe.get_all(
		"Student",
		filters={"student_email_id": ["like", "%@demo.edvronix.com"]},
		fields=["name"],
		order_by="creation asc",
	)
	# Guardians may not have email_address set — match by guardian_name
	guardians = frappe.get_all(
		"Guardian",
		filters={"guardian_name": ["in", GUARDIAN_NAMES]},
		fields=["name", "guardian_name"],
		order_by="creation asc",
	)
	# Fallback: if not found by name, use all guardians
	if not guardians:
		guardians = frappe.get_all("Guardian", fields=["name", "guardian_name"], order_by="creation asc", limit=15)

	if not students or not guardians:
		return {"error": "No demo students or guardians found"}

	created = 0
	skipped = 0
	for i, student in enumerate(students):
		guardian = guardians[i // 2 % len(guardians)]  # 2 students per guardian
		student_doc = frappe.get_doc("Student", student["name"])

		already_linked = any(
			row.guardian == guardian["name"]
			for row in student_doc.get("guardians", [])
		)
		if already_linked:
			skipped += 1
			continue

		student_doc.append("guardians", {
			"guardian": guardian["name"],
			"guardian_name": guardian["guardian_name"],
			"relation": "Father",
			"is_emergency_contact": 1,
		})
		student_doc.save(ignore_permissions=True)
		created += 1

	return {"created": created, "skipped": skipped}


# ── Sales Invoices ────────────────────────────────────────────────────────────

def _ensure_invoices():
	existing = frappe.db.count("Sales Invoice", {"docstatus": ["in", [0, 1]]})
	if existing >= 20:
		return {"created": 0, "skipped": existing}

	students = frappe.get_all(
		"Student",
		filters={"enabled": 1, "student_email_id": ["like", "%@demo.edvronix.com"]},
		fields=["name", "student_name"],
		limit=20,
	)
	if not students:
		return {"error": "No demo students found"}

	company = frappe.defaults.get_global_default("company") or (
		frappe.get_all("Company", fields=["name"], limit=1)[0]["name"]
	)
	if not company:
		return {"error": "No company found"}

	income_account = _get_income_account(company)
	debtors_account = _get_debtors_account(company)
	cost_center = frappe.db.get_value("Cost Center", {"company": company, "is_group": 0}, "name")

	if not income_account:
		return {"error": "No income account found"}

	item_codes = []
	for item_name, rate in FEE_ITEMS:
		item = _get_or_create_item(item_name, income_account, company, cost_center)
		if item:
			item_codes.append((item, rate))

	if cost_center and item_codes:
		for item_code, _ in item_codes:
			frappe.db.sql(
				"UPDATE `tabItem Default` SET selling_cost_center=%s, income_account=%s "
				"WHERE parent=%s AND company=%s",
				(cost_center, income_account, item_code, company),
			)
		frappe.db.commit()

	if not item_codes:
		return {"error": "No items available"}

	# Use current month dates so Fee Collected This Month card always works
	month_start = get_first_day(getdate(today()))

	created = 0
	for i, student in enumerate(students):
		posting_date = str(add_days(month_start, i % 25))
		due_date = str(add_days(month_start, min(i % 25 + 10, 27)))

		items = [
			{
				"item_code": item_code,
				"qty": 1,
				"rate": rate,
				"income_account": income_account,
				"cost_center": cost_center,
			}
			for item_code, rate in item_codes
		]

		inv = frappe.get_doc({
			"doctype": "Sales Invoice",
			"customer": _get_or_create_customer(student["name"], student.get("student_name", "")),
			"posting_date": posting_date,
			"due_date": due_date,
			"company": company,
			"debit_to": debtors_account,
			"student": student["name"],
			"items": items,
		})
		inv.insert(ignore_permissions=True)
		inv.submit()

		if i < 14:
			_make_payment(inv, company, debtors_account)

		created += 1

	return {"created": created, "skipped": existing}


def _patch_invoice_student_field():
	"""
	Set the student field on already-submitted demo invoices that have student=NULL.
	Only touches invoices whose customer maps to a demo student (@demo.edvronix.com).
	Does NOT modify GL entries — student is a custom informational field only.
	"""
	updated = frappe.db.sql(
		"""
		UPDATE `tabSales Invoice` si
		JOIN `tabStudent` st ON si.customer = st.student_name
		SET si.student = st.name
		WHERE si.student IS NULL
		  AND si.docstatus = 1
		  AND st.student_email_id LIKE %s
		""",
		("%@demo.edvronix.com",),
	)
	frappe.db.commit()
	return {"patched": (updated or 0)}


# ── Attendance ────────────────────────────────────────────────────────────────

def _ensure_attendance():
	today_date = today()
	existing = frappe.db.count("Student Attendance", {"date": today_date})
	if existing >= 10:
		return {"created": 0, "skipped": existing}

	students = frappe.get_all("Student", filters={"enabled": 1}, fields=["name"], limit=20)
	enrollments = {
		e["student"]: e["name"]
		for e in frappe.get_all("Program Enrollment", filters={"docstatus": 1}, fields=["student", "name"])
	}

	created = 0
	for i, student in enumerate(students):
		if frappe.db.exists("Student Attendance", {"student": student["name"], "date": today_date}):
			continue
		if not enrollments.get(student["name"]):
			continue

		doc = frappe.get_doc({
			"doctype": "Student Attendance",
			"student": student["name"],
			"date": today_date,
			"status": "Present" if i < 15 else "Absent",
		})
		doc.flags.ignore_validate = True
		doc.insert(ignore_permissions=True)
		doc.flags.ignore_validate = True
		doc.submit()
		created += 1

	return {"created": created, "skipped": existing}


# ── Student Applicants ────────────────────────────────────────────────────────

def _ensure_student_applicants():
	existing = frappe.db.count("Student Applicant")
	if existing >= 10:
		return {"created": 0, "skipped": existing}

	programs = frappe.get_all("Program", fields=["name"], limit=10)
	if not programs:
		return {"error": "No programs found"}

	genders = ["Male", "Female", "Male", "Female", "Male",
	           "Female", "Male", "Female", "Male", "Female"]

	created = 0
	for i, (first, last) in enumerate(APPLICANT_NAMES):
		email = f"applicant{i+1}@demo.edvronix.com"
		if frappe.db.exists("Student Applicant", {"student_email_id": email}):
			continue

		prog = programs[i % len(programs)]["name"]
		application_date = f"2026-0{4 + (i % 2)}-{10 + i:02d}"

		doc = frappe.get_doc({
			"doctype": "Student Applicant",
			"first_name": first,
			"last_name": last,
			"student_email_id": email,
			"gender": genders[i],
			"program": prog,
			"academic_year": "2026-2027",
			"application_date": application_date,
			"application_status": "Approved",
		})
		doc.insert(ignore_permissions=True)
		doc.submit()
		created += 1

	return {"created": created, "skipped": existing}


# ── Disabled / Stuck-Off Demo Students ───────────────────────────────────────

def _ensure_disabled_demo_students():
	"""Create 2 clearly-labelled demo students with enabled=0 for stuck-off reports."""
	disabled_emails = [
		"stuck-off-male@demo.edvronix.com",
		"stuck-off-female@demo.edvronix.com",
	]

	existing = frappe.db.count("Student", {"student_email_id": ["in", disabled_emails]})
	if existing >= 2:
		return {"created": 0, "skipped": existing}

	programs = frappe.get_all("Program", fields=["name"], limit=2)
	data = [
		("Stuck-Off", "Demo Male", "Male", disabled_emails[0]),
		("Stuck-Off", "Demo Female", "Female", disabled_emails[1]),
	]

	created = 0
	for i, (first, last, gender, email) in enumerate(data):
		if frappe.db.exists("Student", {"student_email_id": email}):
			continue

		student_doc = frappe.get_doc({
			"doctype": "Student",
			"first_name": first,
			"last_name": last,
			"student_email_id": email,
			"gender": gender,
			"enabled": 0,
		})
		student_doc.insert(ignore_permissions=True)

		# Add a program enrollment so stuck-off report shows the program
		if programs:
			prog = programs[i % len(programs)]["name"]
			enr = frappe.get_doc({
				"doctype": "Program Enrollment",
				"student": student_doc.name,
				"academic_year": "2026-2027",
				"program": prog,
				"enrollment_date": "2026-04-01",
				"custom_tuition_fee": 3500,
				"custom_monthy_fee_": 3500,
			})
			enr.insert(ignore_permissions=True)
			enr.submit()

		created += 1

	return {"created": created, "skipped": existing}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_income_account(company):
	for keyword in ["Sales", "Service", "Income", "Revenue", "Fee Income"]:
		acc = frappe.db.get_value(
			"Account",
			{"company": company, "account_name": ["like", f"%{keyword}%"], "account_type": "Income Account"},
			"name",
		)
		if acc:
			return acc
	return frappe.db.get_value("Account", {"company": company, "root_type": "Income", "is_group": 0}, "name")


def _get_debtors_account(company):
	return (
		frappe.db.get_value("Account", {"company": company, "account_type": "Receivable", "is_group": 0}, "name")
		or frappe.db.get_value("Account", {"company": company, "account_name": ["like", "%Debtor%"], "is_group": 0}, "name")
	)


def _get_or_create_item(item_name, income_account, company, cost_center=None):
	if frappe.db.exists("Item", item_name):
		item_doc = frappe.get_doc("Item", item_name)
		if item_doc.disabled:
			item_doc.disabled = 0

		has_default = any(d.company == company for d in item_doc.get("item_defaults", []))
		if not has_default:
			item_doc.append("item_defaults", {
				"company": company,
				"income_account": income_account,
				"selling_cost_center": cost_center,
			})
		elif cost_center:
			for d in item_doc.item_defaults:
				if d.company == company:
					d.selling_cost_center = cost_center
		item_doc.save(ignore_permissions=True)
		return item_name

	try:
		item_group = frappe.db.get_value("Item Group", {"is_group": 0}, "name") or "All Item Groups"
		doc = frappe.get_doc({
			"doctype": "Item",
			"item_code": item_name,
			"item_name": item_name,
			"item_group": item_group,
			"stock_uom": "Nos",
			"is_stock_item": 0,
			"is_sales_item": 1,
			"disabled": 0,
			"item_defaults": [{"company": company, "income_account": income_account, "selling_cost_center": cost_center}],
		})
		doc.insert(ignore_permissions=True)
		return item_name
	except Exception:
		return None


def _get_or_create_customer(student_name, display_name):
	customer_name = display_name or student_name
	if frappe.db.exists("Customer", customer_name):
		return customer_name
	try:
		doc = frappe.get_doc({
			"doctype": "Customer",
			"customer_name": customer_name,
			"customer_type": "Individual",
			"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or "All Customer Groups",
			"territory": frappe.db.get_value("Territory", {"is_group": 0}, "name") or "All Territories",
		})
		doc.insert(ignore_permissions=True)
		return customer_name
	except Exception:
		return frappe.db.get_value("Customer", {}, "name")


def _make_payment(invoice, company, debtors_account):
	try:
		cash_account = frappe.db.get_value(
			"Account", {"company": company, "account_type": "Cash", "is_group": 0}, "name"
		)
		if not cash_account:
			return

		pe = frappe.get_doc({
			"doctype": "Payment Entry",
			"payment_type": "Receive",
			"party_type": "Customer",
			"party": invoice.customer,
			"posting_date": invoice.posting_date,
			"company": company,
			"paid_amount": invoice.grand_total,
			"received_amount": invoice.grand_total,
			"paid_from": debtors_account,
			"paid_to": cash_account,
			"paid_from_account_currency": invoice.currency,
			"paid_to_account_currency": invoice.currency,
			"references": [{
				"reference_doctype": "Sales Invoice",
				"reference_name": invoice.name,
				"allocated_amount": invoice.grand_total,
			}],
		})
		pe.insert(ignore_permissions=True)
		pe.submit()
	except Exception:
		pass


@frappe.whitelist()
def cleanup_demo_data():
	"""Remove all demo records created by create_demo_data(). Safe to run on demo site."""
	frappe.only_for("System Manager")
	if not frappe.conf.get("allow_demo_data"):
		frappe.throw("Only allowed on demo sites (allow_demo_data: true in site_config.json).")

	removed = {}

	# Demo students (enabled and disabled)
	demo_students = frappe.get_all(
		"Student",
		filters={"student_email_id": ["like", "%@demo.edvronix.com"]},
		fields=["name"],
	)
	for s in demo_students:
		try:
			frappe.delete_doc("Student", s.name, force=True, ignore_permissions=True)
		except Exception:
			pass
	removed["students"] = len(demo_students)

	# Test / demo Student Applicants
	demo_applicants = frappe.get_all(
		"Student Applicant",
		filters=[["student_email_id", "like", "%@demo.edvronix.com"]],
		fields=["name"],
	)
	test_applicants = frappe.get_all(
		"Student Applicant",
		filters={"first_name": "Test"},
		fields=["name"],
	)
	for a in demo_applicants + test_applicants:
		try:
			frappe.delete_doc("Student Applicant", a.name, force=True, ignore_permissions=True)
		except Exception:
			pass
	removed["applicants"] = len(demo_applicants) + len(test_applicants)

	# Demo guardians
	demo_guardians = frappe.get_all(
		"Guardian",
		filters={"email_address": ["like", "%@demo.edvronix.com"]},
		fields=["name"],
	)
	for g in demo_guardians:
		try:
			frappe.delete_doc("Guardian", g.name, force=True, ignore_permissions=True)
		except Exception:
			pass
	removed["guardians"] = len(demo_guardians)

	frappe.db.commit()
	return removed
