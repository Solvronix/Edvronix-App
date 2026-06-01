// Copyright (c) 2026, Solvronix and contributors
// For license information, please see license.txt

frappe.query_reports["Journal Entry Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_start()
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_end()
        },
        {
            fieldname: "voucher_type",
            label: __("Entry Type"),
            fieldtype: "Select",
            options: "\nJournal Entry\nBank Entry\nCash Entry\nCredit Card Entry\nDebit Note\nCredit Note\nContra Entry\nExcise Entry\nWrite Off Entry\nOpening Entry\nDepreciation Entry"
        }
    ]
};
