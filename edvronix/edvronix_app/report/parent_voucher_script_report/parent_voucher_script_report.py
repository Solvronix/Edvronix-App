# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    
    guardian = filters.get("guardian") or ""
    academic_year = filters.get("academic_year") or ""
    month = filters.get("month") or ""

    # SQL Logic: Matches the month of the Due Date directly with the filter
    data = frappe.db.sql("""
        SELECT DISTINCT
            g.name AS guardian_id,
            g.guardian_name AS parent_name,
            g.mobile_number AS mobile,
            s.name AS student_id,
            s.student_name AS student_name,
            pe.program AS program,
            pe.student_category AS student_category,
            pe.academic_year AS academic_year,
            si.name AS invoice_id,
            si.posting_date AS date,
            si.due_date AS due_date,
            COALESCE(
                (SELECT SUM(amount)
                 FROM `tabSales Invoice Item`
                 WHERE parent = si.name
                 AND (item_name LIKE '%%Tuition%%' OR item_code LIKE '%%Tuition%%')), 0
            ) AS tuition_fee,
            si.grand_total AS total_per_student,
            si.outstanding_amount AS outstanding,
            CASE
                WHEN si.outstanding_amount <= 0 THEN 'Paid'
                WHEN si.outstanding_amount < si.grand_total AND si.outstanding_amount > 0 THEN 'Partially Paid'
                WHEN si.due_date < CURDATE() AND si.outstanding_amount > 0 THEN 'Overdue'
                ELSE 'Unpaid'
            END AS status
        FROM `tabSales Invoice` si
        INNER JOIN `tabStudent` s ON si.student = s.name
        INNER JOIN `tabStudent Guardian` sg ON s.name = sg.parent
        INNER JOIN `tabGuardian` g ON sg.guardian = g.name
        INNER JOIN `tabProgram Enrollment` pe 
            ON pe.student = s.name
            AND pe.docstatus = 1
            AND (%(academic_year)s = '' OR pe.academic_year = %(academic_year)s)
        WHERE
            si.docstatus = 1
            AND (%(guardian)s = '' OR g.name = %(guardian)s)
            AND (%(academic_year)s = '' OR pe.academic_year = %(academic_year)s)
            AND (%(month)s = '' OR MONTHNAME(si.due_date) = %(month)s)
        ORDER BY g.name, s.name
    """, {
        "guardian": guardian,
        "academic_year": academic_year,
        "month": month
    }, as_dict=True)

    # --- DASHBOARD CARD LOGIC START ---
    total_fee = 0
    total_outstanding = 0
    total_paid = 0

    for d in data:
        total_fee += flt(d.get("total_per_student"))
        total_outstanding += flt(d.get("outstanding"))
        # Paid = Total - Outstanding
        total_paid += (flt(d.get("total_per_student")) - flt(d.get("outstanding")))

    report_summary = [
        {"value": total_fee, "label": "Total Fee", "datatype": "Currency", "indicator": "Blue"},
        {"value": total_paid, "label": "Total Paid", "datatype": "Currency", "indicator": "Green"},
        {"value": total_outstanding, "label": "Total Outstanding", "datatype": "Currency", "indicator": "Red"},
    ]
    # --- DASHBOARD CARD LOGIC END ---

    return columns, data, None, None, report_summary

def get_columns():
    return [
        {"label": "Guardian ID", "fieldname": "guardian_id", "fieldtype": "Link", "options": "Guardian", "width": 120},
        {"label": "Parent Name", "fieldname": "parent_name", "fieldtype": "Data", "width": 150},
        {"label": "Student Name", "fieldname": "student_name", "fieldtype": "Data", "width": 150},
        {"label": "Program", "fieldname": "program", "fieldtype": "Data", "width": 120},
        {"label": "Student Category", "fieldname": "student_category", "fieldtype": "Data", "width": 120},
        {"label": "Invoice ID", "fieldname": "invoice_id", "fieldtype": "Link", "options": "Sales Invoice", "width": 120},
        {"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 100},
        {"label": "Tuition Fee", "fieldname": "tuition_fee", "fieldtype": "Currency", "width": 110},
        {"label": "Outstanding", "fieldname": "outstanding", "fieldtype": "Currency", "width": 110},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
    ]