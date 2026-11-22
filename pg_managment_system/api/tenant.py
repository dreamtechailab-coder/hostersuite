"""Tenant 360° view, bookings and occupancy workflows (check-in / notice / check-out)."""

import frappe
from frappe import _
from frappe.utils import flt, getdate, today

from pg_managment_system.api.resource import serialize
from pg_managment_system.api.utils import require_perm


@frappe.whitelist(methods=["GET"])
def get_tenant_details(name: str):
	tenant = frappe.get_doc("PG Tenant", name)
	tenant.check_permission("read")
	data = {"tenant": serialize(tenant)}
	data["occupancies"] = frappe.get_list(
		"PG Occupancy",
		filters={"tenant": name},
		fields=["name", "property", "room", "bed", "status", "check_in_date", "notice_date", "expected_check_out",
				"check_out_date", "monthly_rent", "security_deposit", "deposit_status", "rent_due_day"],
		order_by="check_in_date desc",
	)
	for o in data["occupancies"]:
		o["room_number"] = frappe.db.get_value("PG Room", o.room, "room_number")
		o["bed_label"] = frappe.db.get_value("PG Bed", o.bed, "bed_label")
	data["bookings"] = frappe.get_list(
		"PG Booking",
		filters={"tenant": name},
		fields=["name", "room", "bed", "status", "booking_date", "expected_check_in", "advance_amount"],
		order_by="creation desc",
		page_length=10,
	)
	if frappe.has_permission("PG Rent Invoice", "read"):
		data["invoices"] = frappe.get_list(
			"PG Rent Invoice",
			filters={"tenant": name, "docstatus": ("<", 2)},
			fields=["name", "period_start", "due_date", "total_amount", "paid_amount", "outstanding_amount", "status", "docstatus"],
			order_by="period_start desc",
			page_length=24,
		)
		data["balance"] = flt(
			frappe.db.sql(
				"select sum(outstanding_amount) from `tabPG Rent Invoice` where tenant=%s and docstatus=1", name
			)[0][0]
		)
	if frappe.has_permission("PG Payment", "read"):
		data["payments"] = frappe.get_list(
			"PG Payment",
			filters={"tenant": name, "docstatus": 1},
			fields=["name", "payment_date", "amount", "mode", "reference_no"],
			order_by="payment_date desc",
			page_length=24,
		)
	return {"data": data}


# ------------------------------------------------------------------ bookings
def _booking(name: str):
	doc = frappe.get_doc("PG Booking", name)
	doc.check_permission("write")
	return doc


@frappe.whitelist(methods=["POST"])
def confirm_booking(name: str):
	doc = _booking(name)
	if doc.status != "Pending":
		frappe.throw(_("Only pending bookings can be confirmed"))
	doc.status = "Confirmed"
	doc.save()
	from pg_managment_system.services.whatsapp import send_for_document

	if frappe.get_cached_doc("PG Settings").whatsapp_enabled:
		send_for_document("Booking Confirmation", "PG Booking", doc.name)
	return {"data": serialize(doc), "message": _("Booking confirmed")}


@frappe.whitelist(methods=["POST"])
def cancel_booking(name: str, reason: str | None = None):
	doc = _booking(name)
	if doc.status in ("Checked In", "Cancelled"):
		frappe.throw(_("Booking is already {0}").format(doc.status.lower()))
	doc.status = "Cancelled"
	if reason:
		doc.notes = ((doc.notes or "") + f"\nCancelled: {reason}").strip()
	doc.save()
	return {"data": serialize(doc), "message": _("Booking cancelled")}


