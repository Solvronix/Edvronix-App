# Copyright (c) 2026, Solvronix and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, getdate


@frappe.whitelist()
def get_dashboard_stats():
	"""Returns all KPI stats for the Edvronix dashboard in one API call."""
	today = getdate()

	stats = {}

	# Total active students
	stats["total_students"] = frappe.db.count("Student", filters={"enabled": 1})

	# Fee collected this month (fully paid invoices)
	fee_result = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(grand_total), 0)
		FROM `tabSales Invoice`
		WHERE docstatus = 1
		  AND outstanding_amount = 0
		  AND MONTH(posting_date) = %s
		  AND YEAR(posting_date) = %s
		""",
		(today.month, today.year),
	)
	stats["fee_collected"] = flt(fee_result[0][0])

	# Total outstanding fees
	outstanding_result = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(outstanding_amount), 0)
		FROM `tabSales Invoice`
		WHERE docstatus = 1
		  AND outstanding_amount > 0
		""",
	)
	stats["outstanding"] = flt(outstanding_result[0][0])

	# Total active staff
	stats["total_staff"] = frappe.db.count("Employee", filters={"status": "Active"})

	# Students present today
	stats["present_today"] = frappe.db.count(
		"Student Attendance", filters={"date": today, "status": "Present"}
	)

	# Total registered guardians
	stats["total_guardians"] = frappe.db.count("Guardian")

	return stats
