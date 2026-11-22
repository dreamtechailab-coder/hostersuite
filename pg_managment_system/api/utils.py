"""Common helpers for the Vue-facing API.

All endpoints return JSON shaped as ``{"data": ...}`` (plus ``total``, ``page``
and ``page_size`` for lists). Errors are raised with ``frappe.throw`` which
Frappe serialises consistently (HTTP status + ``exc_type`` + ``_server_messages``).
"""

import json

import frappe
from frappe import _
from frappe.utils import cint

MAX_PAGE_SIZE = 100
FILTER_OPS = {"=", "!=", "<", ">", "<=", ">=", "like", "not like", "in", "not in", "between", "is"}


def parse_json(value, default=None):
	if value is None or value == "":
		return default
	if isinstance(value, (dict, list)):
		return value
	try:
		return json.loads(value)
	except (TypeError, ValueError):
		frappe.throw(_("Invalid JSON payload"))


def page_args(page=1, page_size=20) -> tuple[int, int, int]:
	page = max(1, cint(page) or 1)
	page_size = min(MAX_PAGE_SIZE, max(1, cint(page_size) or 20))
	return page, page_size, (page - 1) * page_size


def clean_filters(filters, allowed_fields: set[str]) -> list:
	"""Convert ``{field: value | [op, value]}`` into Frappe filters, whitelisting fields/operators."""
	filters = parse_json(filters, {}) or {}
	out = []
	items = filters.items() if isinstance(filters, dict) else [(f[0], f[1:]) for f in filters]
	for field, value in items:
		if field not in allowed_fields:
			frappe.throw(_("Filtering on {0} is not allowed").format(field))
		if value in (None, "", []):
			continue
		if isinstance(value, (list, tuple)) and len(value) == 2 and str(value[0]).lower() in FILTER_OPS:
			op, val = str(value[0]).lower(), value[1]
		else:
			op, val = "=", value
		out.append([field, op, val])
	return out


def clean_order_by(order_by: str | None, allowed_fields: set[str], default: str) -> str:
	if not order_by:
		return default
	parts = order_by.strip().split()
	field = parts[0]
	direction = parts[1].lower() if len(parts) > 1 else "asc"
	if field not in allowed_fields or direction not in ("asc", "desc"):
		return default
	return f"`{field}` {direction}"


def require_perm(doctype: str, ptype: str = "read", doc=None):
	if not frappe.has_permission(doctype, ptype, doc=doc):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def require_roles(*roles):
	from pg_managment_system.permissions import is_pg_admin

	if is_pg_admin():
		return
	if not set(roles).intersection(frappe.get_roles()):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def sql_in(values) -> str:
	values = list(values) or [""]
	return ", ".join(frappe.db.escape(v) for v in values)
