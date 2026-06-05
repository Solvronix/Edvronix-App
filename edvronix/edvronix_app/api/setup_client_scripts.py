import frappe


@frappe.whitelist()
def create_student_applicant_script():
	frappe.only_for("System Manager")
	script_content = '''frappe.ui.form.on("Student Applicant", {
    refresh: function(frm) {
        // Make Student Email readonly once it has been auto-generated
        if (frm.doc.student_email_id) {
            frm.set_df_property("student_email_id", "read_only", 1);
            frm.refresh_field("student_email_id");
        }
    }
});'''

	existing = frappe.db.get_value(
		"Client Script",
		{"dt": "Student Applicant", "enabled": 1},
		"name"
	)

	if existing:
		doc = frappe.get_doc("Client Script", existing)
		doc.script = script_content
		doc.save(ignore_permissions=True)
		return f"Updated: {existing}"
	else:
		doc = frappe.get_doc({
			"doctype": "Client Script",
			"dt": "Student Applicant",
			"enabled": 1,
			"view": "Form",
			"script": script_content,
		})
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		return f"Created: {doc.name}"
