"""Rent invoicing."""

import frappe
from frappe import _
from frappe.utils import flt, today

from pg_managment_system.api.resource import serialize
from pg_managment_system.api.utils import require_perm, sql_in
from pg_managment_system.permissions import assert_property_access, resolve_properties
from pg_managment_system.utils import month_bounds


@frappe.whitelist(methods=["GET"])
def get_rent_summary(property: str | None = None, month: str | None = None):
	require_perm("PG Rent Invoice")
	props = resolve_properties(property)
	start, end = month_bounds(month or today())
	P = sql_in(props)
	params = {"start": start, "end": end, "today": today()}
	totals = frappe.db.sql(
		f"""select coalesce(sum(total_amount),0) as invoiced, coalesce(sum(paid_amount),0) as collected,
			coalesce(sum(outstanding_amount),0) as outstanding, count(*) as invoices
		from `tabPG Rent Invoice` where docstatus=1 and property in ({P}) and period_start=%(start)s""",
		params,
		as_dict=True,
	)[0]
	by_status = frappe.db.sql(
		f"""select status, count(*) as count, coalesce(sum(outstanding_amount),0) as outstanding
		from `tabPG Rent Invoice` where docstatus<2 and property in ({P}) and period_start=%(start)s group by status""",
		params,
		as_dict=True,
	)
	overdue_all = frappe.db.sql(
		f"""select count(*), coalesce(sum(outstanding_amount),0) from `tabPG Rent Invoice`
		where docstatus=1 and property in ({P}) and outstanding_amount>0 and due_date < %(today)s""",
		params,
	)[0]
	pending = frappe.db.sql(
		f"""select count(*) from `tabPG Occupancy` o where o.property in ({P}) and o.check_in_date <= %(end)s
		and (o.status != 'Ended' or o.check_out_date >= %(start)s)
		and not exists (select 1 from `tabPG Rent Invoice` i join `tabPG Invoice Item` it on it.parent=i.name
			where i.occupancy=o.name and i.period_start=%(start)s and i.docstatus<2 and it.item_type='Rent')""",
		params,
	)[0][0]
	return {
		"data": {
			"period": {"start": str(start), "end": str(end)},
			"totals": totals,
			"by_status": by_status,
			"overdue": {"count": overdue_all[0], "amount": flt(overdue_all[1])},
			"pending_occupancies": pending,
		}
	}


@frappe.whitelist(methods=["POST"])
def generate_invoices(month: str | None = None, property: str | None = None, submit: int = 1):
	require_perm("PG Rent Invoice", "create")
	if int(submit):
		require_perm("PG Rent Invoice", "submit")
	from pg_managment_system.services.billing import generate_monthly_invoices

	props = resolve_properties(property)
	result = generate_monthly_invoices(month or today(), props, submit=bool(int(submit)))
	msg = _("{0} invoice(s) generated").format(len(result["created"]))
	return {"data": result, "message": msg}


@frappe.whitelist(methods=["POST"])
def create_invoice_for_occupancy(occupancy: str, month: str | None = None):
	require_perm("PG Rent Invoice", "create")
	occ = frappe.get_doc("PG Occupancy", occupancy)
	occ.check_permission("read")
	from pg_managment_system.services.billing import build_invoice

	inv = build_invoice(occupancy, month or today())
	if not inv:
		frappe.throw(_("Nothing to invoice for this period"))
	return {"data": serialize(inv), "message": _("Invoice {0} created").format(inv.name)}


@frappe.whitelist(methods=["GET"])
def get_invoice(name: str):
	inv = frappe.get_doc("PG Rent Invoice", name)
	inv.check_permission("read")
	payments = frappe.db.sql(
		"""select p.name, p.payment_date, p.mode, p.reference_no, a.allocated_amount, p.docstatus
		from `tabPG Payment Allocation` a join `tabPG Payment` p on p.name=a.parent
		where a.invoice=%s and p.docstatus=1 order by p.payment_date""",
		name,
		as_dict=True,
	)
	tenant = frappe.db.get_value("PG Tenant", inv.tenant, ["full_name", "mobile", "email"], as_dict=True)
	room = frappe.db.get_value("PG Room", inv.room, "room_number")
	prop = frappe.db.get_value(
		"PG Property", inv.property, ["property_name", "address_line", "city", "phone"], as_dict=True
	)
	return {"data": {"invoice": serialize(inv), "payments": payments, "tenant": tenant, "room_number": room, "property": prop}}


@frappe.whitelist(methods=["POST"])
def send_invoice_whatsapp(name: str, purpose: str = "Rent Reminder"):
	inv = frappe.get_doc("PG Rent Invoice", name)
	inv.check_permission("read")
	require_perm("PG WhatsApp Message", "create")
	if purpose not in ("Rent Reminder", "Invoice Issued"):
		frappe.throw(_("Invalid message type"))
	from pg_managment_system.services.whatsapp import send_for_document

	log = send_for_document(purpose, "PG Rent Invoice", name)
	if not log:
		frappe.throw(_("No enabled WhatsApp template for {0}, or tenant opted out").format(purpose))
	if purpose == "Rent Reminder":
		frappe.db.set_value("PG Rent Invoice", name, "reminder_sent_on", today(), update_modified=False)
	return {"data": {"message": log.name}, "message": _("WhatsApp message queued")}
