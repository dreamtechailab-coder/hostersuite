# Copyright (c) 2026, Maharajan and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from pg_managment_system.utils import ensure_same_property


class PGFloor(Document):
	def validate(self):
		ensure_same_property(self, "PG Building", self.building, "Building")
