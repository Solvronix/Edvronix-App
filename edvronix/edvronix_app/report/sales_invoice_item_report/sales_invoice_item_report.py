import frappe
from frappe.utils import flt
import json
from itertools import groupby

ITEM_PAYMENT_PRIORITY = [
    "Annual Fund",
    "Monthly Tuition Fee",
    "Admission Fee",
    "Exam Fee",
]

@frappe.whitelist()
def execute(filters=None):
    if isinstance(filters, str):
        filters = json.loads(filters)
    
    if not filters:
        filters = {}

    if filters.get("no_annual_fund"):
        if not filters.get("academic_year") and not filters.get("month"):
            return get_missing_af_columns(), [], None, None, []
        data = get_students_missing_annual_fund(filters)
        summary = [{"value": len(data), "label": "Students Missing Annual Fund", "datatype": "Int", "indicator": "Red"}]
        return get_missing_af_columns(), data, None, None, summary

    columns = get_columns()
    data = get_data(filters)

    if data:
        total_amount = sum(flt(d['amount']) for d in data)
        total_paid = sum(flt(d['paid']) for d in data)
        total_outstanding = sum(flt(d['outstanding']) for d in data)
        data.append({
            "invoice": "",
            "student": "",
            "student_name": "<b>TOTAL</b>",
            "guardian_name": "",
            "program": "",
            "student_category": "",
            "item": "",
            "amount": total_amount,
            "paid": total_paid,
            "outstanding": total_outstanding,
            "invoice_status": "",
            "payment_date": "",
            "posting_date": "",
        })

    summary = get_report_summary(data[:-1] if data else [], filters)

    return columns, data, None, None, summary

