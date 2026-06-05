import frappe


def execute(filters=None):
	filters = filters or {}

	columns = [
		{
			"label": "Student ID",
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Student",
			"width": 130,
		},
		{
			"label": "Student Name",
			"fieldname": "student_name",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": "Program",
			"fieldname": "program",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": "Academic Year",
			"fieldname": "academic_year",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": "Graduation Date",
			"fieldname": "date_of_leaving",
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"label": "Certificate No.",
			"fieldname": "leaving_certificate_number",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": "Gender",
			"fieldname": "gender",
			"fieldtype": "Data",
			"width": 80,
		},
	]

	# Build Student filters
	student_filters = {
		"enabled": 0,
		"reason_for_leaving": "Graduated",
	}

	if filters.get("from_date"):
		student_filters["date_of_leaving"] = [">=", filters["from_date"]]
	if filters.get("to_date"):
		if filters.get("from_date"):
			student_filters["date_of_leaving"] = ["between", [filters["from_date"], filters["to_date"]]]
		else:
			student_filters["date_of_leaving"] = ["<=", filters["to_date"]]

	students = frappe.get_all(
		"Student",
		filters=student_filters,
		fields=["name", "student_name", "gender", "date_of_leaving", "leaving_certificate_number"],
		order_by="date_of_leaving desc, student_name asc",
	)

	if not students:
		return columns, []

	# Get last Program Enrollment for each student to get program + academic_year
	student_names = [s["name"] for s in students]
	enrollments = frappe.db.sql(
		"""
		SELECT pe.student, pe.program, pe.academic_year
		FROM `tabProgram Enrollment` pe
		INNER JOIN (
			SELECT student, MAX(creation) AS latest
			FROM `tabProgram Enrollment`
			WHERE student IN %(students)s AND docstatus = 1
			GROUP BY student
		) latest_pe ON pe.student = latest_pe.student AND pe.creation = latest_pe.latest
		""",
		{"students": student_names},
		as_dict=True,
	)

	enr_map = {e["student"]: e for e in enrollments}

	# Apply program / academic_year filters (post-join)
	data = []
	for s in students:
		enr = enr_map.get(s["name"], {})
		program = enr.get("program", "")
		academic_year = enr.get("academic_year", "")

		if filters.get("program") and program != filters["program"]:
			continue
		if filters.get("academic_year") and academic_year != filters["academic_year"]:
			continue

		data.append({
			"name": s["name"],
			"student_name": s["student_name"],
			"gender": s["gender"],
			"date_of_leaving": s["date_of_leaving"],
			"leaving_certificate_number": s["leaving_certificate_number"],
			"program": program,
			"academic_year": academic_year,
		})

	return columns, data
