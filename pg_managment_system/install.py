"""Idempotent setup: roles, default categories, WhatsApp templates and settings."""

import frappe

ROLES = ("PG Admin", "PG Manager", "PG Accountant", "PG Staff")
EXPENSE_CATEGORIES = (
	"Electricity", "Water", "Internet", "Groceries", "Salaries", "Maintenance & Repairs", "Housekeeping",
	"Rent / Lease", "Property Tax", "Furniture & Fixtures", "Marketing", "Miscellaneous",
)
TEMPLATES = (
	("Rent Reminder", "Rent Reminder",
	 "Hi {{tenant_name}}, a gentle reminder that your rent of {{amount}} for {{period}} is due on {{due_date}}. Invoice: {{invoice}}. – {{organization}}"),
	("Invoice Issued", "Invoice Issued",
	 "Hi {{tenant_name}}, your invoice {{invoice}} for {{period}} of {{total}} has been generated. Due date: {{due_date}}. – {{organization}}"),
	("Payment Receipt", "Payment Receipt",
	 "Hi {{tenant_name}}, we have received your payment of {{amount}} on {{date}} (Ref {{payment}}). Thank you! – {{organization}}"),
	("Welcome", "Welcome",
	 "Welcome to {{property}}, {{tenant_name}}! Your room {{room}} is ready from {{check_in}}. Reach out to us for anything you need. – {{organization}}"),
	("Booking Confirmation", "Booking Confirmation",
	 "Hi {{tenant_name}}, your booking {{booking}} is confirmed. Expected check-in: {{check_in}}. – {{organization}}"),
)


def after_install():
	setup()


def after_migrate():
	setup()


def setup():
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)
	for cat in EXPENSE_CATEGORIES:
		if not frappe.db.exists("PG Expense Category", cat):
			frappe.get_doc({"doctype": "PG Expense Category", "category_name": cat}).insert(ignore_permissions=True)
	for name, purpose, body in TEMPLATES:
		if not frappe.db.exists("PG WhatsApp Template", name):
			frappe.get_doc(
				{"doctype": "PG WhatsApp Template", "template_name": name, "purpose": purpose, "body": body, "enabled": 1}
			).insert(ignore_permissions=True)
	settings = frappe.get_single("PG Settings")
	if not settings.currency:
		settings.currency = "INR" if frappe.db.exists("Currency", "INR") else None
		settings.organization_name = settings.organization_name or "My PG"
		settings.flags.ignore_mandatory = True
		settings.save(ignore_permissions=True)
	frappe.db.commit()