def get_columns():
    return [
        {"label": "Invoice ID", "fieldname": "invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 200},
        {"label": "Student", "fieldname": "student", "fieldtype": "Link", "options": "Student", "width": 130},
        {"label": "Student Name", "fieldname": "student_name", "fieldtype": "Data", "width": 180},
        {"label": "Guardian Name", "fieldname": "guardian_name", "fieldtype": "Data", "width": 160},
        {"label": "Class", "fieldname": "program", "fieldtype": "Link", "options": "Program", "width": 150},
        {"label": "Section", "fieldname": "student_category", "fieldtype": "Link", "options": "Student Category", "width": 130},
        {"label": "Item", "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 180},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 130},
        {"label": "Paid", "fieldname": "paid", "fieldtype": "Currency", "width": 130},
        {"label": "Outstanding", "fieldname": "outstanding", "fieldtype": "Currency", "width": 130},
        {"label": "Invoice Status", "fieldname": "invoice_status", "fieldtype": "Data", "width": 120},
        {"label": "Payment Date", "fieldname": "payment_date", "fieldtype": "Date", "width": 120},
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 130},
    ]

def get_data(filters):
    conditions, values = build_conditions(filters)
    
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    values["academic_year_pe"] = filters.get("academic_year") or ""

    query = f"""
        SELECT
            si.name AS invoice,
            si.student AS student,
            s.student_name AS student_name,
            (SELECT g.guardian_name
             FROM `tabGuardian` g
             INNER JOIN `tabStudent Guardian` sg ON sg.guardian = g.name
             WHERE sg.parent = s.name
             ORDER BY sg.idx ASC LIMIT 1) AS guardian_name,
            pe.program AS program,
            pe.student_category AS student_category,
            si_item.item_code AS item,
            si_item.amount AS amount,
            si_item.idx AS item_idx,
            (si.grand_total - si.outstanding_amount) AS invoice_paid,
            CASE
                WHEN si.outstanding_amount = 0 THEN 'Fully Paid'
                WHEN si.outstanding_amount = si.grand_total THEN 'Not Paid'
                ELSE 'Partial Paid'
            END AS invoice_status,
            (SELECT MAX(pe2.posting_date)
             FROM `tabPayment Entry` pe2
             INNER JOIN `tabPayment Entry Reference` per ON pe2.name = per.parent
             WHERE per.reference_name = si.name
             AND pe2.docstatus = 1) AS payment_date,
            si.posting_date AS posting_date
        FROM
            `tabSales Invoice` AS si
        INNER JOIN
            `tabSales Invoice Item` AS si_item ON si_item.parent = si.name
        LEFT JOIN
            `tabStudent` AS s ON s.name = si.student
        LEFT JOIN
            `tabProgram Enrollment` pe
            ON pe.student = si.student
            AND pe.docstatus = 1
            AND pe.name = (
                SELECT name FROM `tabProgram Enrollment` pe_sub
                WHERE pe_sub.student = si.student AND pe_sub.docstatus = 1
                  AND (%(academic_year_pe)s = '' OR pe_sub.academic_year = %(academic_year_pe)s)
                ORDER BY pe_sub.academic_year DESC LIMIT 1
            )
        {where_clause}
        ORDER BY
            si.posting_date DESC, si.name, si_item.idx
    """

    raw = frappe.db.sql(query, values, as_dict=1)
    result = apply_priority_allocation(raw)

    # Show only the selected item's rows (allocation still ran on all items)
    if filters.get("item"):
        result = [r for r in result if r['item'] == filters.get("item")]

    # Re-filter at item level after allocation (SQL filters at invoice level only)
    if filters.get("unpaid_only") and not filters.get("paid_only"):
        result = [r for r in result if flt(r['outstanding']) > 0]
    elif filters.get("paid_only") and not filters.get("unpaid_only"):
        result = [r for r in result if flt(r['outstanding']) == 0]

    return result

def apply_priority_allocation(raw_data):
    def priority_key(row):
        try:
            return ITEM_PAYMENT_PRIORITY.index(row['item'])
        except ValueError:
            return len(ITEM_PAYMENT_PRIORITY) + (row.get('item_idx') or 0)

    result = []
    for invoice, rows in groupby(raw_data, key=lambda r: r['invoice']):
        rows = list(rows)
        remaining = flt(rows[0]['invoice_paid'])

        for row in sorted(rows, key=priority_key):
            item_amount = flt(row['amount'])
            item_paid = min(item_amount, remaining)
            remaining -= item_paid

            result.append({
                'invoice': row['invoice'],
                'student': row['student'],
                'student_name': row['student_name'],
                'guardian_name': row.get('guardian_name') or '',
                'program': row.get('program') or '',
                'student_category': row.get('student_category') or '',
                'item': row['item'],
                'amount': item_amount,
                'paid': item_paid,
                'outstanding': item_amount - item_paid,
                'invoice_status': row.get('invoice_status') or '',
                'payment_date': row['payment_date'],
                'posting_date': row['posting_date'],
            })

    return result

def build_conditions(filters):
    conditions = []
    values = {}
    
    if filters.get("item"):
        conditions.append("si.name IN (SELECT parent FROM `tabSales Invoice Item` WHERE item_code = %(item)s)")
        values["item"] = filters.get("item")
        
    if filters.get("month"):
        conditions.append("MONTHNAME(si.due_date) = %(month)s")
        values["month"] = filters.get("month")

    if filters.get("paid_only") and filters.get("unpaid_only"):
        conditions.append("1 = 0")
    elif filters.get("unpaid_only"):
        # Safe SQL optimisation: fully paid invoices can never have unpaid items
        conditions.append("si.outstanding_amount > 0")

    if filters.get("academic_year"):
        conditions.append("""
            si.student IN (
                SELECT student FROM `tabProgram Enrollment`
                WHERE docstatus = 1 AND academic_year = %(academic_year)s
            )
        """)
        values["academic_year"] = filters.get("academic_year")
        
    if filters.get("min_amount"):
        conditions.append("si_item.amount >= %(min_amount)s")
        values["min_amount"] = flt(filters.get("min_amount"))
        
    if filters.get("max_amount"):
        conditions.append("si_item.amount <= %(max_amount)s")
        values["max_amount"] = flt(filters.get("max_amount"))
    
    if filters.get("from_date"):
        conditions.append("si.posting_date >= %(from_date)s")
        values["from_date"] = filters.get("from_date")
        
    if filters.get("to_date"):
        conditions.append("si.posting_date <= %(to_date)s")
        values["to_date"] = filters.get("to_date")
        
    conditions.append("si.docstatus = 1")
    
    return conditions, values

def get_missing_af_columns():
    return [
        {"label": "Student", "fieldname": "student", "fieldtype": "Link", "options": "Student", "width": 130},
        {"label": "Student Name", "fieldname": "student_name", "fieldtype": "Data", "width": 200},
        {"label": "Guardian Name", "fieldname": "guardian_name", "fieldtype": "Data", "width": 160},
        {"label": "Program", "fieldname": "program", "fieldtype": "Link", "options": "Program", "width": 150},
        {"label": "Section", "fieldname": "student_category", "fieldtype": "Link", "options": "Student Category", "width": 130},
        {"label": "Academic Year", "fieldname": "academic_year", "fieldtype": "Data", "width": 120},
    ]

def get_students_missing_annual_fund(filters):
    values = {
        "academic_year": filters.get("academic_year") or "",
        "month": filters.get("month") or "",
    }

    return frappe.db.sql("""
        SELECT
            s.name AS student,
            s.student_name AS student_name,
            (SELECT g.guardian_name
             FROM `tabGuardian` g
             INNER JOIN `tabStudent Guardian` sg ON sg.guardian = g.name
             WHERE sg.parent = s.name
             ORDER BY sg.idx ASC LIMIT 1) AS guardian_name,
            pe.program AS program,
            pe.student_category AS student_category,
            pe.academic_year AS academic_year
        FROM `tabStudent` s
        INNER JOIN `tabProgram Enrollment` pe ON pe.student = s.name AND pe.docstatus = 1
            AND (%(academic_year)s = '' OR pe.academic_year = %(academic_year)s)
        WHERE s.name NOT IN (
            SELECT si.student
            FROM `tabSales Invoice` si
            INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
            WHERE si.docstatus = 1
                AND sii.item_code = 'Annual Fund'
                AND si.student IS NOT NULL AND si.student != ''
                AND (%(month)s = '' OR MONTHNAME(si.due_date) = %(month)s)
                AND (%(academic_year)s = '' OR si.student IN (
                    SELECT student FROM `tabProgram Enrollment`
                    WHERE docstatus = 1 AND academic_year = %(academic_year)s
                ))
        )
        AND s.name IS NOT NULL AND s.name != ''
        AND s.enabled = 1
        ORDER BY s.student_name ASC
    """, values, as_dict=1)

def get_report_summary(data, filters):
    if not data:
        return []

    student_count = len({d['student'] for d in data if d.get('student')})

    fully_paid_students = len({d['student'] for d in data if d.get('student') and d.get('invoice_status') == 'Fully Paid'})
    partial_paid_students = len({d['student'] for d in data if d.get('student') and d.get('invoice_status') == 'Partial Paid'})
    not_paid_students = len({d['student'] for d in data if d.get('student') and d.get('invoice_status') == 'Not Paid'})

    total_amount = sum(flt(d['amount']) for d in data)
    total_paid = sum(flt(d['paid']) for d in data)
    total_outstanding = sum(flt(d['outstanding']) for d in data)

    selected_item_label = "Total Amount"
    if filters.get("item"):
        item_name = frappe.db.get_value("Item", filters.get("item"), "item_name")
        selected_item_label = f"Total {item_name or filters.get('item')}"

    return [
        {"value": student_count, "label": "Total Students", "datatype": "Int", "indicator": "Blue"},
        {"value": fully_paid_students, "label": "Fully Paid", "datatype": "Int", "indicator": "Green"},
        {"value": partial_paid_students, "label": "Partial Paid", "datatype": "Int", "indicator": "Orange"},
        {"value": not_paid_students, "label": "Not Paid", "datatype": "Int", "indicator": "Red"},
        {"value": total_amount, "label": selected_item_label, "datatype": "Currency", "indicator": "Blue"},
        {"value": total_paid, "label": "Total Paid", "datatype": "Currency", "indicator": "Green"},
        {"value": total_outstanding, "label": "Total Pending", "datatype": "Currency", "indicator": "Red"},
    ]