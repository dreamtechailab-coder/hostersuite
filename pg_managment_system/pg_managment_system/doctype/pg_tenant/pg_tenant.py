# Copyright (c) 2026, Maharajan and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document

from pg_managment_system.utils import normalize_mobile


class PGTenant(Document):
	def validate(self):
		self.full_name = " ".join((self.full_name or "").split())
		self.mobile = normalize_mobile(self.mobile)
		if self.emergency_contact_phone:
			self.emergency_contact_phone = normalize_mobile(self.emergency_contact_phone)
		dup = frappe.db.get_value(
			"PG Tenant",
			{"mobile": self.mobile, "status": ("!=", "Vacated"), "name": ("!=", self.name or "")},
			"full_name",
		)
		if dup:
			frappe.throw(_("Mobile number already registered for {0}").format(dup))
		if self.id_number:
			self.id_number = re.sub(r"\s", "", self.id_number).upper()
			if self.id_type == "Aadhaar" and not re.fullmatch(r"\d{12}", self.id_number):
				frappe.throw(_("Aadhaar number must be 12 digits"))
			if self.id_type == "PAN" and not re.fullmatch(r"[A-Z]{5}\d{4}[A-Z]", self.id_number):
				frappe.throw(_("Invalid PAN format"))

	def on_trash(self):
		if frappe.db.exists("PG Occupancy", {"tenant": self.name}):
			frappe.throw(_("Tenant has occupancy history and cannot be deleted. Mark as Vacated instead."))
