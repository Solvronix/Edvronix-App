app_name = "edvronix"
app_title = "Edvronix"
app_publisher = "Solvronix"
app_description = "School Management System by Solvronix"
app_email = "info@solvronix.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "edvronix",
# 		"logo": "/assets/edvronix/logo.png",
# 		"title": "Edvronix App",
# 		"route": "/edvronix",
# 		"has_permission": "edvronix.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/edvronix/css/edvronix.css"
# app_include_js = "/assets/edvronix/js/edvronix.js"

# include js, css files in header of web template
# web_include_css = "/assets/edvronix/css/edvronix.css"
# web_include_js = "/assets/edvronix/js/edvronix.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "edvronix/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "edvronix/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "edvronix.utils.jinja_methods",
# 	"filters": "edvronix.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "edvronix.install.before_install"
# after_install = "edvronix.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "edvronix.uninstall.before_uninstall"
# after_uninstall = "edvronix.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "edvronix.utils.before_app_install"
# after_app_install = "edvronix.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "edvronix.utils.before_app_uninstall"
# after_app_uninstall = "edvronix.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "edvronix.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Sales Invoice": {
        # "after_insert": "edvronix.events.override_invoice_rates",
        "before_insert": "edvronix.events.override_invoice_rates"
    },
    "Workspace": {
        "on_update": "edvronix.workspace_utils.export_workspace_on_save"
    }
}

override_whitelisted_methods = {
    "frappe.desk.doctype.workspace.workspace.save_page": "edvronix.workspace_utils.save_page"
}

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
    }
]




# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"edvronix.tasks.all"
# 	],
# 	"daily": [
# 		"edvronix.tasks.daily"
# 	],
# 	"hourly": [
# 		"edvronix.tasks.hourly"
# 	],
# 	"weekly": [
# 		"edvronix.tasks.weekly"
# 	],
# 	"monthly": [
# 		"edvronix.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "edvronix.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "edvronix.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "edvronix.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["edvronix.utils.before_request"]
# after_request = ["edvronix.utils.after_request"]

# Job Events
# ----------
# before_job = ["edvronix.utils.before_job"]
# after_job = ["edvronix.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"edvronix.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

