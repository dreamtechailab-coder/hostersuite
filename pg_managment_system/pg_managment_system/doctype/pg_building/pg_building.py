# Copyright (c) 2026, Maharajan and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class PGBuilding(Document):
	def validate(self):
		self.building_name = (self.building_name or "").strip()
