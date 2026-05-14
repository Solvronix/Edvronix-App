import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Payment ID"), "fieldname": "name", "fieldtype": "Link", "options": "Payment Entry", "width": 150},
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": _("Student"), "fieldname": "party", "fieldtype": "Link", "options": "Student", "width": 150},
        {"label": _("Student Name"), "fieldname": "party_name", "fieldtype": "Data", "width": 150},
        {"label": _("Amount"), "fieldname": "paid_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
    ]

def get_data(filters):
    # This query finds payments where no reference invoice exists
    data = frappe.db.sql("""
        SELECT 
            pe.name, pe.posting_date, pe.party, pe.party_name, pe.paid_amount, pe.status
        FROM 
            `tabPayment Entry` pe
        LEFT JOIN 
            `tabPayment Entry Reference` per ON pe.name = per.parent
        WHERE 
            pe.party_type = 'Student' 
            AND pe.docstatus = 1
            AND (per.reference_name IS NULL OR per.reference_name = '')
    """, as_dict=True)
    
    return data