# Copyright (c) 2026, Dynovative and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    summary = get_report_summary(data)
    return columns, data, None, chart, summary


def get_columns():
    return [
        {
            "label": _("Student ID"),
            "fieldname": "student",
            "fieldtype": "Link",
            "options": "Student",
            "width": 140
        },
        {
            "label": _("Student Name"),
            "fieldname": "student_name",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": _("Gender"),
            "fieldname": "gender",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Defaulter Date"),
            "fieldname": "defaulter_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": _("Reason"),
            "fieldname": "reason",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": _("Mobile Number"),
            "fieldname": "mobile",
            "fieldtype": "Data",
            "width": 140
        },
        {
            "label": _("Last Modified"),
            "fieldname": "modified",
            "fieldtype": "Datetime",
            "width": 160
        }
    ]


def get_data(filters):
    conditions = " WHERE enabled = 0 "

    if filters and filters.get("from_date"):
        conditions += " AND modified >= %(from_date)s "

    if filters and filters.get("to_date"):
        conditions += " AND modified <= %(to_date)s "

    data = frappe.db.sql(f"""
        SELECT
            name as student,
            student_name,
            gender,
            enabled,
            date_of_leaving as defaulter_date,
            reason_for_leaving as reason,
            student_mobile_number as mobile,
            modified
        FROM
            `tabStudent`
        {conditions}
        ORDER BY
            modified DESC
    """, filters, as_dict=1)

    # Convert enabled to readable status
    for d in data:
        d["status"] = "Defaulter"

    return data


def get_chart_data(data):
    return {
        "data": {
            "labels": ["Defaulter Students"],
            "datasets": [
                {
                    "name": "Total",
                    "values": [len(data)]
                }
            ]
        },
        "type": "bar",
        "colors": ["#ff4d4f"]
    }


def get_report_summary(data):
    return [
        {
            "value": len(data),
            "indicator": "Red",
            "label": "Total Defaulter Students",
            "datatype": "Int"
        }
    ]
