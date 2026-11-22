"""Rent & electricity billing workflows."""

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, today

from pg_managment_system.utils import clamp_day, get_settings, money, month_bounds, overlap_days


def build_invoice(occupancy: str, period_date=None, submit: bool = True, include_electricity: bool = True):
	"""Create the monthly invoice for an occupancy. Returns the invoice or None if nothing to bill."""
	occ = frappe.get_doc("PG Occupancy", occupancy)
	start, end = month_bounds(period_date or today())
	stay_end = getdate(occ.check_out_date) if occ.check_out_date else end
	days = overlap_days(occ.check_in_date, stay_end, start, end)
	month_days = (end - start).days + 1

	inv = frappe.new_doc("PG Rent Invoice")
	inv.update(
		{
			"tenant": occ.tenant,
			"occupancy": occ.name,
			"property": occ.property,
			"invoice_date": today(),
			"period_start": start,
			"period_end": end,
		}
	)
	due = clamp_day(start.year, start.month, occ.rent_due_day or get_settings().default_rent_due_day or 5)
	inv.due_date = max(due, getdate(today()))

	already_billed = frappe.db.sql(
		"""select inv.name from `tabPG Rent Invoice` inv join `tabPG Invoice Item` it on it.parent=inv.name
		where inv.occupancy=%s and inv.period_start=%s and inv.docstatus<2 and it.item_type='Rent' limit 1""",
		(occ.name, start),
	)
	if days and not already_billed:
		rent = money(flt(occ.monthly_rent) * days / month_days) if days < month_days else money(occ.monthly_rent)
		label = start.strftime("%b %Y") + (f" ({days} of {month_days} days)" if days < month_days else "")
		inv.append("items", {"item_type": "Rent", "description": f"Rent – {label}", "amount": rent})

	if include_electricity:
		for share in unbilled_electricity(occ.name):
			inv.append(
				"items",
				{
					"item_type": "Electricity",
					"description": f"Electricity {share.period_start.strftime('%d %b')}–{share.period_end.strftime('%d %b')}",
					"amount": share.amount,
					"reference_doctype": "PG Meter Reading",
					"reference_name": share.reading,
				},
			)

	late_fee = late_fee_for(occ.name, start)
	if late_fee:
		inv.append(
			"items",
			{
				"item_type": "Late Fee",
				"description": _("Late fee for {0}").format(late_fee["invoice"]),
				"amount": late_fee["amount"],
				"reference_doctype": "PG Rent Invoice",
				"reference_name": late_fee["invoice"],
			},
		)

	if not inv.items:
		return None
	inv.insert()
	if submit:
		inv.submit()
	return inv


def unbilled_electricity(occupancy: str):
	return frappe.db.sql(
		"""select r.name as reading, r.period_start, r.period_end, s.amount
		from `tabPG Electricity Share` s join `tabPG Meter Reading` r on r.name = s.parent
		where s.parenttype='PG Meter Reading' and r.docstatus=1 and s.occupancy=%s
		and (s.invoice is null or s.invoice='') and s.amount > 0
		and not exists (
			select 1 from `tabPG Invoice Item` it join `tabPG Rent Invoice` i on i.name=it.parent
			where i.docstatus=0 and it.reference_doctype='PG Meter Reading' and it.reference_name=r.name and i.occupancy=%s
		)""",
		(occupancy, occupancy),
		as_dict=True,
	)


def late_fee_for(occupancy: str, period_start):
	"""Late fee on the previous unpaid invoice once grace has elapsed (charged once)."""
	settings = get_settings()
	if not flt(settings.late_fee_amount):
		return None
	cutoff = add_days(today(), -(settings.late_fee_grace_days or 0))
	prev = frappe.db.sql(
		"""select name from `tabPG Rent Invoice` where occupancy=%s and docstatus=1
		and period_start < %s and outstanding_amount > 0 and due_date < %s
		and not exists (select 1 from `tabPG Invoice Item` it join `tabPG Rent Invoice` i on i.name=it.parent
			where i.docstatus<2 and it.item_type='Late Fee' and it.reference_name=`tabPG Rent Invoice`.name)
		order by period_start desc limit 1""",
		(occupancy, period_start, cutoff),
	)
	return {"invoice": prev[0][0], "amount": money(settings.late_fee_amount)} if prev else None


def generate_monthly_invoices(period_date=None, properties: list[str] | None = None, submit: bool = True) -> dict:
	start, end = month_bounds(period_date or today())
	filters = {"check_in_date": ("<=", end), "status": ("!=", "Ended")}
	if properties is not None:
		filters["property"] = ("in", properties or [""])
	occupancies = frappe.get_all("PG Occupancy", filters=filters, pluck="name")
	# include occupancies that ended within the period (final month)
	ended = frappe.get_all(
		"PG Occupancy",
		filters={
			"status": "Ended",
			"check_out_date": ("between", [start, end]),
			**({"property": ("in", properties or [""])} if properties is not None else {}),
		},
		pluck="name",
	)
	created, skipped, errors = [], 0, []
	for occ in occupancies + ended:
		frappe.db.savepoint("pg_invoice")
		try:
			inv = build_invoice(occ, start, submit=submit)
			frappe.db.release_savepoint("pg_invoice")
			if inv:
				created.append(inv.name)
			else:
				skipped += 1
		except Exception as e:
			frappe.db.rollback(save_point="pg_invoice")
			errors.append({"occupancy": occ, "error": str(e)})
	return {"created": created, "skipped": skipped, "errors": errors, "period": str(start)}


# ------------------------------------------------------------------ scheduled jobs
def mark_overdue_invoices():
	frappe.db.sql(
		"""update `tabPG Rent Invoice` set status='Overdue'
		where docstatus=1 and outstanding_amount > 0 and due_date < %s and status != 'Overdue'""",
		today(),
	)


def auto_generate_invoices():
	settings = get_settings()
	if not settings.auto_generate_invoices:
		return
	if getdate(today()).day != (settings.invoice_generation_day or 1):
		return
	result = generate_monthly_invoices()
	if settings.whatsapp_enabled:
		from pg_managment_system.services.whatsapp import send_for_document

		for name in result["created"]:
			send_for_document("Invoice Issued", "PG Rent Invoice", name)


def send_rent_reminders():
	settings = get_settings()
	if not settings.send_rent_reminders or not settings.whatsapp_enabled:
		return
	from pg_managment_system.services.whatsapp import send_for_document

	target = add_days(today(), settings.reminder_days_before_due or 0)
	invoices = frappe.get_all(
		"PG Rent Invoice",
		filters={
			"docstatus": 1,
			"outstanding_amount": (">", 0),
			"due_date": ("<=", target),
			"reminder_sent_on": ("is", "not set"),
		},
		pluck="name",
	)
	for name in invoices:
		send_for_document("Rent Reminder", "PG Rent Invoice", name)
		frappe.db.set_value("PG Rent Invoice", name, "reminder_sent_on", today(), update_modified=False)


def daily():
	mark_overdue_invoices()
	auto_generate_invoices()
	send_rent_reminders()
