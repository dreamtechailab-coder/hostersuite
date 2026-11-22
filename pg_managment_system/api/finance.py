"""Receivables, payables and financial summary."""

import frappe
from frappe.utils import flt, getdate, today

from pg_managment_system.api.utils import require_perm, sql_in
from pg_managment_system.permissions import resolve_properties


@frappe.whitelist(methods=["GET"])
def get_receivables(property: str | None = None, search: str | None = None):
	require_perm("PG Rent Invoice")
	props = resolve_properties(property)
	params = {"today": today(), "search": f"%{search}%" if search else None}
	cond = " and i.tenant_name like %(search)s" if search else ""
	rows = frappe.db.sql(
		f"""select i.tenant, i.tenant_name, i.property, t.mobile, t.status as tenant_status,
			count(*) as invoices, sum(i.outstanding_amount) as outstanding,
			sum(case when datediff(%(today)s, i.due_date) <= 0 then i.outstanding_amount else 0 end) as current_due,
			sum(case when datediff(%(today)s, i.due_date) between 1 and 30 then i.outstanding_amount else 0 end) as d1_30,
			sum(case when datediff(%(today)s, i.due_date) between 31 and 60 then i.outstanding_amount else 0 end) as d31_60,
			sum(case when datediff(%(today)s, i.due_date) between 61 and 90 then i.outstanding_amount else 0 end) as d61_90,
			sum(case when datediff(%(today)s, i.due_date) > 90 then i.outstanding_amount else 0 end) as d90_plus,
			min(i.due_date) as oldest_due
		from `tabPG Rent Invoice` i join `tabPG Tenant` t on t.name=i.tenant
		where i.docstatus=1 and i.outstanding_amount > 0 and i.property in ({sql_in(props)}){cond}
		group by i.tenant, i.tenant_name, i.property, t.mobile, t.status order by outstanding desc""",
		params,
		as_dict=True,
	)
	keys = ("outstanding", "current_due", "d1_30", "d31_60", "d61_90", "d90_plus")
	totals = {k: sum(flt(r[k]) for r in rows) for k in keys}
	return {"data": {"rows": rows, "totals": totals}}


@frappe.whitelist(methods=["GET"])
def get_payables(property: str | None = None):
	require_perm("PG Expense")
	props = resolve_properties(property)
	P = sql_in(props)
	expenses = frappe.db.sql(
		f"""select name, property, category, vendor, amount, expense_date, due_date, description
		from `tabPG Expense` where payment_status='Unpaid' and property in ({P}) order by due_date asc""",
		as_dict=True,
	)
	deposits_due = frappe.db.sql(
		f"""select name, tenant, tenant_name, property, check_out_date, security_deposit, deposit_refund_amount
		from `tabPG Occupancy` where status='Ended' and deposit_status='Held' and security_deposit > 0
		and property in ({P}) order by check_out_date""",
		as_dict=True,
	)
	deposits_held = flt(
		frappe.db.sql(
			f"""select sum(security_deposit) from `tabPG Occupancy` where status!='Ended' and deposit_status='Held'
			and property in ({P})"""
		)[0][0]
	)
	t = getdate(today())
	return {
		"data": {
			"expenses": expenses,
			"deposits_due": deposits_due,
			"totals": {
				"unpaid_expenses": sum(flt(e.amount) for e in expenses),
				"overdue_expenses": sum(flt(e.amount) for e in expenses if e.due_date and getdate(e.due_date) < t),
				"deposits_to_refund": sum(flt(d.security_deposit) for d in deposits_due),
				"deposits_held": deposits_held,
			},
		}
	}


@frappe.whitelist(methods=["GET"])
def get_financial_summary(property: str | None = None, year: int | None = None):
	require_perm("PG Rent Invoice")
	require_perm("PG Expense")
	props = resolve_properties(property)
	year = int(year or getdate(today()).year)
	P = sql_in(props)
	params = {"y": year}
	invoiced = dict(
		frappe.db.sql(
			f"""select month(period_start), sum(total_amount) from `tabPG Rent Invoice`
			where docstatus=1 and year(period_start)=%(y)s and property in ({P}) group by 1""",
			params,
		)
	)
	collected = dict(
		frappe.db.sql(
			f"""select month(payment_date), sum(amount) from `tabPG Payment`
			where docstatus=1 and year(payment_date)=%(y)s and property in ({P}) group by 1""",
			params,
		)
	)
	expenses = dict(
		frappe.db.sql(
			f"""select month(expense_date), sum(amount) from `tabPG Expense`
			where year(expense_date)=%(y)s and property in ({P}) group by 1""",
			params,
		)
	)
	months = []
	for m in range(1, 13):
		inc, exp = flt(collected.get(m)), flt(expenses.get(m))
		months.append({"month": m, "invoiced": flt(invoiced.get(m)), "collected": inc, "expenses": exp, "net": inc - exp})
	income_by_type = frappe.db.sql(
		f"""select it.item_type as name, sum(it.amount) as value from `tabPG Invoice Item` it
		join `tabPG Rent Invoice` i on i.name=it.parent where i.docstatus=1 and year(i.period_start)=%(y)s
		and i.property in ({P}) group by it.item_type order by value desc""",
		params,
		as_dict=True,
	)
	expense_by_category = frappe.db.sql(
		f"""select category as name, sum(amount) as value from `tabPG Expense`
		where year(expense_date)=%(y)s and property in ({P}) group by category order by value desc""",
		params,
		as_dict=True,
	)
	totals = {k: sum(m[k] for m in months) for k in ("invoiced", "collected", "expenses", "net")}
	return {
		"data": {"year": year, "months": months, "totals": totals, "income_by_type": income_by_type,
				 "expense_by_category": expense_by_category}
	}
