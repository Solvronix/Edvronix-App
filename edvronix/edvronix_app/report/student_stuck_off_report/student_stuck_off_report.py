# Copyright (c) 2026, Solvronix and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    summary = get_report_summary(data)
    return columns, data, None, chart, summary

def get_columns():
    return [
        {"label": _("Student ID"), "fieldname": "student", "fieldtype": "Link", "options": "Student", "width": 140},
        {"label": _("Student Name"), "fieldname": "student_name", "fieldtype": "Data", "width": 200},
        {"label": _("Program"), "fieldname": "program", "fieldtype": "Link", "options": "Program", "width": 140},
        {"label": _("Section"), "fieldname": "student_category", "fieldtype": "Link", "options": "Student Category", "width": 140},
        {"label": _("Gender"), "fieldname": "gender", "fieldtype": "Data", "width": 100},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
        {"label": _("Stuck_off_Date"), "fieldname": "stuck_off_date", "fieldtype": "Date", "width": 120},
        {"label": _("Reason"), "fieldname": "reason", "fieldtype": "Data", "width": 200},
        {"label": _("Mobile Number"), "fieldname": "mobile", "fieldtype": "Data", "width": 140},
        {"label": _("Last Modified"), "fieldname": "modified", "fieldtype": "Datetime", "width": 160}
    ]

def get_data(filters):
    # 1. Fetch the Current Academic Year from Education Settings
    current_academic_year = frappe.db.get_single_value("Education Settings", "current_academic_year")

    # 2. Build filters for the Student table
    # We only want disabled students (enabled = 0)
    conditions = ["s.enabled = 0"]
    values = {"current_academic_year": current_academic_year}

    if filters:
        if filters.get("from_date"):
            conditions.append("s.modified >= %(from_date)s")
            values["from_date"] = filters.get("from_date")
        if filters.get("to_date"):
            conditions.append("s.modified <= %(to_date)s")
            values["to_date"] = filters.get("to_date")

    where_clause = " WHERE " + " AND ".join(conditions)

    # 3. Join with Program Enrollment strictly on the Current Academic Year
    data = frappe.db.sql(f"""
        SELECT
            s.name as student,
            s.student_name,
            s.gender,
            pe.program,
            pe.student_category,
            s.enabled,
            s.date_of_leaving as stuck_off_date,
            s.reason_for_leaving as reason,
            s.student_mobile_number as mobile,
            s.modified
        FROM `tabStudent` s
        INNER JOIN `tabProgram Enrollment` pe 
            ON pe.student = s.name 
            AND pe.academic_year = %(current_academic_year)s
            AND pe.docstatus = 1
        {where_clause}
        ORDER BY s.modified DESC
    """, values, as_dict=1)

    for d in data:
        d["status"] = "Stuck Off"

    return data

def get_chart_data(data):
    return {
        "data": {
            "labels": ["Stuck Off Students"],
            "datasets": [{"name": "Total", "values": [len(data)]}]
        },
        "type": "bar",
        "colors": ["#ff4d4f"]
    }

def get_report_summary(data):
    return [
        {
            "value": len(data),
            "indicator": "Red",
            "label": "Total Stuck Off Students",
            "datatype": "Int"
        }
    ]