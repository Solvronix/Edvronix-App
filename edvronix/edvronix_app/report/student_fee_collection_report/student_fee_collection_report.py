# Copyright (c) 2026, Frappe Technologies Pvt. Ltd.
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": "Student",
            "fieldname": "student",
            "fieldtype": "Link",
            "options": "Student",
            "width": 160
        },
        {
            "label": "Student Name",
            "fieldname": "student_name",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": "Program",
            "fieldname": "program",
            "fieldtype": "Link",
            "options": "Program",
            "width": 140
        },
        {
            "label": "Category",
            "fieldname": "student_category",
            "fieldtype": "Link",
            "options": "Student Category",
            "width": 140
        },
        {
            "label": "Paid Amount",
            "fieldname": "paid_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": "Outstanding Amount",
            "fieldname": "outstanding_amount",
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "label": "Grand Total",
            "fieldname": "grand_total",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": "Due Date",
            "fieldname": "due_date",
            "fieldtype": "Date",
            "width": 110
        },
        {
            "label": "Sales Invoices",
            "fieldname": "sales_invoices",
            "fieldtype": "Data",
            "width": 220
        }
    ]


def get_data(filters):

    conditions = ""
    values = {}

    # Program filter
    if filters.get("program"):
        conditions += " AND pe.program = %(program)s"
        values["program"] = filters.get("program")

    # ✅ Month filter based on Due Date
    if filters.get("month"):
        conditions += " AND MONTH(si.due_date) = %(month)s"
        values["month"] = filters.get("month")

    return frappe.db.sql(
        f"""
        SELECT
            si.student,
            st.student_name,
            pe.program,
            pe.student_category,

            SUM(si.grand_total) - SUM(si.outstanding_amount) AS paid_amount,
            SUM(si.outstanding_amount) AS outstanding_amount,
            SUM(si.grand_total) AS grand_total,

            MAX(si.due_date) AS due_date,

            GROUP_CONCAT(DISTINCT si.name ORDER BY si.posting_date SEPARATOR ', ') AS sales_invoices

        FROM
            `tabSales Invoice` si

        INNER JOIN
            `tabStudent` st
            ON st.name = si.student

        LEFT JOIN
            `tabProgram Enrollment` pe
            ON pe.student = si.student
            AND pe.docstatus = 1

        WHERE
            si.docstatus = 1
            AND si.student IS NOT NULL
            AND si.due_date IS NOT NULL
            {conditions}

        GROUP BY
            si.student,
            st.student_name,
            pe.program,
            pe.student_category

        ORDER BY
            pe.program,
            st.student_name
        """,
        values,
        as_dict=True
    )
