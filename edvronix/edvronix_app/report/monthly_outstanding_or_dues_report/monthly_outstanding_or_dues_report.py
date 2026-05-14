import frappe
from frappe.utils import flt
import json
from datetime import datetime

@frappe.whitelist()
def execute(filters=None):
    if isinstance(filters, str):
        filters = json.loads(filters)

    if not filters:
        filters = {}

    columns = get_columns()

    # Get filter values
    student = filters.get("student")
    program = filters.get("program")
    student_category = filters.get("student_category")
    academic_year = filters.get("academic_year")
    month = filters.get("month")
    only_outstanding = filters.get("only_outstanding")
    show_defaulters = filters.get("show_defaulters")
    partial_paid = filters.get("partial_paid")

    # Guard Clause
    if not any([student, program, academic_year, month]):
         return columns, [], None, None, []

    # Month conversion
    month_display = ""
    if month:
        try:
            month_display = datetime(2000, int(month), 1).strftime('%B')
        except:
            month_display = month

    params = {
        "student": student or "",
        "program": program or "",
        "academic_year": academic_year or "",
        "month": month_display or "",
        "month_display": month_display,
        "only_outstanding": 1 if (only_outstanding or show_defaulters) else 0,
        "partial_paid": 1 if partial_paid else 0,
        "show_defaulters": 1 if show_defaulters else 0
    }

    # --- Invoice Data ---
    # When Show Defaulters + All months: one row per student per pending month
    if show_defaulters and not month:
        data = get_defaulter_month_rows(params)
    else:
        data = frappe.db.sql("""
        SELECT
            s.name AS student,
            s.student_name AS student_name,
            s.student_mobile_number AS student_mobile_number, -- Added Field
            g.name AS guardian_id,
            g.guardian_name AS guardian_name,
            %(month_display)s AS fee_month,
            MAX(si.due_date) AS due_date,
            pe.program AS program,
            pe.student_category AS student_category,
            pe.academic_year AS academic_year,
            COUNT(si.name) AS invoice_count,
            SUM(si.grand_total) AS total_fee,
            SUM(si.grand_total - si.outstanding_amount) AS paid_amount,
            SUM(si.outstanding_amount) AS outstanding,
            (SELECT MAX(pe.posting_date)
             FROM `tabPayment Entry` pe
             INNER JOIN `tabPayment Entry Reference` per ON pe.name = per.parent
             INNER JOIN `tabSales Invoice` si2 ON si2.name = per.reference_name
             WHERE si2.student = s.name
             AND si2.docstatus = 1
             AND pe.docstatus = 1
             AND (%(month_display)s = '' OR MONTHNAME(si2.due_date) = %(month_display)s)) AS payment_date,
            CASE
                WHEN COUNT(si.name) > 1 THEN 'Defaulter'
                ELSE 'Active'
            END AS status
        FROM `tabStudent` s
        LEFT JOIN `tabStudent Guardian` sg ON sg.parent = s.name
        LEFT JOIN `tabGuardian` g ON g.name = sg.guardian
        INNER JOIN `tabSales Invoice` si ON si.student = s.name AND si.docstatus = 1
        LEFT JOIN `tabProgram Enrollment` pe ON pe.student = s.name AND pe.docstatus = 1
            AND (%(academic_year)s = '' OR pe.academic_year = %(academic_year)s)
        WHERE 1=1
            AND (%(student)s = '' OR s.name = %(student)s)
            AND (%(program)s = '' OR pe.program = %(program)s)
            AND (%(academic_year)s = '' OR pe.academic_year = %(academic_year)s)
            AND (%(month)s = '' OR MONTHNAME(si.due_date) = %(month)s)
            AND (%(only_outstanding)s = 0 OR si.outstanding_amount > 0)
            AND (
                %(partial_paid)s = 0
                OR (si.outstanding_amount > 0 AND si.outstanding_amount < si.grand_total)
            )
        GROUP BY s.name
        HAVING (%(show_defaulters)s = 0 OR COUNT(si.name) > 1)
    """, params, as_dict=True)

    # --- Summary Calculations ---
    total_fee_sum = 0
    total_paid_sum = 0
    total_outstanding_sum = 0

    for d in data:
        total_fee_sum += flt(d.get("total_fee"))
        total_paid_sum += flt(d.get("paid_amount"))
        total_outstanding_sum += flt(d.get("outstanding"))

    # --- Add Total Row to Data ---
    if data:
        data.append({
            "student": "",
            "student_name": "<b>TOTAL</b>",
            "student_mobile_number": "",
            "guardian_id": "",
            "guardian_name": "",
            "fee_month": "",
            "total_fee": total_fee_sum,
            "paid_amount": total_paid_sum,
            "outstanding": total_outstanding_sum,
            "status": "",
            "due_date": "",
            "payment_date": "",
            "program": "",
            "student_category": "",
            "academic_year": "",
            "invoice_count": "",
        })

    students_in_report = list(set(d.student for d in data if d.get("student")))

    # --- Arrears Calculation ---
    # Arrears = outstanding on any invoice that is NOT the selected month (same logic as fee_vouher_in_bulk_with_bank)
    arrears = 0.0
    if month:
        arrears_conditions = "si.docstatus = 1 AND si.outstanding_amount > 0 AND MONTHNAME(si.due_date) != %(month_display)s"
        arrears_params = {"month_display": month_display}

        if academic_year or program:
            sub_cond = "WHERE 1=1"
            if academic_year:
                sub_cond += " AND academic_year = %(academic_year)s"
                arrears_params["academic_year"] = academic_year
            if program:
                sub_cond += " AND program = %(program)s"
                arrears_params["program"] = program
            arrears_conditions += f" AND si.student IN (SELECT student FROM `tabProgram Enrollment` {sub_cond})"

        if student:
            arrears_conditions += " AND si.student = %(student)s"
            arrears_params["student"] = student

        arrears_result = frappe.db.sql(f"""
            SELECT SUM(si.outstanding_amount)
            FROM `tabSales Invoice` si
            WHERE {arrears_conditions}
        """, arrears_params)
        arrears = flt(arrears_result[0][0]) if arrears_result else 0.0

    target = total_fee_sum + arrears

    report_summary = [
        {"value": len(students_in_report), "label": "Total Students", "datatype": "Int", "indicator": "Blue"},
        {"value": total_fee_sum, "label": "Total Fee", "datatype": "Currency", "indicator": "Blue"},
        {"value": arrears, "label": "Arrears", "datatype": "Currency", "indicator": "Orange"},
        {"value": target, "label": "Target (Fee + Arrears)", "datatype": "Currency", "indicator": "Purple"},
        {"value": total_paid_sum, "label": "Total Paid", "datatype": "Currency", "indicator": "Green"},
        {"value": total_outstanding_sum, "label": "Outstanding", "datatype": "Currency", "indicator": "Red"},
    ]

    return columns, data, None, None, report_summary

