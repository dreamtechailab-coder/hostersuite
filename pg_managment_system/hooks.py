app_name = "pg_managment_system"
app_title = "Pg Managment System"
app_publisher = "Maharajan"
app_description = "PG Management"
app_email = "vijaymaharajan38@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "pg_managment_system",
# 		"logo": "/assets/pg_managment_system/logo.png",
# 		"title": "Pg Managment System",
# 		"route": "/pg_managment_system",
# 		"has_permission": "pg_managment_system.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/pg_managment_system/css/pg_managment_system.css"
# app_include_js = "/assets/pg_managment_system/js/pg_managment_system.js"

# include js, css files in header of web template
# web_include_css = "/assets/pg_managment_system/css/pg_managment_system.css"
# web_include_js = "/assets/pg_managment_system/js/pg_managment_system.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "pg_managment_system/public/scss/website"

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
# app_include_icons = "pg_managment_system/public/icons.svg"

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
# 	"methods": "pg_managment_system.utils.jinja_methods",
# 	"filters": "pg_managment_system.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "pg_managment_system.install.before_install"
# after_install = "pg_managment_system.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "pg_managment_system.uninstall.before_uninstall"
# after_uninstall = "pg_managment_system.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "pg_managment_system.utils.before_app_install"
# after_app_install = "pg_managment_system.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "pg_managment_system.utils.before_app_uninstall"
# after_app_uninstall = "pg_managment_system.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "pg_managment_system.notifications.get_notification_config"

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
# 		"pg_managment_system.tasks.all"
# 	],
# 	"daily": [
# 		"pg_managment_system.tasks.daily"
# 	],
# 	"hourly": [
# 		"pg_managment_system.tasks.hourly"
# 	],
# 	"weekly": [
# 		"pg_managment_system.tasks.weekly"
# 	],
# 	"monthly": [
# 		"pg_managment_system.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "pg_managment_system.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "pg_managment_system.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "pg_managment_system.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["pg_managment_system.utils.before_request"]
# after_request = ["pg_managment_system.utils.after_request"]

# Job Events
# ----------
# before_job = ["pg_managment_system.utils.before_job"]
# after_job = ["pg_managment_system.utils.after_job"]

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
# 	"pg_managment_system.auth.validate"
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



# ---------------------------------------------------------------------------
# PG Management System
# ---------------------------------------------------------------------------
after_install = "pg_managment_system.install.after_install"
after_migrate = "pg_managment_system.install.after_migrate"

_SCOPED = (
	"PG Property",
	"PG Building",
	"PG Floor",
	"PG Room",
	"PG Bed",
	"PG Tenant",
	"PG Booking",
	"PG Occupancy",
	"PG Rent Invoice",
	"PG Electricity Meter",
	"PG Meter Reading",
	"PG Payment",
	"PG Expense",
	"PG WhatsApp Message",
)

# Property-level authorization (see pg_managment_system/permissions.py)
permission_query_conditions = {dt: "pg_managment_system.permissions.property_query_conditions" for dt in _SCOPED}
has_permission = {dt: "pg_managment_system.permissions.has_property_permission" for dt in _SCOPED}

doc_events = {
	"PG Booking": {"after_insert": "pg_managment_system.services.events.booking_after_insert"},
	"PG Occupancy": {
		"after_insert": "pg_managment_system.services.events.occupancy_after_insert",
		"on_update": "pg_managment_system.services.events.occupancy_on_update",
	},
	"PG Payment": {"on_submit": "pg_managment_system.services.events.payment_on_submit"},
}

scheduler_events = {
	"daily": ["pg_managment_system.services.billing.daily"],
}

# Business users never need Desk; send them to the Vue app after login.
role_home_page = {
	"PG Manager": "/hostelsuite",
	"PG Accountant": "/hostelsuite",
	"PG Staff": "/hostelsuite",
}

# Frappe's login always lands System Users on /app; bounce PG users (without
# System Manager) to the Vue site instead. URL: site config `pg_frontend_url`.
update_website_context = ["pg_managment_system.redirects.redirect_desk_to_frontend"]

# Replace Frappe's /login with the HostelSuite (Vue) login. `/login?native=1` bypasses.
page_renderer = [
	"pg_managment_system.redirects.FrontendLoginPage",
	# Serves the built Vue app at /hostelsuite (pg_managment_system/frontend.py)
	"pg_managment_system.frontend.FrontendPage",
]
