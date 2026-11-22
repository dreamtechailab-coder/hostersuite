"""Executive dashboard aggregation (single round-trip for the dashboard page)."""

from datetime import date

import frappe
from frappe.utils import add_days, add_months, flt, getdate, today

from pg_managment_system.api.utils import sql_in
from pg_managment_system.permissions import resolve_properties
from pg_managment_system.utils import month_bounds


def _range(from_date, to_date):
	if from_date and to_date:
		return getdate(from_date), getdate(to_date)
	return month_bounds(today())


def _sum(sql: str, params: dict) -> float:
	return flt(frappe.db.sql(sql, params)[0][0])


@frappe.whitelist(methods=["GET"])
def get_dashboard(property: str | None = None, from_date: str | None = None, to_date: str | None = None):
	props = resolve_properties(property)
	start, end = _range(from_date, to_date)
	can_finance = bool(frappe.has_permission("PG Rent Invoice", "read"))
	P = sql_in(props)
	params = {"start": start, "end": end, "today": today()}

	beds = dict(frappe.db.sql(f"select status, count(*) from `tabPG Bed` where property in ({P}) group by status"))
	total_beds = sum(beds.values())
	occupied = beds.get("Occupied", 0)
	rooms = dict(frappe.db.sql(f"select status, count(*) from `tabPG Room` where property in ({P}) group by status"))
	active_tenants = frappe.db.sql(
		f"select count(*) from `tabPG Occupancy` where property in ({P}) and status != 'Ended'"
	)[0][0]
	on_notice = frappe.db.sql(
		f"select count(*) from `tabPG Occupancy` where property in ({P}) and status = 'On Notice'"
	)[0][0]
	check_ins = frappe.db.sql(
		f"select count(*) from `tabPG Occupancy` where property in ({P}) and check_in_date between %(start)s and %(end)s",
		params,
	)[0][0]
	pending_bookings = frappe.db.sql(
		f"select count(*) from `tabPG Booking` where property in ({P}) and status in ('Pending','Confirmed')"
	)[0][0]

	data = {
		"range": {"from": str(start), "to": str(end)},
		"occupancy": {
			"total_beds": total_beds,
			"occupied": occupied,
			"reserved": beds.get("Reserved", 0),
			"vacant": beds.get("Vacant", 0),
			"maintenance": beds.get("Maintenance", 0),
			"rate": round(occupied * 100 / total_beds, 1) if total_beds else 0,
			"rooms": rooms,
			"active_tenants": active_tenants,
			"on_notice": on_notice,
			"check_ins": check_ins,
			"pending_bookings": pending_bookings,
		},
		"can_finance": can_finance,
	}

	data["property_comparison"] = frappe.db.sql(
		f"""select p.name as property, p.property_name,
			coalesce(sum(b.status='Occupied'),0) as occupied, count(b.name) as beds,
			coalesce(sum(b.status='Vacant'),0) as vacant
		from `tabPG Property` p left join `tabPG Bed` b on b.property = p.name
		where p.name in ({P}) group by p.name order by p.property_name""",
		as_dict=True,
	)

	if not can_finance:
		return {"data": data}

	invoiced = _sum(
		f"""select sum(total_amount) from `tabPG Rent Invoice` where docstatus=1 and property in ({P})
		and period_start between %(start)s and %(end)s""",
		params,
	)
	invoiced_paid = _sum(
		f"""select sum(paid_amount) from `tabPG Rent Invoice` where docstatus=1 and property in ({P})
		and period_start between %(start)s and %(end)s""",
		params,
	)
	collected = _sum(
		f"""select sum(amount) from `tabPG Payment` where docstatus=1 and property in ({P})
		and payment_date between %(start)s and %(end)s""",
		params,
	)
	outstanding = _sum(
		f"select sum(outstanding_amount) from `tabPG Rent Invoice` where docstatus=1 and property in ({P})", params
	)
	overdue = _sum(
		f"""select sum(outstanding_amount) from `tabPG Rent Invoice` where docstatus=1 and property in ({P})
		and outstanding_amount > 0 and due_date < %(today)s""",
		params,
	)
	expenses = _sum(
		f"""select sum(amount) from `tabPG Expense` where property in ({P})
		and expense_date between %(start)s and %(end)s""",
		params,
	)
	unpaid_expenses = _sum(
		f"select sum(amount) from `tabPG Expense` where property in ({P}) and payment_status='Unpaid'", params
	)
	data["finance"] = {
		"invoiced": invoiced,
		"collected": collected,
		"collection_rate": round(invoiced_paid * 100 / invoiced, 1) if invoiced else 0,
		"outstanding": outstanding,
		"overdue": overdue,
		"expenses": expenses,
		"unpaid_expenses": unpaid_expenses,
		"net": collected - expenses,
	}

	# 12-month trend ending at the selected end date
	trend_end = month_bounds(end)[1]
	trend_start = month_bounds(add_months(trend_end, -11))[0]
	tparams = {"start": trend_start, "end": trend_end}
	rows = {
		"invoiced": frappe.db.sql(
			f"""select date_format(period_start,'%%Y-%%m'), sum(total_amount) from `tabPG Rent Invoice`
			where docstatus=1 and property in ({P}) and period_start between %(start)s and %(end)s group by 1""",
			tparams,
		),
		"collected": frappe.db.sql(
			f"""select date_format(payment_date,'%%Y-%%m'), sum(amount) from `tabPG Payment`
			where docstatus=1 and property in ({P}) and payment_date between %(start)s and %(end)s group by 1""",
			tparams,
		),
		"expenses": frappe.db.sql(
			f"""select date_format(expense_date,'%%Y-%%m'), sum(amount) from `tabPG Expense`
			where property in ({P}) and expense_date between %(start)s and %(end)s group by 1""",
			tparams,
		),
	}
	months = []
	cursor = date(trend_start.year, trend_start.month, 1)
	while cursor <= trend_end:
		months.append(cursor.strftime("%Y-%m"))
		cursor = add_months(cursor, 1)
	maps = {k: {m: flt(v) for m, v in r} for k, r in rows.items()}
	data["trend"] = {"months": months, **{k: [maps[k].get(m, 0) for m in months] for k in maps}}

	revenue_by_prop = dict(
		frappe.db.sql(
			f"""select property, sum(amount) from `tabPG Payment` where docstatus=1 and property in ({P})
			and payment_date between %(start)s and %(end)s group by property""",
			params,
		)
	)
	for row in data["property_comparison"]:
		row["collected"] = flt(revenue_by_prop.get(row.property))

	data["expense_by_category"] = frappe.db.sql(
		f"""select category as name, sum(amount) as value from `tabPG Expense`
		where property in ({P}) and expense_date between %(start)s and %(end)s group by category order by value desc""",
		params,
		as_dict=True,
	)

	data["recent_transactions"] = frappe.db.sql(
		f"""(select 'Payment' as type, name, tenant_name as party, payment_date as date, amount, mode as detail, creation
			from `tabPG Payment` where docstatus=1 and property in ({P}))
		union all
		(select 'Expense' as type, name, coalesce(vendor, category) as party, expense_date as date, amount, category as detail, creation
			from `tabPG Expense` where property in ({P}))
		order by date desc, creation desc limit 8""",
		as_dict=True,
	)
	data["upcoming_dues"] = frappe.db.sql(
		f"""select name, tenant, tenant_name, room, due_date, outstanding_amount, status
		from `tabPG Rent Invoice` where docstatus=1 and property in ({P}) and outstanding_amount > 0
		and due_date <= %(horizon)s order by due_date asc limit 8""",
		{"horizon": add_days(today(), 7)},
		as_dict=True,
	)
	return {"data": data}
