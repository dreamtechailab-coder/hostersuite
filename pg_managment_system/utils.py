"""Shared helpers for PG controllers and services."""

import re
from calendar import monthrange
from datetime import date

import frappe
from frappe import _
from frappe.utils import flt, getdate


def get_settings():
	return frappe.get_cached_doc("PG Settings")


def money(value) -> float:
	return flt(value, 2)


def month_bounds(day) -> tuple[date, date]:
	d = getdate(day)
	return date(d.year, d.month, 1), date(d.year, d.month, monthrange(d.year, d.month)[1])


def clamp_day(year: int, month: int, day: int) -> date:
	return date(year, month, max(1, min(int(day or 1), monthrange(year, month)[1])))


def overlap_days(a_start, a_end, b_start, b_end) -> int:
	start = max(getdate(a_start), getdate(b_start))
	end = min(getdate(a_end), getdate(b_end))
	return max(0, (end - start).days + 1)


def normalize_mobile(mobile: str | None) -> str:
	digits = re.sub(r"\D", "", mobile or "")
	if len(digits) < 10 or len(digits) > 15:
		frappe.throw(_("Enter a valid mobile number (10-15 digits)"))
	return digits


def mask_id(value: str | None) -> str | None:
	"""Mask identity numbers (Aadhaar etc.) leaving only the last 4 characters."""
	if not value:
		return None
	value = re.sub(r"\s", "", value)
	return "XXXX-XXXX-" + value[-4:] if len(value) > 4 else "XXXX"


def bed_labels(count: int, start: int = 0) -> list[str]:
	labels = []
	for i in range(start, start + count):
		labels.append(chr(ord("A") + i) if i < 26 else f"B{i + 1}")
	return labels


def update_room_occupancy(room: str):
	"""Recompute occupied-bed counters and status on a room and its property."""
	if not room:
		return
	counts = frappe.db.sql(
		"""select status, count(*) from `tabPG Bed` where room=%s group by status""", room
	)
	counts = dict(counts)
	occupied = counts.get("Occupied", 0)
	capacity, status, prop = frappe.db.get_value("PG Room", room, ["capacity", "status", "property"])
	if status != "Maintenance":
		status = "Full" if occupied + counts.get("Reserved", 0) >= (capacity or 0) else "Available"
	frappe.db.set_value("PG Room", room, {"occupied_beds": occupied, "status": status}, update_modified=False)
	update_property_counts(prop)


def update_property_counts(prop: str):
	if not prop:
		return
	total = frappe.db.count("PG Bed", {"property": prop})
	occupied = frappe.db.count("PG Bed", {"property": prop, "status": "Occupied"})
	frappe.db.set_value(
		"PG Property", prop, {"total_beds": total, "occupied_beds": occupied}, update_modified=False
	)


def ensure_same_property(doc, link_doctype: str, link_name: str | None, label: str):
	if not link_name:
		return
	prop = frappe.db.get_value(link_doctype, link_name, "property")
	if prop is None:
		frappe.throw(_("{0} {1} does not exist").format(label, link_name))
	if prop != doc.property:
		frappe.throw(_("{0} {1} does not belong to property {2}").format(label, link_name, doc.property))
