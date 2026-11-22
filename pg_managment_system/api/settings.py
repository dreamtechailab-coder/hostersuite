"""Application settings (admin only for writes; secrets are write-only)."""

import frappe
from frappe import _

from pg_managment_system.api.utils import parse_json, require_roles

SECRET_FIELDS = ("whatsapp_access_token", "vapid_private_key")
EDITABLE = (
	"organization_name", "currency", "support_phone", "support_email", "default_rent_due_day",
	"auto_generate_invoices", "invoice_generation_day", "late_fee_amount", "late_fee_grace_days",
	"send_rent_reminders", "reminder_days_before_due", "whatsapp_enabled", "whatsapp_api_base",
	"whatsapp_api_version", "whatsapp_phone_number_id", "whatsapp_default_country_code",
	"vapid_public_key", "vapid_subject",
)


@frappe.whitelist(methods=["GET"])
def get_settings():
	require_roles("PG Admin")
	doc = frappe.get_doc("PG Settings")
	data = {f: doc.get(f) for f in EDITABLE}
	for f in SECRET_FIELDS:
		data[f"{f}_set"] = bool(doc.get_password(f, raise_exception=False))
	return {"data": data}


@frappe.whitelist(methods=["POST"])
def update_settings(data):
	require_roles("PG Admin")
	data = parse_json(data, {})
	doc = frappe.get_doc("PG Settings")
	for f in EDITABLE:
		if f in data:
			doc.set(f, data[f])
	for f in SECRET_FIELDS:
		if data.get(f):  # only overwrite when a new secret is supplied
			doc.set(f, data[f])
	for day_field in ("default_rent_due_day", "invoice_generation_day"):
		if doc.get(day_field) and not 1 <= int(doc.get(day_field)) <= 28:
			frappe.throw(_("Day of month must be between 1 and 28"))
	doc.save()
	return {"message": _("Settings saved"), **get_settings()}
