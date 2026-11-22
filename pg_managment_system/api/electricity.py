"""Electricity meters, readings and bills."""

import frappe
from frappe import _
from frappe.utils import flt, today

from pg_managment_system.api.resource import serialize
from pg_managment_system.api.utils import require_perm, sql_in
from pg_managment_system.permissions import resolve_properties
from pg_managment_system.utils import month_bounds


@frappe.whitelist(methods=["GET"])
def get_meters(property: str | None = None, month: str | None = None):
	require_perm("PG Electricity Meter")
	props = resolve_properties(property)
	start, end = month_bounds(month or today())
	meters = frappe.db.sql(
		f"""select m.name, m.meter_number, m.property, m.room, r.room_number, m.rate_per_unit, m.last_reading,
			m.last_reading_date, m.is_active,
			(select mr.name from `tabPG Meter Reading` mr where mr.meter=m.name and mr.docstatus=1
				and mr.period_end between %(start)s and %(end)s limit 1) as reading_this_month
		from `tabPG Electricity Meter` m join `tabPG Room` r on r.name=m.room
		where m.property in ({sql_in(props)}) order by r.room_number""",
		{"start": start, "end": end},
		as_dict=True,
	)
	return {"data": meters}


@frappe.whitelist(methods=["GET"])
def get_summary(property: str | None = None, month: str | None = None):
	require_perm("PG Meter Reading")
	props = resolve_properties(property)
	start, end = month_bounds(month or today())
	P = sql_in(props)
	totals = frappe.db.sql(
		f"""select coalesce(sum(units_consumed),0) as units, coalesce(sum(amount),0) as amount, count(*) as readings
		from `tabPG Meter Reading` where docstatus=1 and property in ({P}) and period_end between %(s)s and %(e)s""",
		{"s": start, "e": end},
		as_dict=True,
	)[0]
	unbilled = flt(
		frappe.db.sql(
			f"""select sum(s.amount) from `tabPG Electricity Share` s join `tabPG Meter Reading` r on r.name=s.parent
			where r.docstatus=1 and r.property in ({P}) and (s.invoice is null or s.invoice='')"""
		)[0][0]
	)
	meters = frappe.db.count("PG Electricity Meter", {"property": ("in", props or [""]), "is_active": 1})
	trend = frappe.db.sql(
		f"""select date_format(period_end,'%%Y-%%m') as month, sum(units_consumed) as units, sum(amount) as amount
		from `tabPG Meter Reading` where docstatus=1 and property in ({P})
		and period_end >= date_sub(%(e)s, interval 6 month) group by 1 order by 1""",
		{"e": end},
		as_dict=True,
	)
	return {
		"data": {
			**totals,
			"unbilled_amount": unbilled,
			"active_meters": meters,
			"pending_readings": max(0, meters - totals.readings),
			"trend": trend,
		}
	}


def _new_reading(meter, current_reading, reading_date=None, period_start=None, period_end=None):
	m = frappe.get_doc("PG Electricity Meter", meter)
	m.check_permission("read")
	start = period_start or (m.last_reading_date and frappe.utils.add_days(m.last_reading_date, 1)) or month_bounds(today())[0]
	doc = frappe.get_doc(
		{
			"doctype": "PG Meter Reading",
			"meter": meter,
			"property": m.property,
			"reading_date": reading_date or today(),
			"period_start": start,
			"period_end": period_end or reading_date or today(),
			"current_reading": flt(current_reading),
		}
	)
	return doc


@frappe.whitelist(methods=["POST"])
def preview_reading(meter: str, current_reading, reading_date=None, period_start=None, period_end=None):
	require_perm("PG Meter Reading", "create")
	doc = _new_reading(meter, current_reading, reading_date, period_start, period_end)
	doc.validate()
	d = doc.as_dict(convert_dates_to_str=True)
	for s in d.get("shares", []):
		s["tenant_name"] = frappe.db.get_value("PG Tenant", s.tenant, "full_name")
	return {"data": d}


@frappe.whitelist(methods=["POST"])
def record_reading(meter: str, current_reading, reading_date=None, period_start=None, period_end=None):
	require_perm("PG Meter Reading", "create")
	doc = _new_reading(meter, current_reading, reading_date, period_start, period_end)
	doc.insert()
	doc.submit()
	return {"data": serialize(doc), "message": _("Reading recorded: {0} units").format(doc.units_consumed)}


@frappe.whitelist(methods=["GET"])
def get_bills(property: str | None = None, billing_status: str | None = None, page=1, page_size=20):
	from pg_managment_system.api.utils import page_args

	require_perm("PG Meter Reading")
	props = resolve_properties(property)
	page, page_size, start = page_args(page, page_size)
	cond = ""
	params = {"start": start, "len": page_size}
	if billing_status:
		cond = " and r.billing_status=%(bs)s"
		params["bs"] = billing_status
	base = f"from `tabPG Meter Reading` r join `tabPG Room` rm on rm.name=r.room where r.docstatus=1 and r.property in ({sql_in(props)}){cond}"
	rows = frappe.db.sql(
		f"""select r.name, r.meter, r.room, rm.room_number, r.property, r.period_start, r.period_end, r.units_consumed,
			r.amount, r.billing_status, r.reading_date {base} order by r.reading_date desc limit %(start)s, %(len)s""",
		params,
		as_dict=True,
	)
	total = frappe.db.sql(f"select count(*) {base}", params)[0][0]
	if rows:
		shares = frappe.db.sql(
			"""select s.parent, s.tenant, t.full_name as tenant_name, s.days, s.amount, s.invoice
			from `tabPG Electricity Share` s left join `tabPG Tenant` t on t.name=s.tenant
			where s.parenttype='PG Meter Reading' and s.parent in %(names)s order by s.idx""",
			{"names": [r.name for r in rows]},
			as_dict=True,
		)
		for r in rows:
			r["shares"] = [s for s in shares if s.parent == r.name]
	return {"data": rows, "total": total, "page": page, "page_size": page_size}
