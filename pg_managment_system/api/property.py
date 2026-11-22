"""Property hierarchy, room board and room details."""

import frappe
from frappe import _

from pg_managment_system.api.resource import serialize
from pg_managment_system.api.utils import require_perm
from pg_managment_system.permissions import assert_property_access, resolve_properties


@frappe.whitelist(methods=["GET"])
def get_property_overview(name: str):
	doc = frappe.get_doc("PG Property", name)
	doc.check_permission("read")
	buildings = frappe.get_all(
		"PG Building", filters={"property": name}, fields=["name", "building_name", "is_active"], order_by="building_name"
	)
	floors = frappe.get_all(
		"PG Floor", filters={"property": name}, fields=["name", "building", "floor_name", "floor_number"], order_by="floor_number"
	)
	room_stats = frappe.db.sql(
		"""select building, floor, count(*) as rooms, sum(capacity) as beds, sum(occupied_beds) as occupied
		from `tabPG Room` where property=%s group by building, floor""",
		name,
		as_dict=True,
	)
	stats = {(r.building, r.floor): r for r in room_stats}
	for f in floors:
		s = stats.get((f.building, f.name)) or {}
		f.update(rooms=s.get("rooms", 0), beds=s.get("beds", 0) or 0, occupied=s.get("occupied", 0) or 0)
	for b in buildings:
		bf = [f for f in floors if f.building == b.name]
		b.update(
			floors=bf,
			rooms=sum(f["rooms"] for f in bf),
			beds=sum(f["beds"] for f in bf),
			occupied=sum(f["occupied"] for f in bf),
		)
	beds = dict(frappe.db.sql("select status, count(*) from `tabPG Bed` where property=%s group by status", name))
	tenants = frappe.db.count("PG Occupancy", {"property": name, "status": ("!=", "Ended")})
	return {
		"data": {
			"property": serialize(doc),
			"buildings": buildings,
			"beds": beds,
			"active_tenants": tenants,
		}
	}


@frappe.whitelist(methods=["GET"])
def get_hierarchy(property: str):
	assert_property_access(property)
	require_perm("PG Building")
	return {
		"data": {
			"buildings": frappe.get_list("PG Building", filters={"property": property}, fields=["name", "building_name"], order_by="building_name"),
			"floors": frappe.get_list(
				"PG Floor", filters={"property": property}, fields=["name", "building", "floor_name"], order_by="floor_number"
			),
		}
	}


@frappe.whitelist(methods=["GET"])
def get_room_board(property: str | None = None, building: str | None = None, floor: str | None = None,
				   status: str | None = None, search: str | None = None, vacant_only: int = 0):
	"""Rooms with their beds and occupants for the visual board / bed allocation."""
	require_perm("PG Room")
	props = resolve_properties(property)
	filters = {"property": ("in", props or [""])}
	if building:
		filters["building"] = building
	if floor:
		filters["floor"] = floor
	if status:
		filters["status"] = status
	if search:
		filters["room_number"] = ("like", f"%{search}%")
	rooms = frappe.get_list(
		"PG Room",
		filters=filters,
		fields=["name", "property", "building", "floor", "room_number", "room_type", "capacity", "occupied_beds",
				"rent_per_bed", "security_deposit", "status", "is_ac", "attached_bathroom"],
		order_by="building asc, floor asc, room_number asc",
		page_length=500,
	)
	if not rooms:
		return {"data": []}
	names = [r.name for r in rooms]
	beds = frappe.db.sql(
		"""select b.name, b.room, b.bed_label, b.status, b.current_tenant, b.current_occupancy, b.reserved_booking,
			t.full_name as tenant_name, t.mobile as tenant_mobile, bk.tenant_name as reserved_for
		from `tabPG Bed` b
		left join `tabPG Tenant` t on t.name = b.current_tenant
		left join `tabPG Booking` bk on bk.name = b.reserved_booking
		where b.room in %(rooms)s order by b.bed_label""",
		{"rooms": names},
		as_dict=True,
	)
	labels = {
		"building": dict(frappe.get_all("PG Building", filters={"name": ("in", list({r.building for r in rooms}))}, fields=["name", "building_name"], as_list=True)),
		"floor": dict(frappe.get_all("PG Floor", filters={"name": ("in", list({r.floor for r in rooms}))}, fields=["name", "floor_name"], as_list=True)),
	}
	by_room = {}
	for b in beds:
		by_room.setdefault(b.room, []).append(b)
	out = []
	for r in rooms:
		r["beds"] = by_room.get(r.name, [])
		r["building_name"] = labels["building"].get(r.building)
		r["floor_name"] = labels["floor"].get(r.floor)
		if int(vacant_only or 0) and not any(b.status == "Vacant" for b in r["beds"]):
			continue
		out.append(r)
	return {"data": out}


@frappe.whitelist(methods=["GET"])
def get_room_details(name: str):
	room = frappe.get_doc("PG Room", name)
	room.check_permission("read")
	board = get_room_board(property=room.property, search=None)["data"]
	beds = next((r["beds"] for r in board if r["name"] == name), [])
	occupants = frappe.get_list(
		"PG Occupancy",
		filters={"room": name},
		fields=["name", "tenant", "tenant_name", "bed", "status", "check_in_date", "check_out_date", "monthly_rent"],
		order_by="check_in_date desc",
		page_length=20,
	)
	meters = frappe.get_list(
		"PG Electricity Meter", filters={"room": name}, fields=["name", "meter_number", "rate_per_unit", "last_reading", "last_reading_date", "is_active"]
	)
	readings = []
	if frappe.has_permission("PG Meter Reading", "read"):
		readings = frappe.get_list(
			"PG Meter Reading",
			filters={"room": name, "docstatus": 1},
			fields=["name", "reading_date", "units_consumed", "amount", "billing_status"],
			order_by="reading_date desc",
			page_length=6,
		)
	return {
		"data": {
			"room": serialize(room),
			"building_name": frappe.db.get_value("PG Building", room.building, "building_name"),
			"floor_name": frappe.db.get_value("PG Floor", room.floor, "floor_name"),
			"beds": beds,
			"occupancies": occupants,
			"meters": meters,
			"readings": readings,
		}
	}


@frappe.whitelist(methods=["POST"])
def set_bed_status(bed: str, status: str):
	if status not in ("Vacant", "Maintenance"):
		frappe.throw(_("Beds can only be set to Vacant or Maintenance manually"))
	doc = frappe.get_doc("PG Bed", bed)
	doc.check_permission("write")
	if doc.status in ("Occupied", "Reserved"):
		frappe.throw(_("Bed is {0}; check the tenant out or cancel the booking first").format(doc.status.lower()))
	doc.status = status
	doc.save()
	from pg_managment_system.utils import update_room_occupancy

	update_room_occupancy(doc.room)
	return {"data": serialize(doc), "message": _("Bed updated")}
