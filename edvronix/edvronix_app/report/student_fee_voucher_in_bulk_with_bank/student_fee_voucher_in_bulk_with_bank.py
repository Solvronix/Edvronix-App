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
        "month": month
    }

    # The logic: We filter the Sales Invoice by the Month of the Due Date
    # and we filter the Program Enrollment by the Academic Year.
    data = frappe.db.sql("""
        SELECT
            g.name AS guardian_id,
            g.guardian_name AS parent_name,
            s.name AS student_id,
            s.student_name AS student_name,
            pe.program AS program,
            pe.student_category AS student_category,
            pe.academic_year AS academic_year,
            si.name AS invoice_id,
            si.due_date AS due_date,
            si.status AS status,
            (SELECT GROUP_CONCAT(CONCAT(item_name, ': ', CAST(ROUND(amount, 0) AS CHAR)) SEPARATOR ', ') 
             FROM `tabSales Invoice Item` 
             WHERE parent = si.name) AS invoice_items,
            COALESCE(si.grand_total, 0) AS total_amount,
            COALESCE(si.outstanding_amount, 0) AS outstanding,
            (COALESCE(si.grand_total, 0) - COALESCE(si.outstanding_amount, 0)) AS paid_amount
        FROM `tabGuardian` g
        INNER JOIN `tabStudent Guardian` sg ON g.name = sg.guardian
        INNER JOIN `tabStudent` s ON sg.parent = s.name AND sg.parenttype = 'Student'
        INNER JOIN `tabSales Invoice` si ON si.student = s.name AND si.docstatus = 1
        LEFT JOIN `tabProgram Enrollment` pe 
            ON pe.student = s.name 
            AND pe.docstatus = 1
        WHERE
            1=1
            AND (%(guardian)s = '' OR g.name = %(guardian)s)
            AND (%(academic_year)s = '' OR pe.academic_year = %(academic_year)s)
            AND (%(month)s = '' OR MONTHNAME(si.due_date) = %(month)s)
        ORDER BY si.due_date DESC, g.name ASC
    """, params, as_dict=True)

    # Totals for Dashboard
    total_val = sum(flt(d.total_amount) for d in data)
    total_out = sum(flt(d.outstanding) for d in data)
    total_paid = total_val - total_out

    report_summary = [
        {"value": total_val, "label": "Total Amount", "datatype": "Currency", "indicator": "Blue"},
        {"value": total_paid, "label": "Total Paid", "datatype": "Currency", "indicator": "Green"},
        {"value": total_out, "label": "Total Outstanding", "datatype": "Currency", "indicator": "Red"},
    ]

    return columns, data, None, None, report_summary

def get_columns():
    return [
        {"label": "Guardian ID", "fieldname": "guardian_id", "fieldtype": "Link", "options": "Guardian", "width": 120},
        {"label": "Parent Name", "fieldname": "parent_name", "fieldtype": "Data", "width": 150},
        {"label": "Student Name", "fieldname": "student_name", "fieldtype": "Data", "width": 150},
        {"label": "Academic Year", "fieldname": "academic_year", "fieldtype": "Link", "options": "Academic Year", "width": 110},
        {"label": "Invoice ID", "fieldname": "invoice_id", "fieldtype": "Link", "options": "Sales Invoice", "width": 120},
        {"label": "Items", "fieldname": "invoice_items", "fieldtype": "Data", "width": 200},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": "Student Category", "fieldname": "student_category", "fieldtype": "Data", "width": 120},
        {"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 100},
        {"label": "Total Amount", "fieldname": "total_amount", "fieldtype": "Currency", "width": 110},
        {"label": "Paid Amount", "fieldname": "paid_amount", "fieldtype": "Currency", "width": 110},
        {"label": "Outstanding", "fieldname": "outstanding", "fieldtype": "Currency", "width": 110},
    ]