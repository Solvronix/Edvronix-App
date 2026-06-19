// Copyright (c) 2026, Solvronix and contributors
// For license information, please see license.txt

frappe.query_reports["Monthly Outstanding or Dues Report"] = {
    filters: [
        {
            fieldname: "month",
            label: __("Month"),
            fieldtype: "Select",
            options: [
                { label: "All", value: "" },
                { label: "January", value: "1" },
                { label: "February", value: "2" },
                { label: "March", value: "3" },
                { label: "April", value: "4" },
                { label: "May", value: "5" },
                { label: "June", value: "6" },
                { label: "July", value: "7" },
                { label: "August", value: "8" },
                { label: "September", value: "9" },
                { label: "October", value: "10" },
                { label: "November", value: "11" },
                { label: "December", value: "12" }
            ]
        },
    
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
        {
            fieldname: "student",
            label: __("Student"),
            fieldtype: "Link",
            options: "Student"
        },
        {
            fieldname: "only_outstanding",
            label: __("Only Outstanding"),
            fieldtype: "Check",
            default: 1
        },
        {
            fieldname: "show_defaulters",
            label: __("Show Defaulters"),
            fieldtype: "Check",
            default: 0
        },
        {
            fieldname: "partial_paid",
            label: __("Partial Paid"),
            fieldtype: "Check",
        },
        {
            fieldname: "show_prior_outstanding",
            label: __("Show Prior Outstanding"),
            fieldtype: "Check",
            default: 0
        }
    ]
};
