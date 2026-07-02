import frappe
from frappe.utils import flt
import json

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data

def get_columns():
    return [
        {"label": "Total Students", "fieldname": "students", "fieldtype": "Int", "width": 120},
        {"label": "Current Fee (" + frappe.utils.formatdate(frappe.utils.today(), "MMMM") + ")", "fieldname": "current_fee", "fieldtype": "Currency", "width": 150},
        {"label": "Total Arrears", "fieldname": "arrears", "fieldtype": "Currency", "width": 130},
        {"label": "Total Receivable", "fieldname": "total_receivable", "fieldtype": "Currency", "width": 150},
        {"label": "Advance Payments", "fieldname": "advance", "fieldtype": "Currency", "width": 130},
        {"label": "Fee Received", "fieldname": "fee_received", "fieldtype": "Currency", "width": 150},
        {"label": "Net Balance", "fieldname": "balance", "fieldtype": "Currency", "width": 150},
    ]

def get_data(filters):
    conditions = "si.docstatus = 1"
    params = {}

    # 1. Date/Month Filter - Using the logic from your working report
    if filters.get("month"):
        conditions += " AND MONTHNAME(si.posting_date) = %(month)s"
        params["month"] = filters.get("month")

    # 2. Program/Academic Year (Using IN clause to avoid JOIN duplication)
    if filters.get("academic_year") or filters.get("program"):
        sub_query_cond = "WHERE 1=1"
        if filters.get("academic_year"):
            sub_query_cond += " AND academic_year = %(academic_year)s"
            params["academic_year"] = filters.get("academic_year")
        if filters.get("program"):
            sub_query_cond += " AND program = %(program)s"
            params["program"] = filters.get("program")

        conditions += f""" AND si.student IN (
            SELECT student FROM `tabProgram Enrollment` {sub_query_cond}
        )"""

    # 3. Execution - Single Row Summary
    # Using si.student (from Sales Invoice) ensures we count everyone billed
    raw_data = frappe.db.sql(f"""
        SELECT
            COUNT(DISTINCT si.student) as students,
            SUM(si.grand_total) as current_fee,
            SUM(si.outstanding_amount) as balance,
            SUM(si.grand_total - si.outstanding_amount) as fee_received
        FROM `tabSales Invoice` si
        WHERE {conditions}
    """, params, as_dict=1)

    res = raw_data[0] if raw_data else {}

    # 4. Advance Calculation (Global or Filtered)
    advance = frappe.db.sql("""
        SELECT SUM(unallocated_amount)
        FROM `tabPayment Entry`
        WHERE docstatus = 1 AND party_type = 'Customer'
    """)[0][0] or 0

    # 5. Final Math
    current_val = flt(res.get("current_fee", 0))
    balance_val = flt(res.get("balance", 0))
    received_val = flt(res.get("fee_received", 0))
    
    # In school terms: Arrears + Current = Total Receivable
    # Since 'balance' in this query is the total remaining on March invoices:
    return [{
        "students": res.get("students", 0),
        "current_fee": current_val,
        "arrears": balance_val, 
        "total_receivable": current_val, # Match this to your specific accounting preference
        "advance": flt(advance),
        "fee_received": received_val,
        "balance": balance_val
    }]