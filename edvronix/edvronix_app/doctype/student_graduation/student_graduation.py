import frappe
from frappe.model.document import Document
from frappe.utils import today


class StudentGraduation(Document):

	def validate(self):
		self.total_students = len(self.students)

	def on_submit(self):
		"""Graduate all students: disable them and set exit fields."""
		if not self.students:
			frappe.throw("No students to graduate. Please fetch students first.")

		graduated = 0
		for row in self.students:
			if not row.student:
				continue
			frappe.db.set_value("Student", row.student, {
				"enabled": 0,
				"date_of_leaving": self.graduation_date,
				"reason_for_leaving": "Graduated",
				"leaving_certificate_number": row.certificate_number or "",
			})
			frappe.db.set_value("Graduation Student Detail", row.name, "is_graduated", 1)
			graduated += 1

		frappe.db.commit()
		frappe.msgprint(f"{graduated} student(s) graduated successfully.", indicator="green", alert=True)

	def on_cancel(self):
		"""Restore all graduated students to active status."""
		restored = 0
		for row in self.students:
			if not row.student or not row.is_graduated:
				continue
			frappe.db.set_value("Student", row.student, {
				"enabled": 1,
				"date_of_leaving": None,
				"reason_for_leaving": "",
				"leaving_certificate_number": "",
			})
			frappe.db.set_value("Graduation Student Detail", row.name, "is_graduated", 0)
			restored += 1

		frappe.db.commit()
		frappe.msgprint(f"{restored} student(s) restored to active.", indicator="orange", alert=True)


@frappe.whitelist()
def fetch_students(academic_year, program):
	"""
	Return list of active students enrolled in the given program + academic_year.
	Called from the JS form button 'Fetch Students'.
	"""
	enrollments = frappe.get_all(
		"Program Enrollment",
		filters={
			"academic_year": academic_year,
			"program": program,
			"docstatus": 1,
		},
		fields=["student", "student_name"],
		order_by="student_name asc",
	)

	# Filter to only active (not already graduated/disabled) students
	active = []
	for e in enrollments:
		enabled = frappe.db.get_value("Student", e["student"], "enabled")
		if enabled:
			active.append({
				"student": e["student"],
				"student_name": e["student_name"] or frappe.db.get_value("Student", e["student"], "student_name"),
				"certificate_number": "",
				"is_graduated": 0,
			})

	return active


@frappe.whitelist()
def graduate_single_student(student, graduation_date, certificate_number="", notes=""):
	"""Graduate a single student directly from the Student form."""
	frappe.only_for(["System Manager", "School Administrator"])

	enabled = frappe.db.get_value("Student", student, "enabled")
	if not enabled:
		frappe.throw(f"Student {student} is already inactive/graduated.")

	frappe.db.set_value("Student", student, {
		"enabled": 0,
		"date_of_leaving": graduation_date,
		"reason_for_leaving": "Graduated",
		"leaving_certificate_number": certificate_number or "",
	})
	frappe.db.commit()
	return {"success": True, "student": student}
