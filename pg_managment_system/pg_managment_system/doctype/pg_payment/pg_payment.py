# Copyright (c) 2026, Maharajan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from pg_managment_system.pg_managment_system.doctype.pg_rent_invoice.pg_rent_invoice import update_invoice_payment
from pg_managment_system.utils import ensure_same_property, money


class PGPayment(Document):
	def validate(self):
		ensure_same_property(self, "PG Tenant", self.tenant, "Tenant")
		if flt(self.amount) <= 0:
			frappe.throw(_("Amount must be greater than zero"))
		if self.mode != "Cash" and not self.reference_no and self.mode != "Card":
			frappe.throw(_("Reference / UTR number is required for {0} payments").format(self.mode))
		seen = set()
		for row in self.allocations:
			if row.invoice in seen:
				frappe.throw(_("Invoice {0} is allocated more than once").format(row.invoice))
			seen.add(row.invoice)
			inv = frappe.db.get_value(
				"PG Rent Invoice", row.invoice, ["tenant", "docstatus", "outstanding_amount", "property"], as_dict=True
			)
			if not inv or inv.docstatus != 1:
				frappe.throw(_("Invoice {0} is not submitted").format(row.invoice))
			if inv.tenant != self.tenant:
				frappe.throw(_("Invoice {0} belongs to another tenant").format(row.invoice))
			if flt(row.allocated_amount) <= 0:
				frappe.throw(_("Row {0}: allocated amount must be positive").format(row.idx))
			if money(row.allocated_amount) > money(inv.outstanding_amount) and self.docstatus == 0:
				frappe.throw(
					_("Allocated amount for {0} exceeds outstanding {1}").format(row.invoice, inv.outstanding_amount)
				)
		self.allocated_amount = money(sum(flt(r.allocated_amount) for r in self.allocations))
		if self.allocated_amount > money(self.amount):
			frappe.throw(_("Allocated amount cannot exceed payment amount"))
		self.unallocated_amount = money(flt(self.amount) - self.allocated_amount)
		if self.is_new():
			self.received_by = frappe.session.user

	def on_submit(self):
		for row in self.allocations:
			update_invoice_payment(row.invoice)

	def on_cancel(self):
		for row in self.allocations:
			update_invoice_payment(row.invoice)
