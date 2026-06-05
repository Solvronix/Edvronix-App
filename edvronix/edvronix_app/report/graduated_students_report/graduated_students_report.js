// Copyright (c) 2026, Solvronix and contributors
// For license information, please see license.txt

frappe.query_reports["Graduated Students Report"] = {
	filters: [
		{
			fieldname: "academic_year",
			label: __("Academic Year"),
			fieldtype: "Link",
			options: "Academic Year",
		},
		{
			fieldname: "program",
			label: __("Program"),
			fieldtype: "Link",
			options: "Program",
		},
		{
			fieldname: "from_date",
			label: __("Graduation Date From"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("Graduation Date To"),
			fieldtype: "Date",
		},
	],
};
