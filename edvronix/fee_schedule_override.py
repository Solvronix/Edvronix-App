import frappe
from frappe import _
from education.education.doctype.fee_schedule.fee_schedule import FeeSchedule


@frappe.whitelist()
def get_pre_check_report(fee_schedule):
	"""Module-level whitelist function so the client can call it via full dotted path.
	frm.call('method') in Frappe 16 resolves to the doctype's original module, not our
	override class, so new methods must live here and be called with the full path."""
	doc = frappe.get_doc("Fee Schedule", fee_schedule)
	# Whitelisted endpoint — enforce read permission before returning any data.
	doc.check_permission("read")
	return doc._get_coverage_issues()


class CustomFeeSchedule(FeeSchedule):

	def validate_total_against_fee_strucuture(self):
		# Education 15.x uses frappe.db.get_all() with a raw "sum(...)" string which
		# Frappe 16 blocks. Override it here using frappe.db.sql() directly.
		fee_schedules_total = (
			frappe.db.sql(
				"SELECT SUM(total_amount) FROM `tabFee Schedule` WHERE fee_structure = %s",
				self.fee_structure,
			)[0][0]
			or 0
		)
		fee_structure_total = (
			frappe.db.get_value("Fee Structure", self.fee_structure, "total_amount") or 0
		)
		if fee_schedules_total > fee_structure_total:
			frappe.msgprint(
				_("Total amount of Fee Schedules exceeds the Total Amount of Fee Structure"),
				alert=True,
			)

	def before_submit(self):
		issues = self._get_coverage_issues()
		if issues:
			frappe.throw(self._format_issues(issues), title="Fee Schedule Pre-Check Failed — Cannot Submit")

	@frappe.whitelist()
	def create_fees(self):
		issues = self._get_coverage_issues()
		if issues:
			frappe.throw(self._format_issues(issues), title="Fee Schedule Pre-Check Failed")
		super().create_fees()

	def _get_coverage_issues(self):
		issues = []

		program = frappe.db.get_value("Fee Structure", self.fee_structure, "program")
		if not program:
			return issues

		scheduled_groups = {row.student_group for row in self.student_groups}

		# Check 1 — Student Groups for this program/year absent from the schedule
		all_groups = frappe.get_all(
			"Student Group",
			filters={"program": program, "academic_year": self.academic_year, "disabled": 0},
			pluck="name",
		)
		missing_groups = [g for g in all_groups if g not in scheduled_groups]
		if missing_groups:
			issues.append({
				"type": "missing_groups",
				"message": "Student Groups for this program/year are missing from the schedule",
				"items": missing_groups,
			})

		if not scheduled_groups:
			return issues

		# Check 2 — For each student group in the schedule, find enabled students who
		# match that group's own filters (the same criteria used by the "Get Students"
		# button: program, academic_year, academic_term, batch, student_category) but
		# are either missing from the group entirely OR present with active=0.
		# These students will be skipped when invoices are created.
		for group_name in sorted(scheduled_groups):
			sg = frappe.db.get_value(
				"Student Group",
				group_name,
				["program", "academic_year", "academic_term", "batch", "student_category"],
				as_dict=True,
			)
			if not sg:
				continue

			# Build PE filter conditions mirroring get_program_enrollment()
			cond = ""
			params = {
				"academic_year": sg.academic_year or self.academic_year,
				"program": sg.program or program,
			}
			if sg.academic_term:
				cond += " AND pe.academic_term = %(academic_term)s"
				params["academic_term"] = sg.academic_term
			if sg.batch:
				cond += " AND pe.student_batch_name = %(batch)s"
				params["batch"] = sg.batch
			if sg.student_category:
				cond += " AND pe.student_category = %(student_category)s"
				params["student_category"] = sg.student_category

			# Students who SHOULD be in this group (enabled + submitted enrollment)
			should_be = frappe.db.sql(
				f"""
				SELECT pe.student, pe.student_name
				FROM `tabProgram Enrollment` pe
				INNER JOIN `tabStudent` s ON s.name = pe.student
				WHERE pe.docstatus = 1
				  AND pe.academic_year = %(academic_year)s
				  AND pe.program = %(program)s
				  AND s.enabled = 1
				  {cond}
				""",
				params,
				as_dict=True,
			)

			if not should_be:
				continue

			# Students actually in this group with active=1
			in_group_active = set(
				frappe.get_all(
					"Student Group Student",
					filters={"parent": group_name, "active": 1},
					pluck="student",
				)
			)

			missing = [s for s in should_be if s.student not in in_group_active]
			if missing:
				issues.append({
					"type": "students_missing_from_group",
					"message": f"Students missing from student group: {group_name}",
					"items": [f"{s.student} — {s.student_name}" for s in missing],
				})

		return issues

	def _format_issues(self, issues):
		lines = ["<b>Please fix the following issues before creating fee invoices:</b><br><br>"]
		for issue in issues:
			lines.append(f"<b>{issue['message']}:</b><br>")
			lines.extend(f"&nbsp;&nbsp;• {item}<br>" for item in issue["items"])
			lines.append("<br>")
		return "".join(lines)
