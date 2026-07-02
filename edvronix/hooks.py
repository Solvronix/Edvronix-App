app_name = "edvronix"
app_title = "Edvronix"
app_publisher = "Solvronix"
app_description = "School Management System by Solvronix"
app_email = "info@solvronix.com"
app_license = "mit"

# ── Required apps (checked by bench install-app) ──────────────────────────────
# edvronix relies on doctypes and APIs from ERPNext (Sales Invoice, etc.)
# and Education (Student, Guardian, Program Enrollment, etc.).
required_apps = ["erpnext", "education"]

# ── Desk assets (loaded on every desk page) ───────────────────────────────────
app_include_css = ["/assets/edvronix/css/edvronix_desk.css"]
app_include_js  = ["/assets/edvronix/js/edvronix_desk.js"]

# ── Install / migrate / uninstall lifecycle hooks ─────────────────────────────
# after_install : add the "Edvronix App" tile to existing users' Desktop Layouts
# after_migrate : fix workspace child tables + number card filter, then self-heal
#                 the desk tile so it re-appears if a layout froze it out
after_install    = "edvronix.install.after_install"
after_migrate    = [
    "edvronix.patches.fix_workspace_number_cards.execute",
    "edvronix.install.ensure_desktop_layout_entries",
]
before_uninstall = "edvronix.install.before_uninstall"

# ── Document events ───────────────────────────────────────────────────────────
doc_events = {
    "Sales Invoice": {
        "before_insert": "edvronix.events.override_invoice_rates"
    },
    "Student Applicant": {
        "before_insert": "edvronix.events.generate_student_email",
    },
    "Student": {
        "validate": "edvronix.events.prevent_enabling_graduated_student"
    },
    "Workspace": {
        "on_update": "edvronix.workspace_utils.export_workspace_on_save"
    }
}
override_doctype_class = {
	"Fee Schedule": "edvronix.fee_schedule_override.CustomFeeSchedule"
}
# ── Method overrides ──────────────────────────────────────────────────────────
override_whitelisted_methods = {
    "frappe.desk.doctype.workspace.workspace.save_page": "edvronix.workspace_utils.save_page"
}

# ── Fixtures (exported/imported on bench migrate) ─────────────────────────────
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            ["name", "in", [
                "Program Enrollment-custom_monthy_fee_",
                "Program Enrollment-custom_tuition_fee",
                "Student Applicant-custom_cnic_no",
                "Student Applicant-workflow_state",
                "Student Applicant-custom_remarks",
                "Student-custom_bform_image",
                "Guardian-custom_cnic_no",
                "Guardian-custom_cnic_img",
                "Sales Order-column_break_ejcc",
                "Sales Order-fee_schedule",
                "Sales Order-student",
                "Sales Order-student_info_section",
                "Sales Invoice-column_break_ejcc",
                "Sales Invoice-fee_schedule",
                "Sales Invoice-student",
                "Sales Invoice-student_info_section"
            ]]
        ]
    },
    {"dt": "Workspace",         "filters": [["name", "=", "Edvronix App"]]},
    {"dt": "Workspace Sidebar", "filters": [["name", "=", "Edvronix App"]]},
    {"dt": "Desktop Icon",      "filters": [["name", "=", "Edvronix App"]]},
    {"dt": "Number Card",    "filters": [["module", "=", "Edvronix App"]]},
    # Dashboard Charts: Frappe 16 blocks re-importing standard charts.
    # They are created on first install via the module-level JSON files.
    {"dt": "Dashboard",      "filters": [["module", "=", "Edvronix App"]]},
    {
        "dt": "Property Setter",
        "filters": [
            ["doc_type", "=", "Student Applicant"],
            ["field_name", "=", "student_email_id"]
        ]
    },
    {
        "dt": "Client Script",
        "filters": [["name", "in", [
            "edvronix-student-applicant-email-readonly",
            "edvronix-student-list-status",
            "edvronix-student-graduate-button",
            "edvronix-exam-setup-progress",
            "edvronix-fee-schedule-precheck"
        ]]]
    },
]
