"""WhatsApp delivery through the Meta Cloud API.

Messages are always logged in *PG WhatsApp Message* and delivered from a
background job, so request handlers never block on the network.
"""

import re

import frappe
import requests
from frappe import _
from frappe.utils import fmt_money, formatdate, now_datetime

from pg_managment_system.utils import get_settings


def document_context(doctype: str, name: str) -> dict:
	doc = frappe.get_doc(doctype, name)
	settings = get_settings()
	ctx = {"organization": settings.organization_name}
	tenant = doc.get("tenant")
	if tenant:
		t = frappe.db.get_value("PG Tenant", tenant, ["full_name", "mobile"], as_dict=True)
		ctx.update(tenant_name=t.full_name, mobile=t.mobile)
	if doc.get("property"):
		ctx["property"] = doc.property
	cur = settings.currency or "INR"
	if doctype == "PG Rent Invoice":
		ctx.update(
			invoice=doc.name,
			amount=fmt_money(doc.outstanding_amount or doc.total_amount, currency=cur),
			total=fmt_money(doc.total_amount, currency=cur),
			due_date=formatdate(doc.due_date),
			period=formatdate(doc.period_start, "MMM yyyy"),
		)
	elif doctype == "PG Payment":
		ctx.update(payment=doc.name, amount=fmt_money(doc.amount, currency=cur), date=formatdate(doc.payment_date))
	elif doctype == "PG Booking":
		ctx.update(booking=doc.name, check_in=formatdate(doc.expected_check_in), room=doc.room)
	elif doctype == "PG Occupancy":
		ctx.update(room=frappe.db.get_value("PG Room", doc.room, "room_number"), check_in=formatdate(doc.check_in_date))
	return ctx


def send_for_document(purpose: str, doctype: str, name: str):
	template = frappe.db.get_value("PG WhatsApp Template", {"purpose": purpose, "enabled": 1}, "name")
	if not template:
		return None
	doc = frappe.get_doc(doctype, name)
	if not doc.get("tenant"):
		return None
	if not frappe.db.get_value("PG Tenant", doc.tenant, "whatsapp_opt_in"):
		return None
	return queue_message(doc.tenant, template, document_context(doctype, name), doctype, name)


def queue_message(tenant: str | None, template: str | None, context: dict, ref_doctype=None, ref_name=None,
				  message: str | None = None, mobile: str | None = None):
	tdoc = frappe.get_doc("PG WhatsApp Template", template) if template else None
	if tenant:
		t = frappe.db.get_value("PG Tenant", tenant, ["mobile", "property", "full_name"], as_dict=True)
		mobile = mobile or t.mobile
		context.setdefault("tenant_name", t.full_name)
		prop = t.property
	else:
		prop = context.get("property")
	if not mobile:
		frappe.throw(_("Mobile number is required"))
	body = tdoc.render(context) if tdoc else message
	if not body:
		frappe.throw(_("Message is empty"))
	log = frappe.get_doc(
		{
			"doctype": "PG WhatsApp Message",
			"tenant": tenant,
			"property": prop,
			"mobile": mobile,
			"template": template,
			"message": body,
			"status": "Queued",
			"reference_doctype": ref_doctype,
			"reference_name": ref_name,
		}
	).insert(ignore_permissions=True)
	params = [str(context.get(p, "")) for p in tdoc.placeholders()] if tdoc else []
	frappe.enqueue(
		"pg_managment_system.services.whatsapp.deliver",
		queue="short",
		message_name=log.name,
		params=params,
		enqueue_after_commit=True,
	)
	return log


def _to_e164(mobile: str, cc: str) -> str:
	digits = re.sub(r"\D", "", mobile)
	return digits if len(digits) > 10 else f"{cc}{digits}"


def deliver(message_name: str, params: list | None = None):
	log = frappe.get_doc("PG WhatsApp Message", message_name)
	settings = get_settings()
	try:
		if not settings.whatsapp_enabled:
			raise ValueError(_("WhatsApp is disabled in PG Settings"))
		token = settings.get_password("whatsapp_access_token", raise_exception=False)
		if not (token and settings.whatsapp_phone_number_id):
			raise ValueError(_("WhatsApp credentials are not configured"))
		url = f"{settings.whatsapp_api_base.rstrip('/')}/{settings.whatsapp_api_version}/{settings.whatsapp_phone_number_id}/messages"
		to = _to_e164(log.mobile, settings.whatsapp_default_country_code or "91")
		tpl = frappe.get_doc("PG WhatsApp Template", log.template) if log.template else None
		if tpl and tpl.meta_template_name:
			payload = {
				"messaging_product": "whatsapp",
				"to": to,
				"type": "template",
				"template": {
					"name": tpl.meta_template_name,
					"language": {"code": tpl.language_code or "en"},
					"components": [{"type": "body", "parameters": [{"type": "text", "text": p} for p in (params or [])]}]
					if params
					else [],
				},
			}
		else:
			payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": log.message}}
		resp = requests.post(url, json=payload, headers={"Authorization": f"Bearer {token}"}, timeout=20)
		data = resp.json() if resp.content else {}
		if resp.status_code >= 400:
			raise ValueError((data.get("error") or {}).get("message") or f"HTTP {resp.status_code}")
		log.db_set(
			{"status": "Sent", "sent_at": now_datetime(), "provider_message_id": (data.get("messages") or [{}])[0].get("id"), "error": None}
		)
	except Exception as e:
		log.db_set({"status": "Failed", "error": str(e)[:500]})
