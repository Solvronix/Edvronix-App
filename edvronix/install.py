"""
Edvronix install/uninstall hooks.

Keeps the "Edvronix App" desk tile in sync with the app's lifecycle:
  • after_install  → add the tile to every existing user's saved Desktop Layout
  • after_migrate  → self-heal (re-add the tile if it went missing)
  • before_uninstall → remove every Edvronix desk artefact cleanly
"""
import frappe

_APP       = "edvronix"
_WORKSPACE = "Edvronix App"


# ── Install / self-heal ───────────────────────────────────────────────────────

def after_install():
    """Runs after `bench install-app edvronix` — surface the tile for existing users."""
    ensure_desktop_layout_entries()


def ensure_desktop_layout_entries():
    """
    Add the Edvronix App tile to every user's *saved* Desktop Layout.

    Users without a saved layout render the server default, which already
    includes the Desktop Icon — so they need no patching. This only fixes users
    (typically the Administrator) whose layout was saved before Edvronix existed
    and therefore froze a snapshot without the tile.

    Note: on `bench install-app`, this runs (via after_install) *before* fixtures
    are synced, so the Desktop Icon record may not exist yet. The layout entry is
    self-contained, so we build it from known defaults and don't require the icon
    to exist — the tile resolves correctly once fixtures finish importing.

    Idempotent: skips any layout that already contains the tile.
    """
    entry = _layout_entry()
    layouts = frappe.db.get_all("Desktop Layout", pluck="name")

    for dl_name in layouts:
        try:
            doc = frappe.get_doc("Desktop Layout", dl_name)
            layout = frappe.parse_json(doc.layout or "[]")
            if any(item.get("name") == _WORKSPACE for item in layout):
                continue
            layout.append(dict(entry))
            doc.layout = frappe.as_json(layout)
            doc.flags.ignore_permissions = True
            doc.save()
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Edvronix: ensure layout entry")

    frappe.db.commit()
    _clear_desk_caches()


def _layout_entry():
    """
    Build a Desktop Layout tile entry for the Edvronix App.

    Uses known-good defaults so it works even before the Desktop Icon fixture is
    imported (after_install runs first). If the Desktop Icon already exists, its
    values enrich the entry.
    """
    icon = frappe.db.get_value(
        "Desktop Icon",
        _WORKSPACE,
        ["icon_type", "link_type", "icon", "bg_color", "standard", "app"],
        as_dict=True,
    ) or {}
    standard = icon.get("standard")
    return {
        "app": icon.get("app"),
        "bg_color": icon.get("bg_color") or "gray",
        "child_icons": [],
        "hidden": 0,
        "icon": icon.get("icon"),
        "icon_image": None,
        "icon_type": icon.get("icon_type") or "Link",
        "idx": 0,
        "label": _WORKSPACE,
        "link": None,
        "link_to": _WORKSPACE,
        "link_type": icon.get("link_type") or "Workspace Sidebar",
        "logo_url": None,
        "name": _WORKSPACE,
        "parent_icon": None,
        "restrict_removal": 0,
        "standard": 1 if standard is None else standard,
    }


# ── Uninstall ──────────────────────────────────────────────────────────────────

def before_uninstall():
    """Runs before `bench uninstall-app edvronix` — removes all Edvronix desk entries."""
    _teardown()


def _teardown():
    """Remove every Edvronix artefact so nothing lingers after uninstall."""

    # 1. Remove the desk tile from every user's Desktop Layout
    layouts = frappe.db.get_all("Desktop Layout", pluck="name")
    for dl_name in layouts:
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

    # 2. Delete every record this app ships as a fixture (Client Scripts, Custom
    #    Fields, Property Setters, Number Cards, Dashboards, Workspace, Desktop
    #    Icon, …). These carry no reliable module link, so Frappe's own uninstall
    #    leaves them behind — we remove them explicitly, driven by the fixtures
    #    hook so this stays in sync automatically as fixtures are added/removed.
    _delete_app_fixtures()

    # 3. Safety net: delete any orphaned workspace child rows
    for table in ("tabWorkspace Shortcut", "tabWorkspace Link",
                  "tabWorkspace Number Card", "tabWorkspace Sidebar Item"):
        frappe.db.sql(f"DELETE FROM `{table}` WHERE parent=%s", _WORKSPACE)

    frappe.db.commit()

    _clear_desk_caches()


def _delete_app_fixtures():
    """Delete all records matching this app's `fixtures` hook definitions."""
    from edvronix import hooks as _hooks

    for fixture in getattr(_hooks, "fixtures", []):
        # Support both the {"dt": ...} and {"doctype": ...} fixture forms; a
        # string fixture ("Some DocType") would mean "all records" — skip those
        # for safety since we never want to blanket-delete a shared doctype.
        if isinstance(fixture, str):
            continue
        doctype = fixture.get("dt") or fixture.get("doctype")
        filters = fixture.get("filters")
        if not doctype or not filters:
            continue

        try:
            names = frappe.get_all(doctype, filters=filters, pluck="name")
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Edvronix: query fixtures {doctype}")
            continue

        for name in names:
            try:
                frappe.delete_doc(
                    doctype, name,
                    force=True, ignore_permissions=True, ignore_missing=True,
                )
            except Exception:
                frappe.log_error(frappe.get_traceback(), f"Edvronix: delete {doctype} {name}")


# ── Shared helpers ──────────────────────────────────────────────────────────────

def _clear_desk_caches(users=None):
    """
    Bust the caches that back the desk grid so it reflects install/uninstall
    immediately (after a page reload) without a manual `bench clear-cache`.

    The Frappe Desktop reads its tiles from the `desktop_icons` cache (see
    frappe.desk.doctype.desktop_icon.get_desktop_icons) and the sidebar/boot from
    `bootinfo`. Both are hash caches keyed by user; we delete the whole keys so
    every user regenerates fresh, mirroring frappe's own clear_desktop_icons_cache.
    """
    for key in ("desktop_icons", "bootinfo"):
        try:
            frappe.cache.delete_key(key)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Edvronix: clear {key} cache")
