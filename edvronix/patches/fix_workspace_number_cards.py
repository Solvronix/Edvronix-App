"""
Runs after every bench migrate AND after every workspace UI save (via workspace_utils.py).

Fixes recurring issues caused by Frappe's fixture import / save_new_widget:
1. Workspace Number Card / Chart child rows get NULL names or deleted entirely.
2. "Fee Collected This Month" number card filter reverts to unsupported "in this month".
3. Workspace shortcut col values revert to 2 (narrow) instead of 4.
"""
import json

import frappe

NUMBER_CARDS = [
	"Total Students",
	"Fee Collected This Month",
	"Outstanding Fees",
	"Total Staff",
	"Present Today",
	"Registered Guardians",
]

CHARTS = [
	"Monthly Fee Collection",
	"Fee Collection Status",
	"Students by Program",
]

CORRECT_FEE_FILTER = json.dumps([
	["Sales Invoice", "docstatus", "=", 1],
	["Sales Invoice", "outstanding_amount", "=", 0],
	["Sales Invoice", "posting_date", "Timespan", "this month"],
])

SHORTCUTS_COL4 = [
	"Student",
	"Sales Invoice",
	"Print Bulk Voucher",
	"Student Attendance",
	"Edvronix Settings",
	"Guardian",
]


def execute():
	_fix_workspace_child_tables()
	_fix_fee_collected_filter()
	_fix_workspace_shortcut_width()
	frappe.db.commit()


def _fix_workspace_child_tables():
	"""
	Ensure number_card_name / chart_name rows exist and are correct.
	Handles both cases: rows with NULL names, and rows missing entirely.
	"""
	if not frappe.db.exists("Workspace", "Edvronix App"):
		return

	# ── Number Cards ──────────────────────────────────────────────────────────
	existing_cards = frappe.db.get_all(
		"Workspace Number Card",
		filters={"parent": "Edvronix App"},
		fields=["name", "idx", "number_card_name"],
		order_by="idx asc",
	)

	if not existing_cards:
		# No rows at all — insert fresh rows
		for i, card_name in enumerate(NUMBER_CARDS):
			frappe.db.sql(
				"""INSERT INTO `tabWorkspace Number Card`
				   (name, parent, parenttype, parentfield, idx, number_card_name, creation, modified, modified_by, owner, docstatus)
				   VALUES (%s, 'Edvronix App', 'Workspace', 'number_cards', %s, %s, NOW(), NOW(), 'Administrator', 'Administrator', 0)""",
				(frappe.generate_hash(length=10), i + 1, card_name),
			)
	else:
		# Rows exist — fix any that have NULL/empty names
		for i, row in enumerate(existing_cards):
			if not row.get("number_card_name") and i < len(NUMBER_CARDS):
				frappe.db.set_value(
					"Workspace Number Card", row["name"], "number_card_name", NUMBER_CARDS[i]
				)

	# ── Charts ────────────────────────────────────────────────────────────────
	existing_charts = frappe.db.get_all(
		"Workspace Chart",
		filters={"parent": "Edvronix App"},
		fields=["name", "idx", "chart_name"],
		order_by="idx asc",
	)

	if not existing_charts:
		# No rows at all — insert fresh rows
		for i, chart_name in enumerate(CHARTS):
			frappe.db.sql(
				"""INSERT INTO `tabWorkspace Chart`
				   (name, parent, parenttype, parentfield, idx, chart_name, creation, modified, modified_by, owner, docstatus)
				   VALUES (%s, 'Edvronix App', 'Workspace', 'charts', %s, %s, NOW(), NOW(), 'Administrator', 'Administrator', 0)""",
				(frappe.generate_hash(length=10), i + 1, chart_name),
			)
	else:
		for i, row in enumerate(existing_charts):
			if not row.get("chart_name") and i < len(CHARTS):
				frappe.db.set_value(
					"Workspace Chart", row["name"], "chart_name", CHARTS[i]
				)


def _fix_fee_collected_filter():
	"""Ensure 'Fee Collected This Month' uses Timespan operator (not 'in this month')."""
	if not frappe.db.exists("Number Card", "Fee Collected This Month"):
		return

	current = frappe.db.get_value("Number Card", "Fee Collected This Month", "filters_json")
	if current and "in this month" in current:
		frappe.db.set_value(
			"Number Card", "Fee Collected This Month", "filters_json", CORRECT_FEE_FILTER
		)


def _fix_workspace_shortcut_width():
	"""Ensure shortcuts use col:4 so full names are visible (not truncated 'Stud...')."""
	if not frappe.db.exists("Workspace", "Edvronix App"):
		return

	content_raw = frappe.db.get_value("Workspace", "Edvronix App", "content")
	if not content_raw:
		return

	try:
		content = json.loads(content_raw)
	except (ValueError, TypeError):
		return

	changed = False
	target_names = set(SHORTCUTS_COL4)
	for block in content:
		if not isinstance(block, dict):
			continue
		for item in block.get("items", []):
			if isinstance(item, dict) and item.get("shortcut_name") in target_names:
				if item.get("col") != 4:
					item["col"] = 4
					changed = True

	if changed:
		frappe.db.set_value("Workspace", "Edvronix App", "content", json.dumps(content))
