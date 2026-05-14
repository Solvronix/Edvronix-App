// Copyright (c) 2026, Dynovative and contributors
// For license information, please see license.txt

frappe.query_reports["Student Fee Collection Report"] = {
	"filters": [

		{
			"fieldname": "program",
			"label": "Program",
			"fieldtype": "Link",
			"options": "Program"
		},

		{
			"fieldname": "month",
			"label": "Month",
			"fieldtype": "Select",
			"options": [
				{ "value": "", "label": "" },
				{ "value": "1", "label": "January" },
				{ "value": "2", "label": "February" },
				{ "value": "3", "label": "March" },
				{ "value": "4", "label": "April" },
				{ "value": "5", "label": "May" },
				{ "value": "6", "label": "June" },
				{ "value": "7", "label": "July" },
				{ "value": "8", "label": "August" },
				{ "value": "9", "label": "September" },
				{ "value": "10", "label": "October" },
				{ "value": "11", "label": "November" },
				{ "value": "12", "label": "December" }
			]
		},

		{
			"fieldname": "year",
			"label": "Year",
			"fieldtype": "Int",
			"default": new Date().getFullYear()
		}

	]
};
