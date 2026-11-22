# Copyright (c) 2026, Maharajan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from pg_managment_system.utils import ensure_same_property, update_room_occupancy


class PGOccupancy(Document):
	def validate(self):
		ensure_same_property(self, "PG Room", self.room, "Room")
		ensure_same_property(self, "PG Tenant", self.tenant, "Tenant")
		bed = frappe.db.get_value(
			"PG Bed", self.bed, ["room", "status", "reserved_booking", "current_occupancy"], as_dict=True
		)
		if not bed or bed.room != self.room:
			frappe.throw(_("Selected bed is not in room {0}").format(self.room))
		if self.status != "Ended":
			if self.is_new():
				if bed.status == "Occupied" or bed.status == "Maintenance":
					frappe.throw(_("Bed is not available (currently {0})").format(bed.status))
				if bed.status == "Reserved" and bed.reserved_booking != self.booking:
					frappe.throw(_("Bed is reserved for booking {0}").format(bed.reserved_booking))
			other = frappe.db.get_value(
				"PG Occupancy",
				{"tenant": self.tenant, "status": ("!=", "Ended"), "name": ("!=", self.name or "")},
				"name",
			)
			if other:
				frappe.throw(_("Tenant already has an active occupancy {0}").format(other))
		if self.check_out_date and getdate(self.check_out_date) < getdate(self.check_in_date):
			frappe.throw(_("Check-out date cannot be before check-in date"))
		if self.status == "Ended" and not self.check_out_date:
			frappe.throw(_("Check-out date is required to end an occupancy"))
		if self.rent_due_day and not 1 <= self.rent_due_day <= 28:
			frappe.throw(_("Rent due day must be between 1 and 28"))
		before = self.get_doc_before_save()
		if before and before.status == "Ended" and self.status != "Ended":
			frappe.throw(_("An ended occupancy cannot be reopened"))

	def on_update(self):
		if self.status == "Ended":
			if frappe.db.get_value("PG Bed", self.bed, "current_occupancy") == self.name:
				frappe.db.set_value(
					"PG Bed", self.bed, {"status": "Vacant", "current_tenant": None, "current_occupancy": None}
				)
			if not frappe.db.exists("PG Occupancy", {"tenant": self.tenant, "status": ("!=", "Ended")}):
				frappe.db.set_value("PG Tenant", self.tenant, "status", "Vacated")
		else:
			frappe.db.set_value(
				"PG Bed",
				self.bed,
				{"status": "Occupied", "current_tenant": self.tenant, "current_occupancy": self.name, "reserved_booking": None},
			)
			frappe.db.set_value(
				"PG Tenant",
				self.tenant,
				{"status": "On Notice" if self.status == "On Notice" else "Active", "property": self.property},
			)
			if self.booking:
				frappe.db.set_value("PG Booking", self.booking, {"status": "Checked In", "occupancy": self.name})
		update_room_occupancy(self.room)

	def on_trash(self):
		if frappe.db.exists("PG Rent Invoice", {"occupancy": self.name, "docstatus": ("<", 2)}):
			frappe.throw(_("Occupancy has invoices and cannot be deleted. End it instead."))
		if frappe.db.get_value("PG Bed", self.bed, "current_occupancy") == self.name:
			frappe.db.set_value("PG Bed", self.bed, {"status": "Vacant", "current_tenant": None, "current_occupancy": None})
			update_room_occupancy(self.room)
