// Copyright (c) 2026, Solvronix and contributors
// For license information, please see license.txt

frappe.query_reports["Fee Vouhcer Check Parent Wise"] = {
	   "filters": [
        {
            "fieldname": "parent",
            "label": "Parent",
            "fieldtype": "Link",
            "options": "Guardian"
        },
        {
            "fieldname": "academic_year",
            "label": "Academic Year",
            "fieldtype": "Link",
            "options": "Academic Year"
        },
        {
            "fieldname": "month",
            "label": "Month",
            "fieldtype": "Select",
            "options": [
                {"label": "","value": ""},
                {"label": "Jan","value": "1"},
                {"label": "Feb","value": "2"},
                {"label": "Mar","value": "3"},
                {"label": "Apr","value": "4"},
                {"label": "May","value": "5"},
                {"label": "Jun","value": "6"},
                {"label": "Jul","value": "7"},
                {"label": "Aug","value": "8"},
                {"label": "Sep","value": "9"},
                {"label": "Oct","value": "10"},
                {"label": "Nov","value": "11"},
                {"label": "Dec","value": "12"}
            ]
        }
    ]
};

