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
        {"label": _("Student"), "fieldname": "student", "fieldtype": "Link", "options": "Student", "width": 150},
        {"label": _("Student Name"), "fieldname": "student_name", "fieldtype": "Data", "width": 180},
        {"label": _("Amount"), "fieldname": "paid_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
    ]


def get_data(filters):
    # Payment Entry uses party_type='Customer'; join tabStudent via the customer field
    # to surface the student name. Unallocated = no reference invoice linked.
    return frappe.db.sql("""
        SELECT
            pe.name,
            pe.posting_date,
            s.name   AS student,
            s.student_name,
            pe.paid_amount,
            pe.status
        FROM `tabPayment Entry` pe
        INNER JOIN `tabStudent` s ON s.customer = pe.party
        LEFT JOIN `tabPayment Entry Reference` per ON per.parent = pe.name
        WHERE pe.party_type = 'Customer'
          AND pe.docstatus = 1
          AND (per.reference_name IS NULL OR per.reference_name = '')
        ORDER BY pe.posting_date DESC
    """, as_dict=True)
