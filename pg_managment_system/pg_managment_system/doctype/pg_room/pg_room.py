# Copyright (c) 2026, Maharajan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from pg_managment_system.utils import bed_labels, ensure_same_property, update_room_occupancy


class PGRoom(Document):
	def validate(self):
		ensure_same_property(self, "PG Building", self.building, "Building")
		if frappe.db.get_value("PG Floor", self.floor, "building") != self.building:
			frappe.throw(_("Floor {0} is not in building {1}").format(self.floor, self.building))
		if self.capacity < 1 or self.capacity > 50:
			frappe.throw(_("Beds must be between 1 and 50"))
		self.room_number = (self.room_number or "").strip()
		dup = frappe.db.exists(
			"PG Room",
			{"property": self.property, "room_number": self.room_number, "name": ("!=", self.name or "")},
		)
		if dup:
			frappe.throw(_("Room {0} already exists in this property").format(self.room_number))
		if not self.is_new():
			self._validate_capacity_change()

	def _validate_capacity_change(self):
		existing = frappe.db.count("PG Bed", {"room": self.name})
		if self.capacity < existing:
			removable = frappe.db.count("PG Bed", {"room": self.name, "status": "Vacant"})
			if existing - self.capacity > removable:
				frappe.throw(_("Cannot reduce beds: only {0} bed(s) are vacant").format(removable))

	def after_insert(self):
		self.sync_beds()

	def on_update(self):
		if not self.is_new():
			self.sync_beds()
		frappe.db.sql("update `tabPG Bed` set property=%s where room=%s", (self.property, self.name))
		update_room_occupancy(self.name)

	def sync_beds(self):
		beds = frappe.get_all("PG Bed", filters={"room": self.name}, fields=["name", "bed_label", "status"], order_by="creation asc")
		if len(beds) < self.capacity:
			used = {b.bed_label for b in beds}
			labels = [l for l in bed_labels(self.capacity + len(used)) if l not in used][: self.capacity - len(beds)]
			for label in labels:
				frappe.get_doc({"doctype": "PG Bed", "property": self.property, "room": self.name, "bed_label": label}).insert(
					ignore_permissions=True
				)
		elif len(beds) > self.capacity:
			for bed in [b for b in reversed(beds) if b.status == "Vacant"][: len(beds) - self.capacity]:
				frappe.delete_doc("PG Bed", bed.name, ignore_permissions=True)

	def on_trash(self):
		if frappe.db.exists("PG Bed", {"room": self.name, "status": ("in", ["Occupied", "Reserved"])}):
			frappe.throw(_("Cannot delete a room with occupied or reserved beds"))
		for bed in frappe.get_all("PG Bed", filters={"room": self.name}, pluck="name"):
			frappe.delete_doc("PG Bed", bed, ignore_permissions=True, force=True)
