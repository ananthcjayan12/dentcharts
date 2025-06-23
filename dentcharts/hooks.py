app_name = "dentcharts"
app_title = "Dentcharts"
app_publisher = "ananthuuu"
app_description = "Complete Dental ERP and HMS"
app_email = "ananthcjayan@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Workspaces
# ----------

workspaces = [
	{
		"name": "Dentcharts",
		"title": "Dentcharts",
		"icon": "fa fa-tooth",
		"category": "Modules",
		"is_standard": 1,
		"module": "Dentcharts",
		"color": "#0891b2",
		"shortcuts": [
			{
				"type": "DocType",
				"name": "Dental Patient",
				"label": "Dental Patient",
				"icon": "fa fa-user"
			},
			{
				"type": "DocType", 
				"name": "Dental Practitioner",
				"label": "Dental Practitioner",
				"icon": "fa fa-user-md"
			},
			{
				"type": "DocType",
				"name": "Dental Clinic", 
				"label": "Dental Clinic",
				"icon": "fa fa-hospital"
			},
			{
				"type": "DocType",
				"name": "Dental Appointment",
				"label": "Dental Appointment", 
				"icon": "fa fa-calendar"
			},
			{
				"type": "DocType",
				"name": "Dental Chart",
				"label": "Dental Chart",
				"icon": "fa fa-tooth"
			},
			{
				"type": "DocType",
				"name": "Treatment Plan",
				"label": "Treatment Plan",
				"icon": "fa fa-list-alt"
			},
			{
				"type": "DocType",
				"name": "Invoice",
				"label": "Invoice",
				"icon": "fa fa-file-invoice"
			},
			{
				"type": "DocType",
				"name": "Payment Entry",
				"label": "Payment Entry", 
				"icon": "fa fa-credit-card"
			}
		],
		"cards": [
			{
				"name": "Patient Management",
				"items": [
					{
						"type": "DocType",
						"name": "Dental Patient",
						"label": "Dental Patient"
					},
					{
						"type": "DocType",
						"name": "Dental Chart", 
						"label": "Dental Chart"
					}
				]
			},
			{
				"name": "Appointments",
				"items": [
					{
						"type": "DocType",
						"name": "Dental Appointment",
						"label": "Dental Appointment"
					},
					{
						"type": "DocType",
						"name": "Treatment Plan",
						"label": "Treatment Plan"  
					}
				]
			},
			{
				"name": "Masters",
				"items": [
					{
						"type": "DocType",
						"name": "Dental Clinic",
						"label": "Dental Clinic"
					},
					{
						"type": "DocType", 
						"name": "Dental Practitioner",
						"label": "Dental Practitioner"
					},
					{
						"type": "DocType",
						"name": "Dental Procedure Master",
						"label": "Dental Procedure Master"
					},
					{
						"type": "DocType",
						"name": "Dental Condition Master", 
						"label": "Dental Condition Master"
					},
					{
						"type": "DocType",
						"name": "Tooth Master",
						"label": "Tooth Master"
					}
				]
			},
			{
				"name": "Billing",
				"items": [
					{
						"type": "DocType",
						"name": "Invoice",
						"label": "Invoice"
					},
					{
						"type": "DocType",
						"name": "Payment Entry", 
						"label": "Payment Entry"
					},
					{
						"type": "DocType",
						"name": "Insurance Claim",
						"label": "Insurance Claim"
					}
				]
			},
			{
				"name": "Reports",
				"items": [
					{
						"type": "Report",
						"name": "Patient Demographics",
						"label": "Patient Demographics"
					},
					{
						"type": "Report", 
						"name": "Revenue Analysis",
						"label": "Revenue Analysis"
					},
					{
						"type": "Report",
						"name": "Treatment Success Metrics",
						"label": "Treatment Success Metrics"
					}
				]
			}
		]
	}
]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "dentcharts",
# 		"logo": "/assets/dentcharts/logo.png",
# 		"title": "Dentcharts",
# 		"route": "/dentcharts",
# 		"has_permission": "dentcharts.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/dentcharts/css/dentcharts.css"
# app_include_js = "/assets/dentcharts/js/dentcharts.js"

# include js, css files in header of web template
# web_include_css = "/assets/dentcharts/css/dentcharts.css"
# web_include_js = "/assets/dentcharts/js/dentcharts.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "dentcharts/public/scss/website"

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
# app_include_icons = "dentcharts/public/icons.svg"

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
# 	"methods": "dentcharts.utils.jinja_methods",
# 	"filters": "dentcharts.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "dentcharts.install.before_install"
# after_install = "dentcharts.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "dentcharts.uninstall.before_uninstall"
# after_uninstall = "dentcharts.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "dentcharts.utils.before_app_install"
# after_app_install = "dentcharts.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "dentcharts.utils.before_app_uninstall"
# after_app_uninstall = "dentcharts.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "dentcharts.notifications.get_notification_config"

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

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"dentcharts.tasks.all"
# 	],
# 	"daily": [
# 		"dentcharts.tasks.daily"
# 	],
# 	"hourly": [
# 		"dentcharts.tasks.hourly"
# 	],
# 	"weekly": [
# 		"dentcharts.tasks.weekly"
# 	],
# 	"monthly": [
# 		"dentcharts.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "dentcharts.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "dentcharts.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "dentcharts.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["dentcharts.utils.before_request"]
# after_request = ["dentcharts.utils.after_request"]

# Job Events
# ----------
# before_job = ["dentcharts.utils.before_job"]
# after_job = ["dentcharts.utils.after_job"]

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
# 	"dentcharts.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

