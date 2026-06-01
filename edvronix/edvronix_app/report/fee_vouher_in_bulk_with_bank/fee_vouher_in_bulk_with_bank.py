

import frappe
from frappe.utils import flt
import json

@frappe.whitelist()
def execute(filters=None):
    if isinstance(filters, str):
        filters = json.loads(filters)
    
    if not filters:
        filters = {}

    # If no filter at all → return empty
    if not filters.get("academic_year") and not filters.get("guardian") and not filters.get("month"):
        return get_columns(), [], None, None, []

    columns = get_columns()
    
    guardian = filters.get("guardian") or ""
    academic_year = filters.get("academic_year") or ""
    month = filters.get("month") or ""

    params = {
        "guardian": guardian,
        "academic_year": academic_year,
        "month": month
    }

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
            (SELECT GROUP_CONCAT(CONCAT(item_name, '|', CAST(ROUND(amount, 0) AS CHAR))
             ORDER BY IF(FIELD(item_code, 'Annual Fund', 'Monthly Tuition Fee', 'Admission Fee', 'Exam Fee') = 0,
                         999,
                         FIELD(item_code, 'Annual Fund', 'Monthly Tuition Fee', 'Admission Fee', 'Exam Fee')),
                      idx
             SEPARATOR '::')
            FROM `tabSales Invoice Item`
            WHERE parent = si.name) AS invoice_items,
            si.due_date AS due_date,
            COALESCE(si.grand_total, 0) AS total_per_student,
            COALESCE(si.outstanding_amount, 0) AS outstanding,
            (COALESCE(si.grand_total, 0) - COALESCE(si.outstanding_amount, 0)) AS paid_amount,
            
            /* Logic to get the most recent payment date for this invoice */
            (SELECT MAX(pe_entry.posting_date)
             FROM `tabPayment Entry` pe_entry
             INNER JOIN `tabPayment Entry Reference` per ON pe_entry.name = per.parent
             WHERE per.reference_name = si.name 
             AND pe_entry.docstatus = 1) AS payment_date,

            (
                SELECT COALESCE(SUM(si2.outstanding_amount), 0)
                FROM `tabSales Invoice` si2
                WHERE
                    si2.student = s.name
                    AND si2.docstatus = 1
                    AND si2.name != si.name
                    AND (%(month)s = '' OR si2.due_date < (
                        SELECT MIN(si_ref.due_date) FROM `tabSales Invoice` si_ref
                        WHERE si_ref.docstatus = 1 AND MONTHNAME(si_ref.due_date) = %(month)s
                    ))
            ) AS arrears,

            (
                SELECT GROUP_CONCAT(
                    CONCAT(
                        sii.item_name, '|',
                        CAST(ROUND(
                            sii.amount - GREATEST(0, LEAST(sii.amount,
                                (si2.grand_total - si2.outstanding_amount) - COALESCE((
                                    SELECT SUM(sp.amount)
                                    FROM `tabSales Invoice Item` sp
                                    WHERE sp.parent = sii.parent
                                    AND (
                                        IF(FIELD(sp.item_code,'Annual Fund','Monthly Tuition Fee','Admission Fee','Exam Fee')=0,999,
                                           FIELD(sp.item_code,'Annual Fund','Monthly Tuition Fee','Admission Fee','Exam Fee'))*1000 + sp.idx
                                        <
                                        IF(FIELD(sii.item_code,'Annual Fund','Monthly Tuition Fee','Admission Fee','Exam Fee')=0,999,
                                           FIELD(sii.item_code,'Annual Fund','Monthly Tuition Fee','Admission Fee','Exam Fee'))*1000 + sii.idx
                                    )
                                ), 0)
                            )), 0) AS CHAR),
                        '|', COALESCE(DATE_FORMAT(si2.due_date, '%%b'), '')
                    )
                    ORDER BY IF(FIELD(sii.item_code, 'Annual Fund', 'Monthly Tuition Fee', 'Admission Fee', 'Exam Fee') = 0,
                               999,
                               FIELD(sii.item_code, 'Annual Fund', 'Monthly Tuition Fee', 'Admission Fee', 'Exam Fee')),
                             sii.idx
                    SEPARATOR '::'
                )
                FROM `tabSales Invoice` si2
                INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si2.name
                WHERE si2.student = s.name
                    AND si2.docstatus = 1
                    AND si2.name != si.name
                    AND si2.outstanding_amount > 0
                    AND (%(month)s = '' OR si2.due_date < (
                        SELECT MIN(si_ref.due_date) FROM `tabSales Invoice` si_ref
                        WHERE si_ref.docstatus = 1 AND MONTHNAME(si_ref.due_date) = %(month)s
                    ))
                    AND (si2.grand_total - si2.outstanding_amount) < (
                        SELECT COALESCE(SUM(sp.amount), 0)
                        FROM `tabSales Invoice Item` sp
                        WHERE sp.parent = sii.parent
                        AND (
                            IF(FIELD(sp.item_code,'Annual Fund','Monthly Tuition Fee','Admission Fee','Exam Fee')=0,999,
                               FIELD(sp.item_code,'Annual Fund','Monthly Tuition Fee','Admission Fee','Exam Fee'))*1000 + sp.idx
                            <=
                            IF(FIELD(sii.item_code,'Annual Fund','Monthly Tuition Fee','Admission Fee','Exam Fee')=0,999,
                               FIELD(sii.item_code,'Annual Fund','Monthly Tuition Fee','Admission Fee','Exam Fee'))*1000 + sii.idx
                        )
                    )
            ) AS arrears_detail,

            COALESCE(si.status, 'No Invoice') AS status
        FROM `tabGuardian` g
        INNER JOIN `tabStudent Guardian` sg ON g.name = sg.guardian
        INNER JOIN `tabStudent` s ON sg.parent = s.name AND sg.parenttype = 'Student'
        LEFT JOIN `tabProgram Enrollment` pe 
            ON pe.student = s.name 
            AND pe.docstatus = 1
            AND (%(academic_year)s = '' OR pe.academic_year = %(academic_year)s)
        INNER JOIN `tabSales Invoice` si 
            ON si.student = s.name 
            AND si.docstatus = 1
            AND (%(month)s = '' OR MONTHNAME(si.due_date) = %(month)s)
        WHERE
            1=1
            AND (%(guardian)s = '' OR g.name = %(guardian)s)
            AND (%(academic_year)s = '' OR pe.academic_year = %(academic_year)s)
        ORDER BY g.guardian_name ASC, s.student_name ASC, si.due_date ASC
    """, params, as_dict=True)

    # Totals from data rows
    total_outstanding = sum(flt(d.outstanding) for d in data)
    total_paid = sum(flt(d.paid_amount) for d in data)
    total_fee = total_paid + total_outstanding
    total_students = len(set(d.student_id for d in data if d.get("student_id")))

    # Arrears = outstanding on invoices NOT in the selected month (same students)
    arrears = 0.0
    if month:
        arrears_conditions = """si.docstatus = 1 AND si.outstanding_amount > 0
            AND si.due_date < (
                SELECT MIN(si_ref.due_date) FROM `tabSales Invoice` si_ref
                WHERE si_ref.docstatus = 1 AND MONTHNAME(si_ref.due_date) = %(month)s
            )"""
        arrears_params = {"month": month}

        if academic_year:
            arrears_conditions += """ AND si.student IN (
                SELECT student FROM `tabProgram Enrollment`
                WHERE docstatus = 1 AND academic_year = %(academic_year)s
            )"""
            arrears_params["academic_year"] = academic_year

        if guardian:
            arrears_conditions += """ AND si.student IN (
                SELECT sg.parent FROM `tabStudent Guardian` sg
                WHERE sg.guardian = %(guardian)s AND sg.parenttype = 'Student'
            )"""
            arrears_params["guardian"] = guardian

        arrears_result = frappe.db.sql(f"""
            SELECT SUM(si.outstanding_amount)
            FROM `tabSales Invoice` si
            WHERE {arrears_conditions}
        """, arrears_params)
        arrears = flt(arrears_result[0][0]) if arrears_result else 0.0

    target = total_fee + arrears

    for d in data:
        d["outstanding"] = flt(d.get("outstanding", 0)) + flt(d.get("arrears", 0))

    report_summary = [
        {"value": total_students, "label": "Total Students", "datatype": "Int", "indicator": "Blue"},
        {"value": total_fee, "label": "Total Fee", "datatype": "Currency", "indicator": "Blue"},
        {"value": arrears, "label": "Arrears", "datatype": "Currency", "indicator": "Orange"},
        {"value": target, "label": "Target (Current Fee + Arrears)", "datatype": "Currency", "indicator": "Purple"},
        {"value": total_paid, "label": "Total Paid", "datatype": "Currency", "indicator": "Green"},
        {"value": target - total_paid, "label": "Outstanding (Target - Total Paid)", "datatype": "Currency", "indicator": "Red"},
    ]

    return columns, data, None, None, report_summary


def get_columns():
    return [
        {"label": "Student ID", "fieldname": "student_id", "fieldtype": "Link", "options": "Student", "width": 120},
        {"label": "Student Name", "fieldname": "student_name", "fieldtype": "Data", "width": 150},
        {"label": "Guardian ID", "fieldname": "guardian_id", "fieldtype": "Link", "options": "Guardian", "width": 120},
        {"label": "Parent Name", "fieldname": "parent_name", "fieldtype": "Data", "width": 150},
        {"label": "Program", "fieldname": "program", "fieldtype": "Data", "width": 120},
        {"label": "Section", "fieldname": "student_category", "fieldtype": "Data", "width": 100},
        {"label": "Invoice ID", "fieldname": "invoice_id", "fieldtype": "Link", "options": "Sales Invoice", "width": 120},
        {"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 100},
        {"label": "Paid Amount", "fieldname": "paid_amount", "fieldtype": "Currency", "width": 110},
        {"label": "Receiving Date", "fieldname": "payment_date", "fieldtype": "Date", "width": 110},
        {"label": "Outstanding", "fieldname": "outstanding", "fieldtype": "Currency", "width": 110},
        {"label": "Arrears", "fieldname": "arrears", "fieldtype": "Currency", "width": 120},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
    ]