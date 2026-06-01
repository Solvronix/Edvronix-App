import frappe
from frappe.utils import flt
import json


@frappe.whitelist()
def execute(filters=None):
    if isinstance(filters, str):
        filters = json.loads(filters)

    if not filters:
        filters = {}

    if not filters.get("from_date") or not filters.get("to_date"):
        return get_columns(), [], None, None, []

    columns = get_columns()
    data = get_data(filters)

    total_debit = sum(flt(d["total_debit"]) for d in data)
    total_credit = sum(flt(d["total_credit"]) for d in data)

    if data:
        data.append({
            "name": "",
            "posting_date": "",
            "voucher_type": "",
            "title": "<b>TOTAL</b>",
            "total_debit": total_debit,
            "total_credit": total_credit,
            "user_remark": "",
        })

    summary = [
        {"value": len(data) - (1 if data else 0), "label": "Total Entries", "datatype": "Int", "indicator": "Blue"},
        {"value": total_debit, "label": "Total Debit", "datatype": "Currency", "indicator": "Blue"},
        {"value": total_credit, "label": "Total Credit", "datatype": "Currency", "indicator": "Green"},
    ]

    return columns, data, None, None, summary


def get_columns():
    return [
        {"label": "Journal Entry", "fieldname": "name", "fieldtype": "Link", "options": "Journal Entry", "width": 180},
        {"label": "Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
        {"label": "Entry Type", "fieldname": "voucher_type", "fieldtype": "Data", "width": 140},
        {"label": "Title", "fieldname": "title", "fieldtype": "Data", "width": 220},
        {"label": "Debit", "fieldname": "total_debit", "fieldtype": "Currency", "width": 130},
        {"label": "Credit", "fieldname": "total_credit", "fieldtype": "Currency", "width": 130},
        {"label": "Remark", "fieldname": "user_remark", "fieldtype": "Data", "width": 250},
    ]


def get_data(filters):
    return frappe.db.sql("""
        SELECT
            je.name,
            je.posting_date,
            je.voucher_type,
            je.title,
            je.total_debit,
            je.total_credit,
            je.user_remark
        FROM `tabJournal Entry` je
        WHERE je.docstatus = 1
            AND je.posting_date >= %(from_date)s
            AND je.posting_date <= %(to_date)s
            AND (%(voucher_type)s = '' OR je.voucher_type = %(voucher_type)s)
        ORDER BY je.posting_date ASC, je.name ASC
    """, {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "voucher_type": filters.get("voucher_type") or "",
    }, as_dict=1)
