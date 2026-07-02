import json
import frappe


@frappe.whitelist()
def get_sections(program, academic_year=""):
	filters = {"program": program}
	if academic_year:
		filters["academic_year"] = academic_year
	return frappe.db.get_all(
		"Student Group",
		filters=filters,
		fields=["name", "student_group_name"],
		order_by="student_group_name",
	)


@frappe.whitelist()
def get_section_progress(exam_name):
	"""Return per-section status for the progress table on the Exam Setup page."""
	plans = frappe.db.get_all(
		"Assessment Plan",
		filters={"assessment_name": exam_name, "docstatus": 1},
		fields=["name", "student_group", "maximum_assessment_score"],
		order_by="student_group",
	)
	rows = []
	for plan in plans:
		total = frappe.db.count("Student Group Student", {"parent": plan.student_group, "active": 1})
		submitted = frappe.db.count("Assessment Result", {"assessment_plan": plan.name, "docstatus": 1})
		if submitted == 0:
			status, color = "Pending", "red"
		elif submitted >= total:
			status, color = "Result Generated", "green"
		else:
			status, color = "Marks Entered", "orange"
		rows.append({
			"section": plan.student_group,
			"plan_name": plan.name,
			"total_students": total,
			"submitted_results": submitted,
			"status": status,
			"color": color,
		})
	return rows


@frappe.whitelist()
def get_exam_setup(exam_name):
	"""Return Exam Setup record fields for pre-filling the form."""
	if not frappe.db.exists("Exam Setup", exam_name):
		return None
	doc = frappe.get_doc("Exam Setup", exam_name)
	return {
		"exam_name": doc.exam_name,
		"program": doc.program,
		"academic_year": doc.academic_year,
		"academic_term": doc.academic_term,
		"exam_date": str(doc.exam_date) if doc.exam_date else "",
		"grading_scale": doc.grading_scale,
		"subjects": [
			{"assessment_criteria": s.assessment_criteria, "max_marks": s.max_marks, "passing_marks": s.passing_marks}
			for s in doc.subjects
		],
	}


@frappe.whitelist()
def create_exam_plans(
	exam_name, academic_year, academic_term, program, sections, exam_date, grading_scale, subjects
):
	sections = json.loads(sections) if isinstance(sections, str) else sections
	subjects = json.loads(subjects) if isinstance(subjects, str) else subjects

	# Create or update the Exam Setup record
	subject_rows = [
		{"assessment_criteria": s["assessment_criteria"], "max_marks": s["max_marks"], "passing_marks": s["passing_marks"]}
		for s in subjects
	]
	if frappe.db.exists("Exam Setup", exam_name):
		es = frappe.get_doc("Exam Setup", exam_name)
		es.program = program
		es.academic_year = academic_year
		es.academic_term = academic_term
		es.exam_date = exam_date
		es.grading_scale = grading_scale
		es.subjects = []
		for row in subject_rows:
			es.append("subjects", row)
		es.save(ignore_permissions=True)
	else:
		es = frappe.get_doc({
			"doctype": "Exam Setup",
			"exam_name": exam_name,
			"program": program,
			"academic_year": academic_year,
			"academic_term": academic_term,
			"exam_date": exam_date,
			"grading_scale": grading_scale,
			"subjects": subject_rows,
		})
		es.insert(ignore_permissions=True)

	# Resolve assessment_group: match term name keywords against existing groups in the DB,
	# so non-English and custom term names work instead of silently using an English fallback.
	all_groups = frappe.get_all("Assessment Group", filters={"is_group": 0}, pluck="name")
	term_lower = academic_term.lower()
	ag = None
	for keyword in ["annual", "mid", "first", "term", "exam"]:
		if keyword in term_lower:
			match = next((g for g in all_groups if keyword in g.lower()), None)
			if match:
				ag = match
				break
	if not ag:
		# Fall back to the first available leaf Assessment Group, or create a default
		ag = all_groups[0] if all_groups else "All Assessment Groups"

	total_max = sum(float(s["max_marks"]) for s in subjects)
	criteria_rows = [
		{"assessment_criteria": s["assessment_criteria"], "maximum_score": float(s["max_marks"])}
		for s in subjects
	]

	first_course = subjects[0]["assessment_criteria"]
	if not frappe.db.exists("Course", first_course):
		c = frappe.get_doc({"doctype": "Course", "course_name": first_course, "course_code": first_course})
		c.insert(ignore_permissions=True)

	created = []
	for sg in sections:
		if frappe.db.exists(
			"Assessment Plan", {"assessment_name": exam_name, "student_group": sg}
		):
			continue
		plan = frappe.get_doc({
			"doctype": "Assessment Plan",
			"assessment_name": exam_name,
			"assessment_group": ag,
			"program": program,
			"course": first_course,
			"academic_year": academic_year,
			"academic_term": academic_term,
			"student_group": sg,
			"schedule_date": exam_date,
			"from_time": "08:00:00",
			"to_time": "14:00:00",
			"grading_scale": grading_scale,
			"maximum_assessment_score": total_max,
			"assessment_criteria": criteria_rows,
		})
		plan.insert(ignore_permissions=True)
		plan.submit()
		created.append(plan.name)

	frappe.db.commit()
	return created
