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
	return {"name": name, "public": public, "label": doc.label}


def export_workspace_on_save(doc, method=None):
	"""Write workspace JSON back to the app file so bench migrate never overwrites UI edits."""
	if doc.public and doc.module and doc.app == "edvronix":
		try:
			from frappe.modules.export_file import export_to_files
			export_to_files(
				record_list=[["Workspace", doc.name]],
				record_module=doc.module,
			)
		except Exception:
			pass