def get_columns():
    return [
        {"label": "Student", "fieldname": "student", "fieldtype": "Link", "options": "Student", "width": 120},
        {"label": "Student Name", "fieldname": "student_name", "fieldtype": "Data", "width": 150},
        {"label": "Mobile Number", "fieldname": "student_mobile_number", "fieldtype": "Data", "width": 120}, # Added Column
        {"label": "Guardian ID", "fieldname": "guardian_id", "fieldtype": "Link", "options": "Guardian", "width": 120},
        {"label": "Guardian Name", "fieldname": "guardian_name", "fieldtype": "Data", "width": 150},
        {"label": "Fee Month", "fieldname": "fee_month", "fieldtype": "Data", "width": 100},
        {"label": "Total Fee", "fieldname": "total_fee", "fieldtype": "Currency", "width": 120},
        {"label": "Paid Amount", "fieldname": "paid_amount", "fieldtype": "Currency", "width": 120},
        {"label": "Outstanding", "fieldname": "outstanding", "fieldtype": "Currency", "width": 120},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 110},
        {"label": "Payment Date", "fieldname": "payment_date", "fieldtype": "Date", "width": 120},
        {"label": "Program", "fieldname": "program", "fieldtype": "Link", "options": "Program", "width": 120},
        {"label": "Section", "fieldname": "student_category", "fieldtype": "Link", "options": "Student Category", "width": 120},
        {"label": "Academic Year", "fieldname": "academic_year", "fieldtype": "Data", "width": 110},
        {"label": "Invoice Count", "fieldname": "invoice_count", "fieldtype": "Int", "width": 100},
    ]


def get_defaulter_month_rows(params):
    """One row per student with all pending months listed — used when Show Defaulters + All months."""
    return frappe.db.sql("""
        SELECT
            s.name AS student,
            s.student_name AS student_name,
            s.student_mobile_number AS student_mobile_number,
            g.name AS guardian_id,
            g.guardian_name AS guardian_name,
            GROUP_CONCAT(DISTINCT MONTHNAME(si.due_date) ORDER BY MONTH(si.due_date) SEPARATOR ', ') AS fee_month,
            MAX(si.due_date) AS due_date,
            pe.program AS program,
            pe.student_category AS student_category,
            pe.academic_year AS academic_year,
            COUNT(si.name) AS invoice_count,
            SUM(si.grand_total) AS total_fee,
            SUM(si.grand_total - si.outstanding_amount) AS paid_amount,
            SUM(si.outstanding_amount) AS outstanding,
            (SELECT MAX(pe2.posting_date)
             FROM `tabPayment Entry` pe2
             INNER JOIN `tabPayment Entry Reference` per2 ON pe2.name = per2.parent
             INNER JOIN `tabSales Invoice` si2 ON si2.name = per2.reference_name
             WHERE si2.student = s.name
             AND si2.docstatus = 1
             AND pe2.docstatus = 1) AS payment_date,
            'Defaulter' AS status
        FROM `tabStudent` s
        LEFT JOIN `tabStudent Guardian` sg ON sg.parent = s.name
        LEFT JOIN `tabGuardian` g ON g.name = sg.guardian
        INNER JOIN `tabSales Invoice` si ON si.student = s.name
            AND si.docstatus = 1
            AND si.outstanding_amount > 0
        LEFT JOIN `tabProgram Enrollment` pe ON pe.student = s.name AND pe.docstatus = 1
            AND (%(academic_year)s = '' OR pe.academic_year = %(academic_year)s)
        WHERE 1=1
            AND (%(student)s = '' OR s.name = %(student)s)
            AND (%(program)s = '' OR pe.program = %(program)s)
            AND (%(academic_year)s = '' OR pe.academic_year = %(academic_year)s)
        GROUP BY s.name
        HAVING COUNT(si.name) > 1
        ORDER BY s.student_name ASC
    """, params, as_dict=True)