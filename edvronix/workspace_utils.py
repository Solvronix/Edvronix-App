import frappe
from frappe.desk.desktop import save_new_widget
from frappe.desk.doctype.workspace.workspace import is_workspace_manager


@frappe.whitelist()
def save_page(name, public, new_widgets, blocks):
	public = frappe.parse_json(public)
	doc = frappe.get_doc("Workspace", name)

	# Frappe's original condition uses `and`, which means public workspaces
	# (for_user = "") can never be saved via the visual editor. Changed to `or`
	# so Workspace Managers can save public workspaces directly.
	if not (is_workspace_manager() or doc.for_user == frappe.session.user):
		return

	if not doc.type:
		doc.type = "Workspace"

	doc.content = blocks
	save_new_widget(doc, name, blocks, new_widgets)

	# Frappe's save_new_widget rebuilds the number_cards/charts child tables
	# but leaves number_card_name / chart_name as NULL (Frappe bug).
	# Fix them immediately after every save so the workspace always renders.
	if name == "Edvronix App":
		_fix_edvronix_workspace_children()

	return {"name": name, "public": public, "label": doc.label}


def export_workspace_on_save(doc, method=None):
	"""
	Write workspace JSON back to the app file when saved from the UI.
	Skipped during migrate / fixture-sync / install to prevent NULL child table
	values from overwriting the fixture file in a feedback loop.
	Also fixes child table NULL values before exporting so the fixture stays clean.
	"""
	if frappe.flags.in_migrate or frappe.flags.in_import or frappe.flags.in_install:
		return

	if doc.public and doc.module and doc.app == "edvronix":
		if doc.name == "Edvronix App":
			_fix_edvronix_workspace_children()

		try:
			from frappe.modules.export_file import export_to_files
			export_to_files(
				record_list=[["Workspace", doc.name]],
				record_module=doc.module,
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Edvronix: workspace export failed")


def _fix_edvronix_workspace_children():
	"""
	Fix NULL number_card_name / chart_name in Edvronix App workspace child tables.
	Called after every UI save because Frappe's save_new_widget resets these to NULL.
	This is the single source of truth — same logic as the after_migrate patch.
	"""
	from edvronix.patches.fix_workspace_number_cards import (
		NUMBER_CARDS,
		CHARTS,
		_fix_workspace_child_tables,
		_fix_fee_collected_filter,
		_fix_workspace_shortcut_width,
	)
	_fix_workspace_child_tables()
	_fix_fee_collected_filter()
	_fix_workspace_shortcut_width()
	frappe.db.commit()
