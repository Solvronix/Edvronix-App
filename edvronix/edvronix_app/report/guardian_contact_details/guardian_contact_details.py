# Copyright (c) 2026, Solvronix and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = frappe._dict({})
        
    columns = get_columns()
    data = get_data(filters)
    
    # Calculate summary metrics
    total_guardians = len(data)
    # Filter out records where child_count is 0 if needed for this metric
    active_parents = len([d for d in data if d.get("child_count", 0) > 0])

    report_summary = [
        {
            "value": total_guardians,
            "label": _("Total Guardians"),
            "datatype": "Int",
            "indicator": "Blue"
        },
        {
            "value": active_parents,
            "label": _("Guardians with Children"),
            "datatype": "Int",
            "indicator": "Green"
        }
    ]

    return columns, data, None, None, report_summary

def get_columns():
    return [
        {"label": _("Guardian ID"), "fieldname": "name", "fieldtype": "Link", "options": "Guardian", "width": 150},
        {"label": _("Guardian Name"), "fieldname": "guardian_name", "fieldtype": "Data", "width": 180},
        {"label": _("Child Count"), "fieldname": "child_count", "fieldtype": "Int", "width": 100},
        {"label": _("Mobile Number"), "fieldname": "mobile_number", "fieldtype": "Data", "width": 140},
        {"label": _("Occupation"), "fieldname": "occupation", "fieldtype": "Data", "width": 150},
        {"label": _("Email Address"), "fieldname": "email_address", "fieldtype": "Data", "width": 150},
        {"label": _("CNIC Number"), "fieldname": "custom_cnic_no", "fieldtype": "Data", "width": 150}
    ]

def get_data(filters):
    query = """
        SELECT 
            g.name,
            g.guardian_name,
            g.mobile_number,
            g.occupation,
            g.email_address,
            g.custom_cnic_no,
            COUNT(DISTINCT CASE 
                WHEN sg.parent IS NOT NULL AND sg.parent != '' 
                THEN sg.parent 
                ELSE NULL 
            END) as child_count
        FROM 
            `tabGuardian` g
        LEFT JOIN 
            `tabStudent Guardian` sg ON sg.guardian = g.name
        GROUP BY 
            g.name, g.guardian_name, g.mobile_number, 
            g.occupation, g.email_address, g.custom_cnic_no
    """
    
    # Apply HAVING clause for filtering guardians with children
    if filters.get("has_child"):
        query += " HAVING COUNT(DISTINCT sg.parent) > 0"
    
    # Order by child count descending
    query += " ORDER BY child_count DESC, g.guardian_name ASC"
    
    return frappe.db.sql(query, as_dict=1)