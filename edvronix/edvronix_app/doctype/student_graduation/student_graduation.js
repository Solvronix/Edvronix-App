// Copyright (c) 2026, Solvronix and contributors
// For license information, please see license.txt

frappe.ui.form.on("Student Graduation", {
	refresh: function(frm) {
		// Show Fetch Students button only in Draft state
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Fetch Students"), function() {
				if (!frm.doc.academic_year || !frm.doc.program) {
					frappe.msgprint({
						message: __("Please select Academic Year and Program first."),
						indicator: "orange"
					});
					return;
				}

				frappe.call({
					method: "edvronix.edvronix_app.doctype.student_graduation.student_graduation.fetch_students",
					args: {
						academic_year: frm.doc.academic_year,
						program: frm.doc.program
					},
					freeze: true,
					freeze_message: __("Fetching students..."),
					callback: function(r) {
						if (!r.message || r.message.length === 0) {
							frappe.msgprint({
								message: __("No active students found for the selected Program and Academic Year."),
								indicator: "orange"
							});
							return;
						}

						// Clear existing rows and populate with fetched students
						frm.clear_table("students");
						r.message.forEach(function(s) {
							let row = frm.add_child("students");
							row.student = s.student;
							row.student_name = s.student_name;
							row.certificate_number = s.certificate_number;
							row.is_graduated = s.is_graduated;
						});
						frm.refresh_field("students");
						frm.set_value("total_students", r.message.length);
						frappe.show_alert({
							message: __("{0} student(s) loaded. Add certificate numbers if needed, then Submit.", [r.message.length]),
							indicator: "green"
						});
					}
				});
			}, __("Actions"));
		}

		// Show graduation summary banner when submitted
		if (frm.doc.docstatus === 1) {
			frm.set_intro(
				`<b>${frm.doc.total_students || 0}</b> student(s) graduated from
				<b>${frm.doc.program}</b> — Academic Year <b>${frm.doc.academic_year}</b>
				on <b>${frappe.datetime.str_to_user(frm.doc.graduation_date)}</b>.
				<br><i>To reverse this graduation, cancel the document.</i>`,
				"green"
			);
		}
	},

	// Auto-clear students table when program or academic_year changes
	academic_year: function(frm) {
		if (frm.doc.students && frm.doc.students.length > 0) {
			frappe.confirm(
				__("Changing the Academic Year will clear the current student list. Continue?"),
				function() { frm.clear_table("students"); frm.refresh_field("students"); }
			);
		}
	},

	program: function(frm) {
		if (frm.doc.students && frm.doc.students.length > 0) {
			frappe.confirm(
				__("Changing the Program will clear the current student list. Continue?"),
				function() { frm.clear_table("students"); frm.refresh_field("students"); }
			);
		}
	}
});
