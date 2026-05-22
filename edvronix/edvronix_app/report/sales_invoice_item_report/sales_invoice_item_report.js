// Copyright (c) 2026, Dynovative and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Invoice Item Report"] = {
	"filters": [
    {
        "fieldname": "academic_year",
        "label": "Academic Year",
        "fieldtype": "Link",
        "options": "Academic Year",
        "reqd": 0
    },
    {
        "fieldname": "month",
        "label": "Month",
        "fieldtype": "Select",
        "options": "\nJanuary\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember",
        "reqd": 0
    },
    {
        "fieldname": "item",
        "label": "Item",
        "fieldtype": "Link",
        "options": "Item",
        "reqd": 0
    },
    {
        "fieldname": "unpaid_only",
        "label": "Unpaid Only",
        "fieldtype": "Check",
        "default": 0,
        onchange: function() {
            if (frappe.query_report.get_filter_value('unpaid_only'))
                frappe.query_report.set_filter_value('paid_only', 0);
        }
    },
    {
        "fieldname": "paid_only",
        "label": "Paid Only",
        "fieldtype": "Check",
        "default": 0,
        onchange: function() {
            if (frappe.query_report.get_filter_value('paid_only'))
                frappe.query_report.set_filter_value('unpaid_only', 0);
        }
    },
    {
        "fieldname": "no_annual_fund",
        "label": "Students Missing Annual Fund",
        "fieldtype": "Check",
        "default": 0,
        onchange: function() {
            if (frappe.query_report.get_filter_value('no_annual_fund')) {
                frappe.query_report.set_filter_value('unpaid_only', 0);
                frappe.query_report.set_filter_value('paid_only', 0);
                frappe.query_report.set_filter_value('item', '');
            }
        }
    }
]
};
