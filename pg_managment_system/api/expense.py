"""Expenses."""

import frappe
from frappe import _
from frappe.utils import today

from pg_managment_system.api.resource import serialize
from pg_managment_system.api.utils import require_perm, sql_in
from pg_managment_system.permissions import resolve_properties
from pg_managment_system.utils import month_bounds


@frappe.whitelist(methods=["POST"])
def mark_paid(name: str, paid_on: str | None = None, payment_mode: str | None = None):
	doc = frappe.get_doc("PG Expense", name)
	doc.check_permission("write")
	doc.payment_status = "Paid"
	doc.paid_on = paid_on or today()
	doc.payment_mode = payment_mode or doc.payment_mode
	doc.save()
	return {"data": serialize(doc), "message": _("Expense marked as paid")}


@frappe.whitelist(methods=["GET"])
def get_summary(property: str | None = None, from_date: str | None = None, to_date: str | None = None):
	require_perm("PG Expense")
	props = resolve_properties(property)
	start, end = (from_date, to_date) if from_date and to_date else month_bounds(today())
	P = sql_in(props)
	params = {"s": start, "e": end}
	by_category = frappe.db.sql(
		f"""select category as name, sum(amount) as value, count(*) as count from `tabPG Expense`
		where property in ({P}) and expense_date between %(s)s and %(e)s group by category order by value desc""",
		params,
		as_dict=True,
	)
	totals = frappe.db.sql(
		f"""select coalesce(sum(amount),0) as total,
			coalesce(sum(case when payment_status='Unpaid' then amount end),0) as unpaid,
			count(*) as count
		from `tabPG Expense` where property in ({P}) and expense_date between %(s)s and %(e)s""",
		params,
		as_dict=True,
	)[0]
	return {"data": {"totals": totals, "by_category": by_category, "range": {"from": str(start), "to": str(end)}}}
