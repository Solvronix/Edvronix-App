import json
import frappe


@frappe.whitelist()
def get_exam_names():
	return frappe.db.sql(
		"SELECT DISTINCT assessment_name FROM `tabAssessment Plan` "
		"WHERE docstatus=1 ORDER BY assessment_name",
		as_dict=True,
	)


@frappe.whitelist()
def get_exam_details(exam_name):
	"""Return Exam Setup metadata + sections for pre-filling the marks entry form."""
	sections = frappe.db.get_all(
		"Assessment Plan",
		filters={"assessment_name": exam_name, "docstatus": 1},
		fields=["name as plan_name", "student_group", "program", "academic_year", "academic_term",
		        "grading_scale", "maximum_assessment_score"],
		order_by="student_group",
	)
	meta = {}
	if frappe.db.exists("Exam Setup", exam_name):
		es = frappe.get_doc("Exam Setup", exam_name)
		meta = {
			"program": es.program,
			"academic_year": es.academic_year,
			"academic_term": es.academic_term,
		}
	elif sections:
		meta = {
			"program": sections[0].program,
			"academic_year": sections[0].academic_year,
			"academic_term": sections[0].academic_term,
		}
	return {"meta": meta, "sections": sections}


@frappe.whitelist()
def get_sections_for_exam(exam_name):
	return frappe.db.get_all(
		"Assessment Plan",
		filters={"assessment_name": exam_name, "docstatus": 1},
		fields=["name as plan_name", "student_group", "grading_scale", "maximum_assessment_score"],
		order_by="student_group",
	)


@frappe.whitelist()
def get_marks_data(plan_name):
	plan = frappe.get_doc("Assessment Plan", plan_name)
	criteria = [
		{"assessment_criteria": c.assessment_criteria, "maximum_score": c.maximum_score}
		for c in plan.assessment_criteria
	]
	students = frappe.db.get_all(
		"Student Group Student",
		filters={"parent": plan.student_group, "active": 1},
		fields=["student", "student_name", "group_roll_number"],
		order_by="group_roll_number",
	)
	for s in students:
		result = frappe.db.get_value(
			"Assessment Result",
			{"student": s.student, "assessment_plan": plan_name, "docstatus": 1},
			["name", "total_score"],
			as_dict=True,
		)
		s["result_name"] = result.name if result else None
		s["scores"] = {}
		if result:
			details = frappe.db.get_all(
				"Assessment Result Detail",
				filters={"parent": result.name},
				fields=["assessment_criteria", "score"],
			)
			s["scores"] = {d.assessment_criteria: d.score for d in details}
	return {
		"criteria": criteria,
		"students": students,
		"plan": {
			"grading_scale": plan.grading_scale,
			"maximum_score": plan.maximum_assessment_score,
		},
	}


@frappe.whitelist()
def save_marks(plan_name, marks_data):
	marks_data = json.loads(marks_data) if isinstance(marks_data, str) else marks_data
	plan = frappe.get_doc("Assessment Plan", plan_name)
	criteria_map = {c.assessment_criteria: c.maximum_score for c in plan.assessment_criteria}
	saved = 0
	for entry in marks_data:
		student = entry["student"]
		scores = entry["scores"]
		# Cancel any existing submitted result so we can re-create it
		existing = frappe.db.get_value(
			"Assessment Result",
			{"student": student, "assessment_plan": plan_name, "docstatus": 1},
			"name",
		)
		if existing:
			frappe.get_doc("Assessment Result", existing).cancel()

		total = sum(float(scores.get(c, 0)) for c in criteria_map)
		details = [
			{
				"assessment_criteria": c,
				"maximum_score": criteria_map[c],
				"score": float(scores.get(c, 0)),
			}
			for c in criteria_map
		]
		result = frappe.get_doc(
			{
				"doctype": "Assessment Result",
				"student": student,
				"student_name": frappe.db.get_value("Student", student, "student_name"),
				"program": plan.program,
				"course": plan.course,
				"assessment_plan": plan_name,
				"academic_year": plan.academic_year,
				"academic_term": plan.academic_term,
				"student_group": plan.student_group,
				"grading_scale": plan.grading_scale,
				"total_score": total,
				"maximum_score": plan.maximum_assessment_score,
				"details": details,
			}
		)
		result.insert(ignore_permissions=True)
		result.submit()
		saved += 1

	frappe.db.commit()
	return {"saved": saved}
