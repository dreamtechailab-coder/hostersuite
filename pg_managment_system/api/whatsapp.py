"""WhatsApp messaging endpoints."""

import frappe
from frappe import _
from frappe.utils import add_days, today

from pg_managment_system.api.utils import require_perm, sql_in
from pg_managment_system.permissions import resolve_properties


@frappe.whitelist(methods=["GET"])
def get_dashboard(property: str | None = None):
	require_perm("PG WhatsApp Message")
	props = resolve_properties(property)
	since = add_days(today(), -30)
	P = sql_in(props)
	by_status = dict(
		frappe.db.sql(
			f"""select status, count(*) from `tabPG WhatsApp Message`
			where (property in ({P}) or property is null) and creation >= %s group by status""",
			since,
		)
	)
	daily = frappe.db.sql(
		f"""select date(creation) as day, sum(status='Sent') as sent, sum(status='Failed') as failed
		from `tabPG WhatsApp Message` where (property in ({P}) or property is null) and creation >= %s
		group by 1 order by 1""",
		since,
		as_dict=True,
	)
	settings = frappe.get_cached_doc("PG Settings")
	return {
		"data": {
			"enabled": bool(settings.whatsapp_enabled),
			"configured": bool(settings.whatsapp_phone_number_id and settings.get_password("whatsapp_access_token", raise_exception=False)),
			"by_status": by_status,
			"daily": daily,
			"templates": frappe.db.count("PG WhatsApp Template", {"enabled": 1}),
			"opted_in_tenants": frappe.db.count("PG Tenant", {"whatsapp_opt_in": 1, "status": ("in", ["Active", "On Notice"]), "property": ("in", props or [""])}),
		}
	}


@frappe.whitelist(methods=["POST"])
def send_message(tenant: str, template: str | None = None, message: str | None = None):
	require_perm("PG WhatsApp Message", "create")
	t = frappe.get_doc("PG Tenant", tenant)
	t.check_permission("read")
	if not t.whatsapp_opt_in:
		frappe.throw(_("{0} has not opted in to WhatsApp messages").format(t.full_name))
	if not template and not (message or "").strip():
		frappe.throw(_("Choose a template or type a message"))
	from pg_managment_system.services.whatsapp import queue_message

	ctx = {"tenant_name": t.full_name, "property": t.property,
		   "organization": frappe.get_cached_doc("PG Settings").organization_name}
	log = queue_message(tenant, template, ctx, "PG Tenant", tenant, message=message)
	return {"data": {"name": log.name}, "message": _("Message queued")}


@frappe.whitelist(methods=["POST"])
def send_bulk_reminders(property: str | None = None):
	require_perm("PG WhatsApp Message", "create")
	require_perm("PG Rent Invoice")
	props = resolve_properties(property)
	from pg_managment_system.services.whatsapp import send_for_document

	invoices = frappe.get_list(
		"PG Rent Invoice",
		filters={"docstatus": 1, "outstanding_amount": (">", 0), "property": ("in", props or [""])},
		pluck="name",
	)
	queued = 0
	for inv in invoices:
		if send_for_document("Rent Reminder", "PG Rent Invoice", inv):
			frappe.db.set_value("PG Rent Invoice", inv, "reminder_sent_on", today(), update_modified=False)
			queued += 1
	return {"data": {"queued": queued, "invoices": len(invoices)}, "message": _("{0} reminder(s) queued").format(queued)}


@frappe.whitelist(methods=["POST"])
def preview_template(template: str, tenant: str | None = None):
	require_perm("PG WhatsApp Template")
	tpl = frappe.get_doc("PG WhatsApp Template", template)
	ctx = {p: f"[{p}]" for p in tpl.placeholders()}
	if tenant:
		t = frappe.get_doc("PG Tenant", tenant)
		t.check_permission("read")
		ctx.update(tenant_name=t.full_name, property=t.property)
	return {"data": {"text": tpl.render(ctx), "placeholders": tpl.placeholders()}}


@frappe.whitelist(methods=["POST"])
def retry_message(name: str):
	require_perm("PG WhatsApp Message", "create")
	doc = frappe.get_doc("PG WhatsApp Message", name)
	doc.check_permission("read")
	if doc.status != "Failed":
		frappe.throw(_("Only failed messages can be retried"))
	doc.db_set({"status": "Queued", "error": None})
	frappe.enqueue("pg_managment_system.services.whatsapp.deliver", queue="short", message_name=name,
				   enqueue_after_commit=True)
	return {"data": {"name": name}, "message": _("Message re-queued")}
