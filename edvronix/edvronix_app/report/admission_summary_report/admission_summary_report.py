import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": "Student Applicant ID",
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Student Applicant",
            "width": 120
        },
        {
            "label": "Full Name",
            "fieldname": "full_name",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Guardian Name",
            "fieldname": "guardian_name",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": "Program (Class)",
            "fieldname": "program",
            "fieldtype": "Link",
            "options": "Program",
            "width": 140
        },
        {
            "label": "Student Category",
            "fieldname": "student_category",
            "fieldtype": "Link",
            "options": "Student Category",
            "width": 140
        },
        {
            "label": "Admission Date",
            "fieldname": "date",
            "fieldtype": "Date",
            "width": 110
        },
        {
            "label": "Academic Year",
            "fieldname": "academic_year",
            "fieldtype": "Link",
            "options": "Academic Year",
            "width": 120
        },
        {
            "label": "Status",
            "fieldname": "application_status",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": "Remarks",
            "fieldname": "remarks",
            "fieldtype": "Data",
            "width": 200
        },
    ]


def get_data(filters):
    conditions = []
    values = {}

    # Date Filter
    if filters.get("from_date") and filters.get("to_date"):
        conditions.append("sa.application_date BETWEEN %(from_date)s AND %(to_date)s")
        values["from_date"] = filters.get("from_date")
        values["to_date"] = filters.get("to_date")

    # Program Filter
    if filters.get("program"):
        conditions.append("sa.program = %(program)s")
        values["program"] = filters.get("program")

    # Academic Year Filter
    if filters.get("academic_year"):
        conditions.append("sa.academic_year = %(academic_year)s")
        values["academic_year"] = filters.get("academic_year")

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    return frappe.db.sql(f"""
        SELECT
    sa.name,
    g.name as guardian_id,
    g.guardian_name as guardian_name,

    CONCAT_WS(' ',
        sa.first_name,
        sa.middle_name,
        sa.last_name
    ) as full_name,

    sa.student_category,
    sa.application_date as date,
    sa.academic_year,
    sa.program,
    sa.application_status,
    sa.custom_remarks as remarks

FROM `tabStudent Applicant` sa

LEFT JOIN `tabStudent Guardian` sg
    ON sg.parent = sa.name
LEFT JOIN `tabGuardian` g
    ON g.name = sg.guardian

{where_clause}

ORDER BY sa.application_date DESC, sa.name ASC
    """, values, as_dict=True)