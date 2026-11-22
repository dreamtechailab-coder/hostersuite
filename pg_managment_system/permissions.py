"""Property-level authorization.

Every PG document carries a ``property`` link. Users holding ``PG Admin`` /
``System Manager`` see all properties; everyone else only sees properties
assigned to them through *User Permission* (allow = PG Property).  A user with
no assignment sees nothing — this is stricter than Frappe's default (where no
user permission means "unrestricted") and is enforced here for every list
query and document access, regardless of whether the request comes from the
Vue frontend, ``/api/resource`` or Desk.
"""

import frappe
from frappe import _

ADMIN_ROLES = frozenset({"System Manager", "PG Admin"})
PG_ROLES = ("PG Admin", "PG Manager", "PG Accountant", "PG Staff")

# DocTypes whose rows are scoped by a ``property`` link field.
PROPERTY_SCOPED = (
	"PG Building",
	"PG Floor",
	"PG Room",
	"PG Bed",
	"PG Tenant",
	"PG Booking",
	"PG Occupancy",
	"PG Rent Invoice",
	"PG Electricity Meter",
	"PG Meter Reading",
	"PG Payment",
	"PG Expense",
	"PG WhatsApp Message",
)


def is_pg_admin(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	return bool(ADMIN_ROLES.intersection(frappe.get_roles(user)))


def get_allowed_properties(user: str | None = None) -> list[str] | None:
	"""Return property names the user may access, or ``None`` for unrestricted."""
	user = user or frappe.session.user
	if is_pg_admin(user):
		return None
	cache = getattr(frappe.local, "pg_allowed_properties", None)
	if cache is None:
		cache = frappe.local.pg_allowed_properties = {}
	if user not in cache:
		cache[user] = frappe.get_all(
			"User Permission",
			filters={"user": user, "allow": "PG Property"},
			pluck="for_value",
			ignore_permissions=True,
		)
	return cache[user]


def clear_cache(user: str | None = None):
	cache = getattr(frappe.local, "pg_allowed_properties", None)
	if cache is not None:
		cache.pop(user, None) if user else cache.clear()


def resolve_properties(requested: str | list | None = None, user: str | None = None) -> list[str]:
	"""Intersect the requested property filter with what the user may see.

	Always returns an explicit list (possibly empty) so callers can safely use
	it in ``IN`` clauses. Raises PermissionError if a specific property was
	requested that the user cannot access.
	"""
	allowed = get_allowed_properties(user)
	if requested:
		req = [requested] if isinstance(requested, str) else list(requested)
		if allowed is not None:
			denied = [p for p in req if p not in allowed]
			if denied:
				frappe.throw(_("You do not have access to property {0}").format(denied[0]), frappe.PermissionError)
		return req
	if allowed is None:
		return frappe.get_all("PG Property", pluck="name", ignore_permissions=True)
	return list(allowed)


def assert_property_access(property_name: str | None, user: str | None = None):
	if not property_name:
		frappe.throw(_("Property is required"))
	allowed = get_allowed_properties(user)
	if allowed is not None and property_name not in allowed:
		frappe.throw(_("You do not have access to property {0}").format(property_name), frappe.PermissionError)


def _sql_in(values: list[str]) -> str:
	return ", ".join(frappe.db.escape(v) for v in values)


def property_query_conditions(user: str | None = None, doctype: str | None = None) -> str:
	allowed = get_allowed_properties(user)
	if allowed is None:
		return ""
	if not allowed:
		return "1=0"
	column = "name" if doctype == "PG Property" else "property"
	return f"`tab{doctype}`.`{column}` in ({_sql_in(allowed)})"


def has_property_permission(doc, ptype=None, user=None, debug=False):
	allowed = get_allowed_properties(user)
	if allowed is None:
		return None  # defer to role permissions
	value = doc.name if doc.doctype == "PG Property" else doc.get("property")
	if not value:
		# new docs without property fail validation (reqd) anyway; deny reads
		return ptype == "create"
	return value in allowed or False
