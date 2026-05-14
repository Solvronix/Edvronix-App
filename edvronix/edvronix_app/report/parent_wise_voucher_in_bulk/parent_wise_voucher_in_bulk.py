import frappe
from frappe.utils import flt
import json

@frappe.whitelist()
def execute(filters=None):
    if isinstance(filters, str):
        filters = json.loads(filters)
    
    if not filters:
        filters = {}

    columns = get_columns()
    
    guardian = filters.get("guardian") or ""
    academic_year = filters.get("academic_year") or ""
    month = filters.get("month") or ""

    params = {
        "guardian": guardian,
        "academic_year": academic_year,
        "month": month,
        "tuition_search": "%%Tuition%%"
    }

    # Use LEFT JOIN for Sales Invoice to include students without invoices
    data = frappe.db.sql("""
        SELECT
            g.name AS guardian_id,
            g.guardian_name AS parent_name,
            s.name AS student_id,
            s.student_name AS student_name,
            pe.program AS program,
            pe.academic_year AS academic_year,
            pe.student_category AS student_category,
            si.name AS invoice_id,
            si.due_date AS due_date,
            COALESCE(si.grand_total, 0) AS total_per_student,
            COALESCE(si.outstanding_amount, 0) AS outstanding,
            COALESCE(
                (SELECT SUM(amount) FROM `tabSales Invoice Item`
                 WHERE parent = si.name AND (item_name LIKE %(tuition_search)s OR item_code LIKE %(tuition_search)s)
                ), 0
            ) AS tuition_fee
        FROM `tabGuardian` g
        INNER JOIN `tabStudent Guardian` sg ON g.name = sg.guardian
        INNER JOIN `tabStudent` s ON sg.parent = s.name AND sg.parenttype = 'Student'
        LEFT JOIN `tabProgram Enrollment` pe 
            ON pe.student = s.name
            AND pe.docstatus = 1
        LEFT JOIN `tabSales Invoice` si 
            ON si.student = s.name 
            AND si.docstatus = 1
            AND (%(month)s = '' OR MONTHNAME(si.due_date) = %(month)s)
        WHERE
            1=1
            AND (%(guardian)s = '' OR g.name = %(guardian)s)
            AND (%(academic_year)s = '' OR pe.academic_year = %(academic_year)s)
        ORDER BY g.name, s.name, si.due_date
    """, params, as_dict=True)

    # Dashboard summary
    total_fee = sum(flt(d.total_per_student) for d in data)
    total_outstanding = sum(flt(d.outstanding) for d in data)
    total_paid = total_fee - total_outstanding

    report_summary = [
        {"value": total_fee, "label": "Total Fee", "datatype": "Currency", "indicator": "Blue"},
        {"value": total_paid, "label": "Total Paid", "datatype": "Currency", "indicator": "Green"},
        {"value": total_outstanding, "label": "Total Outstanding", "datatype": "Currency", "indicator": "Red"},
    ]

    return columns, data, None, None, report_summary

def get_columns():
    return [
        {"label": "Student ID", "fieldname": "student_id", "fieldtype": "Link", "options": "Student", "width": 120},
        {"label": "Student Name", "fieldname": "student_name", "fieldtype": "Data", "width": 150},
        {"label": "Guardian ID", "fieldname": "guardian_id", "fieldtype": "Link", "options": "Guardian", "width": 120},
        {"label": "Parent Name", "fieldname": "parent_name", "fieldtype": "Data", "width": 150},
        {"label": "Program", "fieldname": "program", "fieldtype": "Data", "width": 120},
        {"label": "Invoice ID", "fieldname": "invoice_id", "fieldtype": "Link", "options": "Sales Invoice", "width": 120},
        {"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 100},
        {"label": "Tuition Fee", "fieldname": "tuition_fee", "fieldtype": "Currency", "width": 110},
        {"label": "Outstanding", "fieldname": "outstanding", "fieldtype": "Currency", "width": 110},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
    ]