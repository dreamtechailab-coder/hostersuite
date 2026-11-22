"""Generic, allow-listed CRUD for the Vue frontend.

Only DocTypes in ``REGISTRY`` are reachable. For each one we define which
fields may be listed / filtered, which fields the client may *write*
(system-computed fields such as status, paid_amount, outstanding etc. are never
writable from the client) and an optional serializer used to strip/mask data
(e.g. identity numbers). Role permissions and property scoping are enforced by
Frappe (``frappe.get_list`` / ``doc.check_permission``) plus the hooks in
``pg_managment_system.permissions``.
"""

import frappe
from frappe import _

from pg_managment_system.api.utils import clean_filters, clean_order_by, page_args, parse_json
from pg_managment_system.utils import mask_id

STD = ["name", "creation", "modified"]


def _tenant_serializer(d: dict, doc=None) -> dict:
	d["id_number_masked"] = mask_id(d.pop("id_number", None) or (doc.get("id_number") if doc else None))
	d["has_id_document"] = bool(d.pop("id_document", None))
	return d


REGISTRY: dict[str, dict] = {
	"PG Property": {
		"list": ["property_name", "property_code", "property_type", "city", "state", "is_active", "phone",
				 "manager", "total_beds", "occupied_beds"],
		"search": ["property_name", "city", "property_code"],
		"write": ["property_name", "property_code", "property_type", "is_active", "manager", "phone", "email",
				  "address_line", "city", "state", "pincode", "amenities", "notes"],
		"order": "property_name asc",
	},
	"PG Building": {
		"list": ["property", "building_name", "is_active", "address_line"],
		"search": ["building_name"],
		"write": ["property", "building_name", "is_active", "address_line", "notes"],
		"order": "building_name asc",
	},
	"PG Floor": {
		"list": ["property", "building", "floor_name", "floor_number"],
		"search": ["floor_name"],
		"write": ["property", "building", "floor_name", "floor_number"],
		"order": "floor_number asc",
	},
	"PG Room": {
		"list": ["property", "building", "floor", "room_number", "room_type", "capacity", "occupied_beds",
				 "rent_per_bed", "security_deposit", "status", "is_ac", "attached_bathroom"],
		"search": ["room_number"],
		"write": ["property", "building", "floor", "room_number", "room_type", "capacity", "rent_per_bed",
				  "security_deposit", "is_ac", "attached_bathroom", "amenities", "status"],
		"order": "room_number asc",
	},
	"PG Bed": {
		"list": ["property", "room", "bed_label", "status", "current_tenant", "current_occupancy", "reserved_booking"],
		"search": ["bed_label"],
		"write": ["status"],  # only Vacant <-> Maintenance; other transitions happen via workflows
		"order": "bed_label asc",
	},
	"PG Tenant": {
		"list": ["full_name", "mobile", "email", "gender", "property", "status", "occupation", "organization",
				 "photo", "kyc_verified", "whatsapp_opt_in"],
		"search": ["full_name", "mobile", "email"],
		"write": ["full_name", "mobile", "email", "gender", "property", "date_of_birth", "photo", "occupation",
				  "organization", "permanent_address", "id_type", "id_number", "id_document", "kyc_verified",
				  "emergency_contact_name", "emergency_contact_phone", "whatsapp_opt_in", "notes"],
		"serializer": _tenant_serializer,
		# fetched only to be masked by the serializer; deliberately NOT filterable/searchable
		"hidden_fetch": ["id_number", "id_document"],
		"order": "full_name asc",
	},
	"PG Booking": {
		"list": ["tenant", "tenant_name", "property", "room", "bed", "booking_date", "expected_check_in",
				 "advance_amount", "status", "occupancy"],
		"search": ["tenant_name", "name"],
		"write": ["tenant", "property", "room", "bed", "booking_date", "expected_check_in", "advance_amount", "notes"],
		"order": "creation desc",
	},
	"PG Occupancy": {
		"list": ["tenant", "tenant_name", "property", "room", "bed", "status", "check_in_date", "notice_date",
				 "expected_check_out", "check_out_date", "monthly_rent", "security_deposit", "deposit_status", "rent_due_day"],
		"search": ["tenant_name", "name"],
		"write": ["monthly_rent", "rent_due_day", "security_deposit", "expected_check_out"],
		"order": "check_in_date desc",
	},
	"PG Rent Invoice": {
		"list": ["tenant", "tenant_name", "property", "room", "occupancy", "invoice_date", "period_start",
				 "period_end", "due_date", "total_amount", "paid_amount", "outstanding_amount", "status", "docstatus"],
		"search": ["tenant_name", "name"],
		"write": ["tenant", "occupancy", "invoice_date", "period_start", "period_end", "due_date", "items"],
		"children": {"items": ["item_type", "description", "amount"]},
		"order": "invoice_date desc",
	},
	"PG Electricity Meter": {
		"list": ["property", "room", "meter_number", "rate_per_unit", "last_reading", "last_reading_date", "is_active"],
		"search": ["meter_number"],
		"write": ["property", "room", "meter_number", "rate_per_unit", "initial_reading", "is_active"],
		"order": "meter_number asc",
	},
	"PG Meter Reading": {
		"list": ["meter", "property", "room", "reading_date", "period_start", "period_end", "previous_reading",
				 "current_reading", "units_consumed", "rate_per_unit", "amount", "billing_status", "docstatus"],
		"search": ["meter", "name"],
		"write": ["meter", "reading_date", "period_start", "period_end", "current_reading"],
		"order": "reading_date desc",
	},
	"PG Payment": {
		"list": ["tenant", "tenant_name", "property", "payment_date", "amount", "mode", "reference_no",
				 "allocated_amount", "unallocated_amount", "received_by", "docstatus"],
		"search": ["tenant_name", "reference_no", "name"],
		"write": [],  # payments are created only through api.payment.collect_payment
		"order": "payment_date desc",
	},
	"PG Expense Category": {
		"list": ["category_name", "description"],
		"search": ["category_name"],
		"write": ["category_name", "description"],
		"order": "category_name asc",
	},
	"PG Expense": {
		"list": ["property", "category", "expense_date", "amount", "vendor", "payment_status", "due_date",
				 "paid_on", "payment_mode", "description", "attachment"],
		"search": ["vendor", "description", "category"],
		"write": ["property", "category", "expense_date", "amount", "vendor", "payment_status", "due_date",
				  "paid_on", "payment_mode", "description", "attachment"],
		"order": "expense_date desc",
	},
	"PG WhatsApp Template": {
		"list": ["template_name", "purpose", "enabled", "meta_template_name", "language_code", "body"],
		"search": ["template_name"],
		"write": ["template_name", "purpose", "enabled", "meta_template_name", "language_code", "body"],
		"order": "template_name asc",
	},
	"PG WhatsApp Message": {
		"list": ["tenant", "property", "mobile", "template", "status", "sent_at", "message", "error",
				 "reference_doctype", "reference_name"],
		"search": ["mobile", "message"],
		"write": [],
		"order": "creation desc",
	},
}


