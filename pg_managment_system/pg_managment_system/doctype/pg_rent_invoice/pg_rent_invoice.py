# Copyright (c) 2026, Maharajan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today

from pg_managment_system.utils import money


class PGRentInvoice(Document):
	def validate(self):
		occ = frappe.db.get_value("PG Occupancy", self.occupancy, ["tenant", "property", "room"], as_dict=True)
		if not occ or occ.tenant != self.tenant:
			frappe.throw(_("Occupancy {0} does not belong to tenant {1}").format(self.occupancy, self.tenant))
		self.property, self.room = occ.property, occ.room
		if getdate(self.period_end) < getdate(self.period_start):
			frappe.throw(_("Period end cannot be before period start"))
		if not self.items:
			frappe.throw(_("Add at least one charge"))
		for item in self.items:
			if flt(item.amount) <= 0:
				frappe.throw(_("Row {0}: amount must be greater than zero").format(item.idx))
		self.total_amount = money(sum(flt(i.amount) for i in self.items))
		self.paid_amount = money(self.paid_amount)
		if any(i.item_type == "Rent" for i in self.items):
			dup = frappe.db.sql(
				"""select inv.name from `tabPG Rent Invoice` inv
				join `tabPG Invoice Item` it on it.parent = inv.name
				where inv.occupancy=%s and inv.period_start=%s and inv.docstatus < 2
				and it.item_type='Rent' and inv.name != %s limit 1""",
				(self.occupancy, self.period_start, self.name or ""),
			)
			if dup:
				frappe.throw(_("Rent for this period is already invoiced in {0}").format(dup[0][0]))
		self.set_status()

	def set_status(self, update=False):
		self.outstanding_amount = money(flt(self.total_amount) - flt(self.paid_amount))
		if self.docstatus == 0:
			status = "Draft"
		elif self.docstatus == 2:
			status = "Cancelled"
		elif self.outstanding_amount <= 0:
			status = "Paid"
		elif getdate(self.due_date) < getdate(today()):
			status = "Overdue"
		elif flt(self.paid_amount) > 0:
			status = "Partially Paid"
		else:
			status = "Unpaid"
		self.status = status
		if update:
			self.db_set(
				{"status": status, "outstanding_amount": self.outstanding_amount, "paid_amount": self.paid_amount},
				update_modified=False,
			)

	def before_submit(self):
		self.docstatus = 1
		self.set_status()

	def on_submit(self):
		self._link_electricity(self.name)

	def before_cancel(self):
		if flt(self.paid_amount) > 0:
			frappe.throw(_("Cancel the payments allocated to this invoice first"))

	def on_cancel(self):
		self.set_status(update=True)
		self._link_electricity(None)

	def _link_electricity(self, invoice):
		readings = {i.reference_name for i in self.items if i.reference_doctype == "PG Meter Reading" and i.reference_name}
		for reading in readings:
			frappe.db.sql(
				"""update `tabPG Electricity Share` set invoice=%s
				where parent=%s and parenttype='PG Meter Reading' and occupancy=%s""",
				(invoice, reading, self.occupancy),
			)
			frappe.get_doc("PG Meter Reading", reading).update_billing_status()


def update_invoice_payment(invoice: str):
	"""Recompute paid amount from submitted payment allocations (idempotent)."""
	doc = frappe.get_doc("PG Rent Invoice", invoice, for_update=True)
	paid = frappe.db.sql(
		"""select coalesce(sum(a.allocated_amount), 0) from `tabPG Payment Allocation` a
		join `tabPG Payment` p on p.name = a.parent
		where a.invoice=%s and p.docstatus=1""",
		invoice,
	)[0][0]
	if money(paid) > money(doc.total_amount):
		frappe.throw(_("Allocation exceeds outstanding amount of invoice {0}").format(invoice))
	doc.paid_amount = money(paid)
	doc.set_status(update=True)
