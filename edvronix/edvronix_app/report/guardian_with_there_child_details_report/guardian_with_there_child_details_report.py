import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data()

    total_guardians = len({row["guardian_id"] for row in data})
    total_students = sum(1 for row in data if row.get("student"))

    report_summary = [
        {"label": _("Total Guardians"), "value": total_guardians, "datatype": "Int", "indicator": "Blue"},
        {"label": _("Total Students Linked"), "value": total_students, "datatype": "Int", "indicator": "Green"},
    ]
    return columns, data, None, None, report_summary


def get_data():
    # Single query: Guardian → Student Guardian → Student → latest Program Enrollment.
    # Uses a correlated subquery to pick only the most recent submitted enrollment per student.
    rows = frappe.db.sql("""
        SELECT
            g.name                  AS guardian_id,
            g.guardian_name,
            g.mobile_number,
            s.name                  AS student,
            s.student_name,
            pe.program,
            pe.student_category,
            pe.custom_tuition_fee
        FROM `tabGuardian` g
        LEFT JOIN `tabStudent Guardian` sg
            ON sg.guardian = g.name AND sg.parenttype = 'Student'
        LEFT JOIN `tabStudent` s
            ON s.name = sg.parent
        LEFT JOIN `tabProgram Enrollment` pe
            ON pe.student = s.name
            AND pe.docstatus = 1
            AND pe.creation = (
                SELECT MAX(pe2.creation)
                FROM `tabProgram Enrollment` pe2
                WHERE pe2.student = s.name AND pe2.docstatus = 1
            )
        WHERE g.docstatus < 2
        ORDER BY g.guardian_name, s.student_name
    """, as_dict=True)

    # Collapse multiple student rows per guardian into one display row
    seen = {}
    result = []
    for row in rows:
        gid = row["guardian_id"]
        if gid not in seen:
            seen[gid] = {
                "guardian_id": gid,
                "guardian_name": row["guardian_name"],
                "mobile_number": row["mobile_number"],
                "_details": [],
                "_ids": [],
            }
            result.append(seen[gid])
        if row.get("student"):
            detail = row["student_name"] or row["student"]
            parts = [p for p in [row.get("program"), row.get("student_category"), row.get("custom_tuition_fee")] if p]
            if parts:
                detail += " (" + ", ".join(str(p) for p in parts) + ")"
            seen[gid]["_details"].append(detail)
            seen[gid]["_ids"].append(row["student"])

    for entry in result:
        entry["student"] = ", ".join(entry.pop("_ids")) or None
        entry["student_name"] = ", ".join(entry.pop("_details")) or None

    return result


def get_columns():
    return [
        {"label": _("Guardian ID"), "fieldname": "guardian_id", "fieldtype": "Link", "options": "Guardian", "width": 200},
        {"label": _("Guardian Name"), "fieldname": "guardian_name", "fieldtype": "Data", "width": 180},
        {"label": _("Mobile Number"), "fieldname": "mobile_number", "fieldtype": "Data", "width": 135},
        {"label": _("Student IDs"), "fieldname": "student", "fieldtype": "Small Text", "width": 200},
        {"label": _("Student Details"), "fieldname": "student_name", "fieldtype": "Small Text", "width": 600},
    ]
