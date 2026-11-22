"""Session bootstrap for the SPA (uses Frappe's cookie session + CSRF token)."""

import frappe
from frappe.sessions import get_csrf_token

from pg_managment_system.permissions import PG_ROLES, get_allowed_properties, is_pg_admin

PG_DOCTYPES = (
	"PG Property", "PG Building", "PG Floor", "PG Room", "PG Bed", "PG Tenant", "PG Booking",
	"PG Occupancy", "PG Rent Invoice", "PG Electricity Meter", "PG Meter Reading", "PG Payment",
	"PG Expense", "PG Expense Category", "PG WhatsApp Template", "PG WhatsApp Message", "PG Settings",
)
PTYPES = ("read", "write", "create", "delete", "submit", "cancel")


@frappe.whitelist(allow_guest=True)
def get_session():
	user = frappe.session.user
	if user == "Guest":
		return {"data": {"user": None}}

	roles = frappe.get_roles(user)
	allowed = get_allowed_properties(user)
	prop_filters = {"name": ("in", allowed or [""])} if allowed is not None else {}
	properties = frappe.get_all(
		"PG Property",
		filters={**prop_filters},
		fields=["name", "property_name", "city", "is_active"],
		order_by="property_name asc",
		ignore_permissions=True,
	)
	can = {}
	for dt in PG_DOCTYPES:
		can[dt] = {p: bool(frappe.has_permission(dt, p, user=user)) for p in PTYPES}

	settings = frappe.get_cached_doc("PG Settings")
	info = frappe.db.get_value("User", user, ["full_name", "user_image", "email"], as_dict=True)
	return {
		"data": {
			"user": user,
			"full_name": info.full_name,
			"email": info.email,
			"user_image": info.user_image,
			"roles": [r for r in roles if r in PG_ROLES or r == "System Manager"],
			"is_admin": is_pg_admin(user),
			"properties": properties,
			"can": can,
			"csrf_token": get_csrf_token(),
			"settings": {
				"organization_name": settings.organization_name,
				"currency": settings.currency or "INR",
				"whatsapp_enabled": bool(settings.whatsapp_enabled),
				"vapid_public_key": settings.vapid_public_key,
			},
		}
	}
