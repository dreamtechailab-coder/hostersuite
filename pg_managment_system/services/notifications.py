"""In-app (Notification Log) and Web Push notifications for PG staff."""

import json

import frappe

from pg_managment_system.permissions import PG_ROLES


def recipients_for_property(prop: str, roles=("PG Admin", "PG Manager")) -> list[str]:
	users = set(
		frappe.get_all(
			"Has Role",
			filters={"role": ("in", ["PG Admin"]), "parenttype": "User"},
			pluck="parent",
		)
	)
	scoped = frappe.get_all(
		"User Permission", filters={"allow": "PG Property", "for_value": prop}, pluck="user"
	)
	role_users = set(
		frappe.get_all("Has Role", filters={"role": ("in", list(roles)), "parent": ("in", scoped or [""])}, pluck="parent")
	)
	users |= role_users
	enabled = frappe.get_all("User", filters={"name": ("in", list(users) or [""]), "enabled": 1}, pluck="name")
	return [u for u in enabled if u not in ("Administrator", "Guest")]


def notify(prop: str, subject: str, doctype: str, name: str, roles=("PG Admin", "PG Manager")):
	exclude = frappe.session.user
	for user in recipients_for_property(prop, roles):
		if user == exclude:
			continue
		frappe.get_doc(
			{
				"doctype": "Notification Log",
				"for_user": user,
				"type": "Alert",
				"subject": subject,
				"document_type": doctype,
				"document_name": name,
				"from_user": exclude,
			}
		).insert(ignore_permissions=True)
		frappe.enqueue(
			"pg_managment_system.services.notifications.push_to_user",
			queue="short",
			user=user,
			title=subject,
			url=f"/{doctype.lower().replace('pg ', '').replace(' ', '-')}/{name}",
			enqueue_after_commit=True,
		)


def push_to_user(user: str, title: str, url: str = "/"):
	"""Send a Web Push message if pywebpush and VAPID keys are configured (optional)."""
	try:
		from pywebpush import WebPushException, webpush
	except ImportError:
		return
	settings = frappe.get_cached_doc("PG Settings")
	private_key = settings.get_password("vapid_private_key", raise_exception=False)
	if not private_key:
		return
	for sub in frappe.get_all("PG Push Subscription", filters={"user": user}, fields=["name", "subscription_json"]):
		try:
			webpush(
				subscription_info=json.loads(sub.subscription_json),
				data=json.dumps({"title": title, "url": url}),
				vapid_private_key=private_key,
				vapid_claims={"sub": settings.vapid_subject or "mailto:admin@example.com"},
			)
		except WebPushException as e:
			if getattr(e, "response", None) is not None and e.response.status_code in (404, 410):
				frappe.delete_doc("PG Push Subscription", sub.name, ignore_permissions=True)
