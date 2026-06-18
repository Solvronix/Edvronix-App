import frappe


@frappe.whitelist()
def get_exam_names():
	return frappe.db.sql(
		"SELECT DISTINCT assessment_name FROM `tabAssessment Plan` "
		"WHERE docstatus=1 ORDER BY assessment_name",
		as_dict=True,
	)


@frappe.whitelist()
def get_programs_for_exam(exam_name):
	"""Return distinct programs (classes) that have plans for this exam."""
	return frappe.db.sql(
		"SELECT DISTINCT program FROM `tabAssessment Plan` "
		"WHERE assessment_name=%s AND docstatus=1 ORDER BY program",
		exam_name,
		as_dict=True,
	)


@frappe.whitelist()
def get_sections_for_exam(exam_name, program=""):
	"""Return sections for an exam, optionally filtered by program."""
	filters = {"assessment_name": exam_name, "docstatus": 1}
	if program:
		filters["program"] = program
	return frappe.db.get_all(
		"Assessment Plan",
		filters=filters,
		fields=["name as plan_name", "student_group"],
		order_by="student_group",
	)


@frappe.whitelist()
def get_result_cards_for_section(exam_name, student_group="ALL"):
	"""
	Return result card data for all students.
	student_group='ALL' → returns every section for this exam.
	"""
	filters = {"assessment_name": exam_name, "docstatus": 1}
	if student_group and student_group != "ALL":
		filters["student_group"] = student_group

	plans = frappe.db.get_all(
		"Assessment Plan",
		filters=filters,
		fields=["name", "student_group", "program", "academic_year", "academic_term",
		        "grading_scale", "maximum_assessment_score", "assessment_name"],
		order_by="student_group",
	)

	school_info = _get_school_info()

	if not plans:
		return {"school_info": school_info, "criteria": [], "results": []}

	# Build criteria list from the first plan (all plans share same criteria for one exam)
	first_plan = frappe.get_doc("Assessment Plan", plans[0].name)
	criteria = [
		{"assessment_criteria": c.assessment_criteria, "maximum_score": c.maximum_score}
		for c in first_plan.assessment_criteria
	]
	total_max = sum(c["maximum_score"] for c in criteria)

	# Fetch passing marks from Exam Setup if available
	passing_map = {}
	if frappe.db.exists("Exam Setup", exam_name):
		es = frappe.get_doc("Exam Setup", exam_name)
		passing_map = {s.assessment_criteria: float(s.passing_marks or 0) for s in es.subjects}
		# Attach passing marks to each criterion for the frontend
		for c in criteria:
			c["passing_marks"] = passing_map.get(c["assessment_criteria"], 0)

	all_results = []

	for p in plans:
		# Roll-number lookup from Student Group Student
		roll_map = {
			sg.student: sg.group_roll_number or ""
			for sg in frappe.db.get_all(
				"Student Group Student",
				filters={"parent": p.student_group, "active": 1},
				fields=["student", "group_roll_number"],
			)
		}

		results = frappe.db.get_all(
			"Assessment Result",
			filters={"assessment_plan": p.name, "docstatus": 1},
			fields=["name", "student", "student_name", "total_score", "maximum_score", "grade"],
			order_by="total_score desc",
		)

		# Assign dense-rank position within the section
		pos, prev_score = 1, None
		for i, r in enumerate(results):
			if r.total_score != prev_score:
				pos = i + 1
				prev_score = r.total_score

			r["position"] = pos
			r["section_total"] = len(results)
			r["student_group"] = p.student_group
			r["program"] = p.program
			r["academic_year"] = p.academic_year
			r["academic_term"] = p.academic_term
			r["assessment_name"] = p.assessment_name
			r["roll_number"] = roll_map.get(r.student, "")
			r["details"] = frappe.db.get_all(
				"Assessment Result Detail",
				filters={"parent": r.name},
				fields=["assessment_criteria", "maximum_score", "score", "grade"],
			)

			pct = round(r.total_score / r.maximum_score * 100, 1) if r.maximum_score else 0
			r["percentage"] = pct

			# PASS/FAIL — subject-level check when passing marks are available
			if passing_map:
				failed = [
					d for d in r["details"]
					if float(d.score or 0) < passing_map.get(d.assessment_criteria, 0)
				]
				r["result"] = "FAIL" if failed else "PASS"
			else:
				r["result"] = "PASS" if pct >= 33 else "FAIL"

			all_results.append(r)

	return {"school_info": school_info, "criteria": criteria, "results": all_results}


def _get_school_info():
	settings = frappe.get_single("Edvronix Settings")
	return {
		"school_name": settings.school_name or "School",
		"school_logo": settings.school_logo or "",
		"address": settings.address or "",
		"phone": settings.phone or "",
	}
