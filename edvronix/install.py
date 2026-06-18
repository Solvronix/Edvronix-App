"""
Edvronix install/uninstall hooks.
Ensures workspace entries are cleanly removed when the app is uninstalled.
"""
import frappe

_APP       = "edvronix"
_WORKSPACE = "Edvronix App"


def before_uninstall():
    """Runs before `bench uninstall-app edvronix` — removes all Edvronix desk entries."""
    _teardown()


def _teardown():
    """Remove every Edvronix desk artefact so nothing lingers after uninstall."""

    # Remove the tile from every user's Desktop Layout
    users = frappe.db.get_all(
        "User",
        filters={"enabled": 1, "name": ["!=", "Guest"]},
        pluck="name",
    )
    for user in users:
        dl_name = frappe.db.get_value("Desktop Layout", {"user": user}, "name")
        if not dl_name:
            continue
        try:
            doc = frappe.get_doc("Desktop Layout", dl_name)
            layout = frappe.parse_json(doc.layout or "[]")
            new_layout = [item for item in layout if item.get("name") != _WORKSPACE]
            if len(new_layout) != len(layout):
                doc.layout = frappe.as_json(new_layout)
                doc.flags.ignore_permissions = True
                doc.save()
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Edvronix: teardown layout")

    # Delete Desktop Icon, Workspace Sidebar, Workspace
    for doctype in ("Desktop Icon", "Workspace Sidebar", "Workspace"):
        if frappe.db.exists(doctype, _WORKSPACE):
            frappe.delete_doc(doctype, _WORKSPACE, force=True, ignore_permissions=True)

    # Safety net: delete any orphaned child rows
    for table in ("tabWorkspace Shortcut", "tabWorkspace Link",
                  "tabWorkspace Number Card", "tabWorkspace Sidebar Item"):
        frappe.db.sql(f"DELETE FROM `{table}` WHERE parent=%s", _WORKSPACE)

    frappe.db.commit()

    # Bust boot cache so users stop seeing the tile immediately
    try:
        import redis as _redis
        r = _redis.Redis.from_url(frappe.conf.redis_cache)
        for user in users:
            r.hdel("bootinfo", user)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Edvronix: clear bootinfo cache")
