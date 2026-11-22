"""Global search across key records (permission aware)."""

import frappe

SOURCES = (
	("PG Tenant", ["full_name", "mobile"], "full_name", "mobile", "tenant"),
	("PG Room", ["room_number"], "room_number", "property", "room"),
	("PG Property", ["property_name", "city"], "property_name", "city", "property"),
	("PG Rent Invoice", ["name", "tenant_name"], "tenant_name", "status", "invoice"),
	("PG Booking", ["name", "tenant_name"], "tenant_name", "status", "booking"),
)


@frappe.whitelist(methods=["GET"])
def global_search(q: str, limit: int = 5):
	q = (q or "").strip()
	if len(q) < 2:
		return {"data": []}
	results = []
	for doctype, fields, title, subtitle, kind in SOURCES:
		if not frappe.has_permission(doctype, "read"):
			continue
		rows = frappe.get_list(
			doctype,
			or_filters=[[f, "like", f"%{q}%"] for f in fields],
			fields=["name", f"{title} as title", f"{subtitle} as subtitle"],
			page_length=min(int(limit), 10),
		)
		results += [{"type": kind, "name": r.name, "title": r.title or r.name, "subtitle": r.subtitle} for r in rows]
	return {"data": results}
