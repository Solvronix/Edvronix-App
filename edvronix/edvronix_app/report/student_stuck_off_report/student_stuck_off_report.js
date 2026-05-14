// Copyright (c) 2026, Dynovative and contributors
// For license information, please see license.txt

frappe.query_reports["Student Stuck Off Report"] = {
    "filters": [
        // {
        //     "fieldname": "academic_year",
        //     "label": "Academic Year",
        //     "fieldtype": "Link",
        //     "options": "Academic Year"
        // },
        {
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date"
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date"
        }
    ]
};
