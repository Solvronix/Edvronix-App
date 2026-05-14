# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)
    
    # 1. Calculate Totals FIRST
    total_all = sum(row.get("total_students", 0) for row in data)
    total_male = sum(row.get("male", 0) for row in data)
    total_female = sum(row.get("female", 0) for row in data)
    total_other = sum(row.get("other", 0) for row in data)

    # 2. Add the Total Row to the data list
    if data:
        data.append({
            "program": frappe.bold("Total"),
            "total_students": total_all,
            "male": total_male,
            "female": total_female,
            "other": total_other
        })

    # 3. Report Summary (The colored boxes at the top)
    report_summary = [
        {"value": total_all, "label": "Total Students", "datatype": "Int", "indicator": "Blue"},
        {"value": total_male, "label": "Total Boys", "datatype": "Int", "indicator": "Green"},
        {"value": total_female, "label": "Total Girls", "datatype": "Int", "indicator": "Red"}
    ]

    return columns, data, None, None, report_summary

def get_columns():
    return [
        {"label": "Program", "fieldname": "program", "fieldtype": "Link", "options": "Program", "width": 200},
        {"label": "Total Students", "fieldname": "total_students", "fieldtype": "Int", "width": 140},
        {"label": "Male", "fieldname": "male", "fieldtype": "Int", "width": 100},
        {"label": "Female", "fieldname": "female", "fieldtype": "Int", "width": 100}
        
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    return frappe.db.sql(f"""
        SELECT 
            pe.program,
            COUNT(DISTINCT pe.student) as total_students,
            SUM(CASE WHEN s.gender = 'Male' THEN 1 ELSE 0 END) as male,
            SUM(CASE WHEN s.gender = 'Female' THEN 1 ELSE 0 END) as female,
            SUM(CASE WHEN s.gender NOT IN ('Male', 'Female') OR s.gender IS NULL THEN 1 ELSE 0 END) as other
        FROM 
            `tabProgram Enrollment` pe
        JOIN 
            `tabStudent` s ON pe.student = s.name
        WHERE 
            {conditions}
        GROUP BY 
            pe.program
        ORDER BY 
            total_students DESC
    """, filters, as_dict=1)

def get_conditions(filters):
    conditions = ["pe.docstatus = 1", "s.enabled = 1"]  #  Always only enabled students

    if filters.get("academic_year"):
        conditions.append("pe.academic_year = %(academic_year)s")
    if filters.get("program"):
        conditions.append("pe.program = %(program)s")
    if filters.get("batch"):
        conditions.append("pe.student_batch_name = %(batch)s")

    return " AND ".join(conditions)