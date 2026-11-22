# Copyright (c) 2026, Maharajan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class PGExpense(Document):
	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Amount must be greater than zero"))
		if self.payment_status == "Paid":
			self.paid_on = self.paid_on or self.expense_date
			self.due_date = None
		else:
			self.paid_on = None
			self.due_date = self.due_date or self.expense_date
