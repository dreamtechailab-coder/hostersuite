"""User & role management for PG staff (PG Admin only)."""

import frappe
from frappe import _
from frappe.utils import cint

from pg_managment_system.api.utils import page_args, parse_json, require_roles
from pg_managment_system.permissions import PG_ROLES, clear_cache


@frappe.whitelist(methods=["GET"])
def list_users(search: str | None = None, page=1, page_size=20):
	require_roles("PG Admin")
	page, page_size, start = page_args(page, page_size)
	users = frappe.get_all("Has Role", filters={"role": ("in", PG_ROLES), "parenttype": "User"}, pluck="parent", distinct=True)
	filters = {"name": ("in", users or [""])}
	or_filters = [["full_name", "like", f"%{search}%"], ["email", "like", f"%{search}%"]] if search else None
	rows = frappe.get_all(
		"User",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "full_name", "email", "enabled", "last_login", "mobile_no", "user_image"],
		order_by="full_name asc",
		start=start,
		page_length=page_size,
	)
	total = len(frappe.get_all("User", filters=filters, or_filters=or_filters, pluck="name"))
	for r in rows:
		r["roles"] = [x for x in frappe.get_roles(r.name) if x in PG_ROLES]
		r["properties"] = frappe.get_all(
			"User Permission", filters={"user": r.name, "allow": "PG Property"}, pluck="for_value"
		)
	return {"data": rows, "total": total, "page": page, "page_size": page_size}


@frappe.whitelist(methods=["POST"])
def save_user(data):
	require_roles("PG Admin")
	data = parse_json(data, {})
	email = (data.get("email") or "").strip().lower()
	if not email:
		frappe.throw(_("Email is required"))
	roles = [r for r in data.get("roles") or [] if r in PG_ROLES]
	if not roles:
		frappe.throw(_("Select at least one role"))
	if email == frappe.session.user and "PG Admin" not in roles and "System Manager" not in frappe.get_roles():
		frappe.throw(_("You cannot remove your own admin role"))
	properties = data.get("properties") or []
	for p in properties:
		if not frappe.db.exists("PG Property", p):
			frappe.throw(_("Property {0} not found").format(p))

	is_new = not frappe.db.exists("User", email)
	user = frappe.new_doc("User") if is_new else frappe.get_doc("User", email)
	if is_new:
		user.email = email
		user.send_welcome_email = cint(data.get("send_welcome_email", 1))
	user.first_name = data.get("first_name") or user.first_name or email.split("@")[0]
	user.last_name = data.get("last_name")
	user.mobile_no = data.get("mobile_no")
	user.enabled = cint(data.get("enabled", 1))
	user.user_type = "System User"
	existing = [r.role for r in user.roles]
	user.set("roles", [r for r in user.roles if r.role not in PG_ROLES])
	for role in roles:
		user.append("roles", {"role": role})
	user.flags.ignore_permissions = True
	user.save() if not is_new else user.insert()

	current = frappe.get_all("User Permission", filters={"user": email, "allow": "PG Property"}, fields=["name", "for_value"])
	keep = set(properties)
	for up in current:
		if up.for_value not in keep:
			frappe.delete_doc("User Permission", up.name, ignore_permissions=True)
	have = {up.for_value for up in current}
	for p in keep - have:
		frappe.get_doc({"doctype": "User Permission", "user": email, "allow": "PG Property", "for_value": p}).insert(
			ignore_permissions=True
		)
	clear_cache(email)
	return {"data": {"name": email, "created": is_new}, "message": _("User saved")}


@frappe.whitelist(methods=["GET"])
def get_role_matrix():
	require_roles("PG Admin")
	from pg_managment_system.api.session import PG_DOCTYPES

	perms = frappe.get_all(
		"DocPerm",
		filters={"parent": ("in", PG_DOCTYPES), "role": ("in", PG_ROLES), "permlevel": 0},
		fields=["parent", "role", "read", "write", "create", "delete", "submit", "cancel"],
	)
	matrix = {}
	for p in perms:
		matrix.setdefault(p.parent, {})[p.role] = {k: bool(p[k]) for k in ("read", "write", "create", "delete", "submit", "cancel")}
	counts = {r: frappe.db.count("Has Role", {"role": r, "parenttype": "User"}) for r in PG_ROLES}
	return {"data": {"roles": PG_ROLES, "doctypes": PG_DOCTYPES, "matrix": matrix, "user_counts": counts}}
