"""Payment collection with invoice allocation."""

import frappe
from frappe import _
from frappe.utils import flt, today

from pg_managment_system.api.resource import serialize
from pg_managment_system.api.utils import parse_json, require_perm
from pg_managment_system.utils import money


@frappe.whitelist(methods=["GET"])
def get_outstanding_invoices(tenant: str):
	require_perm("PG Rent Invoice")
	t = frappe.get_doc("PG Tenant", tenant)
	t.check_permission("read")
	rows = frappe.get_list(
		"PG Rent Invoice",
		filters={"tenant": tenant, "docstatus": 1, "outstanding_amount": (">", 0)},
		fields=["name", "period_start", "due_date", "total_amount", "paid_amount", "outstanding_amount", "status"],
		order_by="due_date asc",
	)
	return {"data": rows}


@frappe.whitelist(methods=["POST"])
def collect_payment(tenant: str, amount, mode: str, payment_date: str | None = None, reference_no: str | None = None,
					remarks: str | None = None, allocations=None, client_request_id: str | None = None):
	"""Record and submit a payment. Without explicit allocations it settles the oldest dues first.

	``client_request_id`` makes the call idempotent: a retried request returns the original payment
	instead of creating a duplicate.
	"""
	require_perm("PG Payment", "create")
	require_perm("PG Payment", "submit")
	if client_request_id:
		existing = frappe.db.get_value("PG Payment", {"client_request_id": client_request_id}, "name")
		if existing:
			doc = frappe.get_doc("PG Payment", existing)
			doc.check_permission("read")
			return {"data": serialize(doc), "message": _("Payment already recorded")}

	t = frappe.get_doc("PG Tenant", tenant)
	t.check_permission("read")
	amount = money(amount)
	allocations = parse_json(allocations, None)
	if allocations is None:
		allocations, remaining = [], amount
		for inv in get_outstanding_invoices(tenant)["data"]:
			if remaining <= 0:
				break
			alloc = min(remaining, flt(inv.outstanding_amount))
			allocations.append({"invoice": inv.name, "allocated_amount": alloc})
			remaining = money(remaining - alloc)

	doc = frappe.get_doc(
		{
			"doctype": "PG Payment",
			"tenant": tenant,
			"property": t.property,
			"amount": amount,
			"mode": mode,
			"payment_date": payment_date or today(),
			"reference_no": reference_no,
			"remarks": remarks,
			"client_request_id": client_request_id,
			"allocations": [
				{"invoice": a["invoice"], "allocated_amount": money(a["allocated_amount"])}
				for a in allocations
				if flt(a.get("allocated_amount")) > 0
			],
		}
	)
	doc.insert()
	doc.submit()
	return {"data": serialize(doc), "message": _("Payment of {0} recorded").format(amount)}


@frappe.whitelist(methods=["GET"])
def get_payment(name: str):
	doc = frappe.get_doc("PG Payment", name)
	doc.check_permission("read")
	data = serialize(doc)
	for a in data["allocations"]:
		a.update(
			frappe.db.get_value(
				"PG Rent Invoice", a["invoice"], ["period_start", "total_amount", "outstanding_amount", "status"], as_dict=True
			)
			or {}
		)
	tenant = frappe.db.get_value("PG Tenant", doc.tenant, ["full_name", "mobile"], as_dict=True)
	received_by = frappe.db.get_value("User", doc.received_by, "full_name") if doc.received_by else None
	return {"data": {"payment": data, "tenant": tenant, "received_by_name": received_by}}


@frappe.whitelist(methods=["POST"])
def cancel_payment(name: str, reason: str | None = None):
	doc = frappe.get_doc("PG Payment", name)
	doc.check_permission("cancel")
	if reason:
		doc.add_comment("Comment", _("Cancelled: {0}").format(reason))
	doc.cancel()
	return {"data": serialize(doc), "message": _("Payment cancelled")}
