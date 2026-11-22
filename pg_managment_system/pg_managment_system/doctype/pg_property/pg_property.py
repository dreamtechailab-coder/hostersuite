# Copyright (c) 2026, Maharajan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PGProperty(Document):
	def validate(self):
		if self.property_code:
			self.property_code = self.property_code.strip().upper()

	def after_insert(self):
		# Give the creating (non-admin) user access to the property they created.
		from pg_managment_system.permissions import clear_cache, is_pg_admin

		user = frappe.session.user
		if not is_pg_admin(user) and not frappe.db.exists(
			"User Permission", {"user": user, "allow": "PG Property", "for_value": self.name}
		):
			frappe.get_doc(
				{"doctype": "User Permission", "user": user, "allow": "PG Property", "for_value": self.name}
			).insert(ignore_permissions=True)
			clear_cache(user)
