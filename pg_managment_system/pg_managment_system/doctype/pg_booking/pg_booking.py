# Copyright (c) 2026, Maharajan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from pg_managment_system.utils import ensure_same_property, update_room_occupancy


class PGBooking(Document):
	def validate(self):
		ensure_same_property(self, "PG Room", self.room, "Room")
		ensure_same_property(self, "PG Tenant", self.tenant, "Tenant")
		if self.bed and frappe.db.get_value("PG Bed", self.bed, "room") != self.room:
			frappe.throw(_("Selected bed is not in room {0}").format(self.room))
		if getdate(self.expected_check_in) < getdate(self.booking_date):
			frappe.throw(_("Expected check-in cannot be before booking date"))
		before = self.get_doc_before_save()
		if before and before.status in ("Checked In", "Cancelled") and self.status != before.status:
			frappe.throw(_("A {0} booking cannot be changed").format(before.status.lower()))
		if self.status in ("Pending", "Confirmed") and self.bed:
			bed = frappe.db.get_value("PG Bed", self.bed, ["status", "reserved_booking"], as_dict=True)
			if bed.status == "Occupied" or bed.status == "Maintenance" or (
				bed.status == "Reserved" and bed.reserved_booking not in (None, "", self.name)
			):
				frappe.throw(_("Bed is not available (currently {0})").format(bed.status))

	def on_update(self):
		before = self.get_doc_before_save()
		old_bed = before.bed if before else None
		if old_bed and old_bed != self.bed:
			self._release(old_bed)
		if self.bed and self.status == "Confirmed":
			frappe.db.set_value("PG Bed", self.bed, {"status": "Reserved", "reserved_booking": self.name})
			update_room_occupancy(self.room)
		elif self.bed and self.status == "Cancelled":
			self._release(self.bed)

	def _release(self, bed):
		if frappe.db.get_value("PG Bed", bed, "reserved_booking") == self.name:
			frappe.db.set_value("PG Bed", bed, {"status": "Vacant", "reserved_booking": None})
			update_room_occupancy(frappe.db.get_value("PG Bed", bed, "room"))

	def on_trash(self):
		if self.status == "Checked In":
			frappe.throw(_("Checked-in bookings cannot be deleted"))
		if self.bed:
			self._release(self.bed)
