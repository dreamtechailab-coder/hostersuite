"""Reports: occupancy, revenue, expense."""

import frappe
from frappe.utils import add_months, flt, getdate, today

from pg_managment_system.api.utils import require_perm, sql_in
from pg_managment_system.permissions import resolve_properties
from pg_managment_system.utils import month_bounds


def _range(from_date, to_date):
	if from_date and to_date:
		return getdate(from_date), getdate(to_date)
	end = month_bounds(today())[1]
	return month_bounds(add_months(end, -11))[0], end


@frappe.whitelist(methods=["GET"])
def occupancy_report(property: str | None = None, from_date: str | None = None, to_date: str | None = None):
	require_perm("PG Occupancy")
	props = resolve_properties(property)
	start, end = _range(from_date, to_date)
	P = sql_in(props)
	by_property = frappe.db.sql(
		f"""select p.name as property, p.property_name, count(b.name) as beds,
			coalesce(sum(b.status='Occupied'),0) as occupied, coalesce(sum(b.status='Reserved'),0) as reserved,
			coalesce(sum(b.status='Vacant'),0) as vacant, coalesce(sum(b.status='Maintenance'),0) as maintenance
		from `tabPG Property` p left join `tabPG Bed` b on b.property=p.name where p.name in ({P})
		group by p.name order by p.property_name""",
		as_dict=True,
	)
	for r in by_property:
		r["rate"] = round(flt(r.occupied) * 100 / r.beds, 1) if r.beds else 0
	by_room_type = frappe.db.sql(
		f"""select r.room_type, count(b.name) as beds, coalesce(sum(b.status='Occupied'),0) as occupied,
			avg(r.rent_per_bed) as avg_rent
		from `tabPG Room` r join `tabPG Bed` b on b.room=r.name where r.property in ({P}) group by r.room_type""",
		as_dict=True,
	)
	for r in by_room_type:
		r["rate"] = round(flt(r.occupied) * 100 / r.beds, 1) if r.beds else 0
	params = {"s": start, "e": end}
	movement = frappe.db.sql(
		f"""select m, sum(ins) as check_ins, sum(outs) as check_outs from (
			select date_format(check_in_date,'%%Y-%%m') as m, 1 as ins, 0 as outs from `tabPG Occupancy`
				where property in ({P}) and check_in_date between %(s)s and %(e)s
			union all
			select date_format(check_out_date,'%%Y-%%m') as m, 0, 1 from `tabPG Occupancy`
				where property in ({P}) and check_out_date between %(s)s and %(e)s
		) x group by m order by m""",
		params,
		as_dict=True,
	)
	avg_stay = flt(
		frappe.db.sql(
			f"""select avg(datediff(check_out_date, check_in_date)) from `tabPG Occupancy`
			where status='Ended' and property in ({P}) and check_out_date between %(s)s and %(e)s""",
			params,
		)[0][0]
	)
	return {
		"data": {
			"range": {"from": str(start), "to": str(end)},
			"by_property": by_property,
			"by_room_type": by_room_type,
			"movement": movement,
			"average_stay_days": round(avg_stay, 1),
		}
	}


@frappe.whitelist(methods=["GET"])
def revenue_report(property: str | None = None, from_date: str | None = None, to_date: str | None = None):
	require_perm("PG Rent Invoice")
	props = resolve_properties(property)
	start, end = _range(from_date, to_date)
	P = sql_in(props)
	params = {"s": start, "e": end}
	monthly = frappe.db.sql(
		f"""select date_format(period_start,'%%Y-%%m') as month, property, sum(total_amount) as invoiced,
			sum(paid_amount) as collected, sum(outstanding_amount) as outstanding, count(*) as invoices
		from `tabPG Rent Invoice` where docstatus=1 and property in ({P}) and period_start between %(s)s and %(e)s
		group by 1, 2 order by 1, 2""",
		params,
		as_dict=True,
	)
	by_type = frappe.db.sql(
		f"""select it.item_type as name, sum(it.amount) as value from `tabPG Invoice Item` it
		join `tabPG Rent Invoice` i on i.name=it.parent where i.docstatus=1 and i.property in ({P})
		and i.period_start between %(s)s and %(e)s group by 1 order by value desc""",
		params,
		as_dict=True,
	)
	by_mode = frappe.db.sql(
		f"""select mode as name, sum(amount) as value, count(*) as count from `tabPG Payment`
		where docstatus=1 and property in ({P}) and payment_date between %(s)s and %(e)s group by mode order by value desc""",
		params,
		as_dict=True,
	)
	keys = ("invoiced", "collected", "outstanding")
	totals = {k: sum(flt(r[k]) for r in monthly) for k in keys}
	return {"data": {"range": {"from": str(start), "to": str(end)}, "monthly": monthly, "by_type": by_type,
					 "by_mode": by_mode, "totals": totals}}


@frappe.whitelist(methods=["GET"])
def expense_report(property: str | None = None, from_date: str | None = None, to_date: str | None = None):
	require_perm("PG Expense")
	props = resolve_properties(property)
	start, end = _range(from_date, to_date)
	P = sql_in(props)
	params = {"s": start, "e": end}
	base = f"from `tabPG Expense` where property in ({P}) and expense_date between %(s)s and %(e)s"
	return {
		"data": {
			"range": {"from": str(start), "to": str(end)},
			"by_category": frappe.db.sql(
				f"select category as name, sum(amount) as value, count(*) as count {base} group by 1 order by value desc",
				params, as_dict=True),
			"monthly": frappe.db.sql(
				f"select date_format(expense_date,'%%Y-%%m') as month, sum(amount) as amount {base} group by 1 order by 1",
				params, as_dict=True),
			"by_property": frappe.db.sql(
				f"select property, sum(amount) as amount {base} group by 1 order by amount desc", params, as_dict=True),
			"top_vendors": frappe.db.sql(
				f"""select vendor as name, sum(amount) as value, count(*) as count {base} and vendor is not null and vendor != ''
				group by 1 order by value desc limit 10""",
				params, as_dict=True),
			"total": flt(frappe.db.sql(f"select sum(amount) {base}", params)[0][0]),
		}
	}
