// Copyright (c) 2026, Solvronix and contributors
// For license information, please see license.txt
frappe.query_reports["Student Strength Report"] = {
    filters: [
        {
            fieldname: "academic_year",
            label: __("Academic Year"),
            fieldtype: "Link",
            options: "Academic Year"
        },
        {
            fieldname: "program",
            label: __("Program"),
            fieldtype: "Link",
            options: "Program"
        },
    ]
};