def _config(doctype: str) -> dict:
	cfg = REGISTRY.get(doctype)
	if not cfg:
		frappe.throw(_("Resource {0} is not available").format(doctype), frappe.PermissionError)
	return cfg


def serialize(doc, cfg: dict | None = None) -> dict:
	cfg = cfg or _config(doc.doctype)
	doc.apply_fieldlevel_read_permissions()
	d = doc.as_dict(no_default_fields=False, convert_dates_to_str=True)
	for key in ("_user_tags", "_comments", "_assign", "_liked_by", "_seen", "doctype"):
		d.pop(key, None)
	for child in doc.meta.get_table_fields():
		d[child.fieldname] = [
			{k: v for k, v in row.items() if k not in ("parent", "parenttype", "parentfield", "doctype", "owner", "modified_by")}
			for row in d.get(child.fieldname) or []
		]
	if cfg.get("serializer"):
		d = cfg["serializer"](d, doc)
	return d


@frappe.whitelist(methods=["GET"])
def get_list(doctype: str, filters=None, search: str | None = None, page=1, page_size=20, order_by: str | None = None):
	cfg = _config(doctype)
	fields = set(STD + cfg["list"] + ["docstatus"])
	flt = clean_filters(filters, fields)
	page, page_size, start = page_args(page, page_size)
	or_filters = [[f, "like", f"%{search.strip()}%"] for f in cfg["search"]] if search and search.strip() else None
	order = clean_order_by(order_by, fields, cfg.get("order", "modified desc"))

	rows = frappe.get_list(
		doctype,
		filters=flt,
		or_filters=or_filters,
		fields=[f for f in STD + cfg["list"] if f in fields] + cfg.get("hidden_fetch", []),
		order_by=order,
		start=start,
		page_length=page_size,
	)
	total = frappe.get_list(
		doctype, filters=flt, or_filters=or_filters, fields=[f"count(`tab{doctype}`.`name`) as total"], as_list=True
	)[0][0]
	if cfg.get("serializer"):
		rows = [cfg["serializer"](dict(r)) for r in rows]
	return {"data": rows, "total": total, "page": page, "page_size": page_size}


