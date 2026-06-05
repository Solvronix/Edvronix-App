import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = []

    guardians = frappe.get_all(
        "Guardian",
        filters={"docstatus": ["<", 2]},
        fields=["name", "guardian_name", "mobile_number", ]
    )

    total_students_count = 0

    for g in guardians:
        guardian_doc = frappe.get_doc("Guardian", g.name)
        
        student_ids = []
        student_names = []

        #  FIXED + EXTENDED LOGIC
        children = guardian_doc.get("guardian_of") or guardian_doc.get("students") or []

        for row in children:
            if not row.student:
                continue

            student_ids.append(row.student)
            total_students_count += 1

            # Always get student name from Student doctype
            student_name = frappe.db.get_value(
                "Student", row.student, "student_name"
            ) or row.student

            #  Get latest Program Enrollment
            enrollment = frappe.db.get_value(
                "Program Enrollment",
                {
                    "student": row.student,
                    "docstatus": 1
                },
                ["program", "student_category", "custom_tuition_fee"],
                order_by="creation desc",
                as_dict=True
            )

            program = enrollment.program if enrollment else "N/A"
            category = enrollment.student_category if enrollment else "N/A"
            fee = enrollment.custom_tuition_fee if enrollment else "N/A"

            #  FINAL FORMAT YOU ASKED
            student_names.append(
                f"{student_name} ({program}, {category}, {fee})"
            )

        data.append({
            "guardian_id": g.name,
            "guardian_name": g.guardian_name,
            "mobile_number": g.mobile_number,
            "student": ", ".join(student_ids) if student_ids else None,
            "student_name": ", ".join(student_names) if student_names else None
        })

    report_summary = [
        {
            "label": _("Total Guardians"),
            "value": len(guardians),
            "datatype": "Int",
            "indicator": "Blue"
        },
        {
            "label": _("Total Students Linked"),
            "value": total_students_count,
            "datatype": "Int",
            "indicator": "Green"
        }
    ]

    return columns, data, None, None, report_summary


def get_columns():
    return [
        {"label": _("Guardian ID"), "fieldname": "guardian_id", "fieldtype": "Link", "options": "Guardian", "width": 200},
        {"label": _("Guardian Name"), "fieldname": "guardian_name", "fieldtype": "Data", "width": 180},
        {"label": _("Mobile Number"), "fieldname": "mobile_number", "fieldtype": "Data", "width": 135},
        {"label": _("Student IDs"), "fieldname": "student", "fieldtype": "Small Text", "width": 200},
        {"label": _("Student Details"), "fieldname": "student_name", "fieldtype": "Small Text", "width": 600}
    ]
