frappe.query_reports["Admission Summary Report"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "default": frappe.datetime.month_start()
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
            "default": frappe.datetime.month_end()
        },
        {
            "fieldname": "academic_year",
            "label": "Academic Year",
            "fieldtype": "Link",
            "options": "Academic Year"
        }
    ]
};
