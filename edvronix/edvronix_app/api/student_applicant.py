import re
import random

import frappe


@frappe.whitelist()
def generate_email_now(applicant_name):
	"""
	Instantly generate and persist student_email_id for a Student Applicant
	that was saved without one. Called from the form's client script on load.
	Returns the generated email so the form can display it without a full reload.
	"""
	doc = frappe.get_doc("Student Applicant", applicant_name)
	if doc.student_email_id:
		return doc.student_email_id

	from edvronix.events import _get_school_domain, _get_email_domain

	school_domain = _get_school_domain()
	email_tld     = _get_email_domain()

	first = re.sub(r'[^a-z]', '', (doc.first_name or "").lower())
	last  = re.sub(r'[^a-z]', '', (doc.last_name  or "").lower())
	base  = (first + last) or "student"

	for _ in range(50):
		number = random.randint(10, 9999)
		email  = f"{base}{number}@{school_domain}.{email_tld}"
		if not frappe.db.exists("Student Applicant", {"student_email_id": email}):
			frappe.db.set_value("Student Applicant", applicant_name, "student_email_id", email)
			frappe.db.commit()
			return email

	frappe.log_error(
		f"Could not generate unique email for {doc.first_name} {doc.last_name}",
		"Edvronix: student email generation failed"
	)
	return None
