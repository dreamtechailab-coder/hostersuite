"""Notification center + Web Push subscription."""

import json

import frappe
from frappe import _


@frappe.whitelist(methods=["GET"])
def get_notifications(limit: int = 20):
	user = frappe.session.user
	rows = frappe.get_all(
		"Notification Log",
		filters={"for_user": user},
		fields=["name", "subject", "document_type", "document_name", "read", "creation", "type"],
		order_by="creation desc",
		page_length=min(int(limit), 50),
	)
	unread = frappe.db.count("Notification Log", {"for_user": user, "read": 0})
	for r in rows:
		r["subject"] = frappe.utils.strip_html(r.subject or "")
	return {"data": rows, "unread": unread}


@frappe.whitelist(methods=["POST"])
def mark_read(name: str | None = None):
	user = frappe.session.user
	filters = {"for_user": user, "read": 0}
	if name:
		filters["name"] = name
	for n in frappe.get_all("Notification Log", filters=filters, pluck="name"):
		frappe.db.set_value("Notification Log", n, "read", 1, update_modified=False)
	return {"message": _("Marked as read")}


@frappe.whitelist(methods=["POST"])
def save_push_subscription(subscription, user_agent: str | None = None):
	sub = subscription if isinstance(subscription, dict) else json.loads(subscription)
	endpoint = sub.get("endpoint")
	if not endpoint or not str(endpoint).startswith("https://"):
		frappe.throw(_("Invalid subscription"))
	existing = frappe.db.get_value("PG Push Subscription", {"endpoint": endpoint}, "name")
	if existing:
		frappe.db.set_value("PG Push Subscription", existing, {"user": frappe.session.user, "subscription_json": json.dumps(sub)})
	else:
		frappe.get_doc(
			{"doctype": "PG Push Subscription", "user": frappe.session.user, "endpoint": endpoint,
			 "subscription_json": json.dumps(sub), "user_agent": (user_agent or "")[:500]}
		).insert(ignore_permissions=True)
	return {"message": _("Notifications enabled")}


@frappe.whitelist(methods=["POST"])
def remove_push_subscription(endpoint: str):
	name = frappe.db.get_value("PG Push Subscription", {"endpoint": endpoint, "user": frappe.session.user}, "name")
	if name:
		frappe.delete_doc("PG Push Subscription", name, ignore_permissions=True)
	return {"message": _("Notifications disabled")}
