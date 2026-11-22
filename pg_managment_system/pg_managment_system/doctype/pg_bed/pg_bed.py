# Copyright (c) 2026, Maharajan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PGBed(Document):
	def validate(self):
		room_property = frappe.db.get_value("PG Room", self.room, "property")
		if room_property and room_property != self.property:
			self.property = room_property
		if self.status in ("Vacant", "Maintenance"):
			if self.current_occupancy and frappe.db.get_value("PG Occupancy", self.current_occupancy, "status") != "Ended":
				frappe.throw(_("Bed {0} has an active occupancy").format(self.bed_label))
			self.current_tenant = self.current_occupancy = None
			self.reserved_booking = None