# ------------------------------------------------------------------ occupancy
@frappe.whitelist(methods=["POST"])
def check_in(tenant: str, bed: str, check_in_date: str | None = None, monthly_rent=None, security_deposit=None,
			 rent_due_day=None, booking: str | None = None, generate_invoice: int = 0):
	require_perm("PG Occupancy", "create")
	bed_doc = frappe.get_doc("PG Bed", bed)
	bed_doc.check_permission("read")
	room = frappe.get_doc("PG Room", bed_doc.room)
	if booking:
		b = frappe.get_doc("PG Booking", booking)
		b.check_permission("write")
		if b.status not in ("Pending", "Confirmed"):
			frappe.throw(_("Booking {0} is {1}").format(booking, b.status))
		if b.tenant != tenant:
			frappe.throw(_("Booking belongs to another tenant"))
		if bed_doc.status == "Reserved" and bed_doc.reserved_booking != booking:
			frappe.throw(_("Bed is reserved for another booking"))
		if b.bed and b.bed != bed:
			# release the originally reserved bed
			b.bed = bed
			b.save()
	settings = frappe.get_cached_doc("PG Settings")
	occ = frappe.get_doc(
		{
			"doctype": "PG Occupancy",
			"tenant": tenant,
			"property": room.property,
			"room": room.name,
			"bed": bed,
			"booking": booking,
			"check_in_date": check_in_date or today(),
			"monthly_rent": flt(monthly_rent) if monthly_rent not in (None, "") else room.rent_per_bed,
			"security_deposit": flt(security_deposit) if security_deposit not in (None, "") else room.security_deposit,
			"rent_due_day": int(rent_due_day or settings.default_rent_due_day or 5),
			"status": "Active",
			"deposit_status": "Held" if flt(security_deposit if security_deposit not in (None, "") else room.security_deposit) else "Not Collected",
		}
	)
	occ.insert()
	invoice = None
	if int(generate_invoice or 0) and frappe.has_permission("PG Rent Invoice", "create"):
		from pg_managment_system.services.billing import build_invoice

		inv = build_invoice(occ.name, occ.check_in_date)
		invoice = inv.name if inv else None
	return {"data": {"occupancy": serialize(occ), "invoice": invoice}, "message": _("Tenant checked in")}


@frappe.whitelist(methods=["POST"])
def give_notice(name: str, notice_date: str | None = None, expected_check_out: str | None = None):
	doc = frappe.get_doc("PG Occupancy", name)
	doc.check_permission("write")
	if doc.status != "Active":
		frappe.throw(_("Only active occupancies can be put on notice"))
	doc.status = "On Notice"
	doc.notice_date = notice_date or today()
	doc.expected_check_out = expected_check_out
	doc.save()
	return {"data": serialize(doc), "message": _("Notice recorded")}


@frappe.whitelist(methods=["POST"])
def check_out(name: str, check_out_date: str | None = None, deposit_status: str = "Held", deposit_refund_amount=0,
			  generate_final_invoice: int = 0):
	doc = frappe.get_doc("PG Occupancy", name)
	doc.check_permission("write")
	if doc.status == "Ended":
		frappe.throw(_("Tenant has already checked out"))
	if deposit_status not in ("Held", "Refunded", "Adjusted", "Not Collected"):
		frappe.throw(_("Invalid deposit status"))
	if flt(deposit_refund_amount) > flt(doc.security_deposit):
		frappe.throw(_("Refund cannot exceed the security deposit"))
	doc.status = "Ended"
	doc.check_out_date = check_out_date or today()
	if getdate(doc.check_out_date) < getdate(doc.check_in_date):
		frappe.throw(_("Check-out date cannot be before check-in date"))
	doc.deposit_status = deposit_status
	doc.deposit_refund_amount = flt(deposit_refund_amount)
	doc.save()
	invoice = None
	if int(generate_final_invoice or 0) and frappe.has_permission("PG Rent Invoice", "create"):
		from pg_managment_system.services.billing import build_invoice

		inv = build_invoice(doc.name, doc.check_out_date)
		invoice = inv.name if inv else None
	return {"data": {"occupancy": serialize(doc), "invoice": invoice}, "message": _("Tenant checked out")}