@frappe.whitelist(methods=["GET"])
def get_doc(doctype: str, name: str):
	cfg = _config(doctype)
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	return {"data": serialize(doc, cfg)}


def _apply(doc, data: dict, cfg: dict):
	writable = set(cfg["write"])
	for key, value in data.items():
		if key not in writable:
			continue
		if key in cfg.get("children", {}):
			allowed = set(cfg["children"][key])
			doc.set(key, [])
			for row in value or []:
				doc.append(key, {k: v for k, v in row.items() if k in allowed})
		else:
			doc.set(key, value)


@frappe.whitelist(methods=["POST"])
def save_doc(doctype: str, data):
	cfg = _config(doctype)
	data = parse_json(data, {})
	if not cfg["write"]:
		frappe.throw(_("{0} cannot be edited directly").format(doctype), frappe.PermissionError)
	name = data.get("name")
	if name:
		doc = frappe.get_doc(doctype, name)
		doc.check_permission("write")
		if data.get("modified") and str(doc.modified) != str(data["modified"]):
			frappe.throw(_("This record was modified by someone else. Reload and try again."), frappe.TimestampMismatchError)
		if doctype == "PG Bed" and data.get("status") not in ("Vacant", "Maintenance"):
			frappe.throw(_("Beds can only be set to Vacant or Maintenance manually"))
		_apply(doc, data, cfg)
		doc.save()
	else:
		doc = frappe.new_doc(doctype)
		_apply(doc, data, cfg)
		doc.insert()
	return {"data": serialize(doc, cfg), "message": _("Saved")}


@frappe.whitelist(methods=["POST"])
def delete_doc(doctype: str, name: str):
	_config(doctype)
	frappe.delete_doc(doctype, name)  # permission checked by frappe
	return {"data": {"name": name}, "message": _("Deleted")}


@frappe.whitelist(methods=["POST"])
def submit_doc(doctype: str, name: str):
	cfg = _config(doctype)
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("submit")
	doc.submit()
	return {"data": serialize(doc, cfg), "message": _("Submitted")}


@frappe.whitelist(methods=["POST"])
def cancel_doc(doctype: str, name: str):
	cfg = _config(doctype)
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("cancel")
	doc.cancel()
	return {"data": serialize(doc, cfg), "message": _("Cancelled")}


@frappe.whitelist(methods=["GET"])
def get_options(doctype: str, filters=None, search: str | None = None, limit=20):
	"""Lightweight [{value, label}] list for selects/comboboxes."""
	cfg = _config(doctype)
	meta = frappe.get_meta(doctype)
	title = meta.title_field or "name"
	fields = set(STD + cfg["list"])
	flt = clean_filters(filters, fields)
	or_filters = [[f, "like", f"%{search.strip()}%"] for f in cfg["search"] + ["name"]] if search else None
	rows = frappe.get_list(
		doctype,
		filters=flt,
		or_filters=or_filters,
		fields=["name", f"{title} as label"] + (["mobile"] if doctype == "PG Tenant" else []),
		order_by=cfg.get("order", "modified desc"),
		page_length=min(int(limit or 20), 200),
	)
	return {"data": [{"value": r.name, "label": r.label or r.name, **({"hint": r.mobile} if r.get("mobile") else {})} for r in rows]}
