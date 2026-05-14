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
    data = get_data(filters)
    summary = get_report_summary(data, filters)

    return columns, data, None, None, summary

def get_columns():
    return [
        {"label": "Invoice ID", "fieldname": "invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 200},
        {"label": "Student", "fieldname": "student", "fieldtype": "Link", "options": "Student", "width": 130},
        {"label": "Student Name", "fieldname": "student_name", "fieldtype": "Data", "width": 180},
        {"label": "Item", "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 180},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 130},
        {"label": "Paid", "fieldname": "paid", "fieldtype": "Currency", "width": 130},
        {"label": "Outstanding", "fieldname": "outstanding", "fieldtype": "Currency", "width": 130},
        {"label": "Payment Date", "fieldname": "payment_date", "fieldtype": "Date", "width": 120},
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 130},
    ]

def get_data(filters):
    conditions, values = build_conditions(filters)
    
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # One row per item line. Paid/outstanding are proportional to each item's
    # share of the invoice total so filtering by a specific item gives correct figures.
    query = f"""
        SELECT
            si.name AS invoice,
            si.student AS student,
            s.student_name AS student_name,
            si_item.item_code AS item,
            si_item.amount AS amount,
            ROUND((si_item.amount / NULLIF(si.total, 0)) * (si.grand_total - si.outstanding_amount), 2) AS paid,
            ROUND((si_item.amount / NULLIF(si.total, 0)) * si.outstanding_amount, 2) AS outstanding,
            (SELECT MAX(pe.posting_date)
             FROM `tabPayment Entry` pe
             INNER JOIN `tabPayment Entry Reference` per ON pe.name = per.parent
             WHERE per.reference_name = si.name
             AND pe.docstatus = 1) AS payment_date,
            si.posting_date AS posting_date
        FROM
            `tabSales Invoice` AS si
        INNER JOIN
            `tabSales Invoice Item` AS si_item ON si_item.parent = si.name
        LEFT JOIN
            `tabStudent` AS s ON s.name = si.student
        {where_clause}
        ORDER BY
            si.posting_date DESC, si.name, si_item.idx
    """

    return frappe.db.sql(query, values, as_dict=1)

def build_conditions(filters):
    conditions = []
    values = {}
    
    if filters.get("item"):
        conditions.append("si_item.item_code = %(item)s")
        values["item"] = filters.get("item")
        
    if filters.get("month"):
        conditions.append("MONTHNAME(si.due_date) = %(month)s")
        values["month"] = filters.get("month")

    if filters.get("paid_only") and filters.get("unpaid_only"):
        conditions.append("1 = 0")
    elif filters.get("unpaid_only"):
        conditions.append("si.outstanding_amount > 0")
    elif filters.get("paid_only"):
        conditions.append("si.outstanding_amount = 0")

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

def get_report_summary(data, filters):
    if not data:
        return []

    student_count = len({d['student'] for d in data if d.get('student')})

    total_amount = sum(flt(d['amount']) for d in data)
    total_paid = sum(flt(d['paid']) for d in data)
    total_outstanding = sum(flt(d['outstanding']) for d in data)

    selected_item_label = "Total Amount"
    if filters.get("item"):
        item_name = frappe.db.get_value("Item", filters.get("item"), "item_name")
        selected_item_label = f"Total {item_name or filters.get('item')}"

    return [
        {"value": student_count, "label": "Total Students", "datatype": "Int", "indicator": "Blue"},
        {"value": total_amount, "label": selected_item_label, "datatype": "Currency", "indicator": "Blue"},
        {"value": total_paid, "label": "Total Paid", "datatype": "Currency", "indicator": "Green"},
        {"value": total_outstanding, "label": "Total Pending", "datatype": "Currency", "indicator": "Red"},
    ]