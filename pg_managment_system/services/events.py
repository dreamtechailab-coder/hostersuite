"""Document event handlers wired through hooks.doc_events."""

import frappe
from frappe import _
from frappe.utils import fmt_money

from pg_managment_system.services.notifications import notify


def _wa_enabled():
	return bool(frappe.get_cached_doc("PG Settings").whatsapp_enabled)


def _safe(fn, *args):
	"""Side effects (notifications/messages) must never break the business transaction."""
	try:
		fn(*args)
	except Exception:
		frappe.log_error(title="PG notification failed")


def booking_after_insert(doc, method=None):
	_safe(notify, doc.property, _("New booking from {0}").format(doc.tenant_name or doc.tenant), doc.doctype, doc.name)


def occupancy_after_insert(doc, method=None):
	_safe(notify, doc.property, _("{0} checked in").format(doc.tenant_name or doc.tenant), doc.doctype, doc.name)
	if _wa_enabled():
		from pg_managment_system.services.whatsapp import send_for_document

		_safe(send_for_document, "Welcome", doc.doctype, doc.name)


def occupancy_on_update(doc, method=None):
	before = doc.get_doc_before_save()
	if before and before.status != doc.status and doc.status == "On Notice":
		_safe(notify, doc.property, _("{0} gave notice").format(doc.tenant_name), doc.doctype, doc.name)


def payment_on_submit(doc, method=None):
	currency = frappe.get_cached_doc("PG Settings").currency or "INR"
	_safe(
		notify,
		doc.property,
		_("Payment of {0} received from {1}").format(fmt_money(doc.amount, currency=currency), doc.tenant_name),
		doc.doctype,
		doc.name,
		("PG Admin", "PG Manager", "PG Accountant"),
	)
	if _wa_enabled():
		from pg_managment_system.services.whatsapp import send_for_document

		_safe(send_for_document, "Payment Receipt", doc.doctype, doc.name)
