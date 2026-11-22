# Copyright (c) 2026, Maharajan and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from pg_managment_system.utils import ensure_same_property


class PGElectricityMeter(Document):
	def validate(self):
		ensure_same_property(self, "PG Room", self.room, "Room")
		if self.is_new() and not self.last_reading:
			self.last_reading = self.initial_reading or 0
