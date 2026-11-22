# Copyright (c) 2026, Maharajan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

from pg_managment_system.utils import money, overlap_days


class PGMeterReading(Document):
	def validate(self):
		meter = frappe.db.get_value(
			"PG Electricity Meter", self.meter, ["property", "room", "rate_per_unit", "last_reading", "is_active"], as_dict=True
		)
		if not meter or not meter.is_active:
			frappe.throw(_("Meter {0} is not active").format(self.meter))
		self.property, self.room = meter.property, meter.room
		if self.docstatus == 0:
			self.previous_reading = flt(meter.last_reading)
			self.rate_per_unit = meter.rate_per_unit
		if getdate(self.period_end) < getdate(self.period_start):
			frappe.throw(_("Period end cannot be before period start"))
		if flt(self.current_reading) < flt(self.previous_reading):
			frappe.throw(
				_("Current reading ({0}) cannot be less than previous reading ({1})").format(
					self.current_reading, self.previous_reading
				)
			)
		self.units_consumed = flt(self.current_reading) - flt(self.previous_reading, 3)
		self.amount = money(self.units_consumed * flt(self.rate_per_unit))
		if self.docstatus == 0:
			self.compute_shares()

	def compute_shares(self):
		"""Split the bill among occupants, pro-rated by days stayed in the period."""
		occupancies = frappe.db.sql(
			"""select name, tenant, check_in_date, coalesce(check_out_date, %(end)s) as check_out
			from `tabPG Occupancy`
			where room=%(room)s and check_in_date <= %(end)s
			and (check_out_date is null or check_out_date >= %(start)s)
			order by check_in_date""",
			{"room": self.room, "start": self.period_start, "end": self.period_end},
			as_dict=True,
		)
		rows = []
		for occ in occupancies:
			days = overlap_days(occ.check_in_date, occ.check_out, self.period_start, self.period_end)
			if days:
				rows.append({"tenant": occ.tenant, "occupancy": occ.name, "days": days})
		self.set("shares", [])
		total_days = sum(r["days"] for r in rows)
		allocated = 0.0
		for i, row in enumerate(rows):
			if i == len(rows) - 1:
				row["amount"] = money(self.amount - allocated)
			else:
				row["amount"] = money(self.amount * row["days"] / total_days)
				allocated += row["amount"]
			self.append("shares", row)

	def on_submit(self):
		meter = frappe.get_doc("PG Electricity Meter", self.meter, for_update=True)
		if flt(meter.last_reading) != flt(self.previous_reading):
			frappe.throw(_("Meter reading changed meanwhile. Please reload and try again."))
		meter.db_set({"last_reading": self.current_reading, "last_reading_date": self.reading_date})
		self.update_billing_status()

	def before_cancel(self):
		if any(s.invoice for s in self.shares):
			frappe.throw(_("Cancel the invoices that include this electricity bill first"))
		later = frappe.db.exists(
			"PG Meter Reading",
			{"meter": self.meter, "docstatus": 1, "creation": (">", self.creation), "name": ("!=", self.name)},
		)
		if later:
			frappe.throw(_("Only the latest reading of a meter can be cancelled"))

	def on_cancel(self):
		frappe.db.set_value("PG Electricity Meter", self.meter, "last_reading", self.previous_reading)

	def update_billing_status(self):
		shares = frappe.get_all("PG Electricity Share", filters={"parent": self.name, "parenttype": self.doctype}, pluck="invoice")
		billed = len([s for s in shares if s])
		status = "Unbilled" if not billed else ("Billed" if billed == len(shares) else "Partially Billed")
		if not shares and self.docstatus == 1:
			status = "Billed"  # nothing to bill (vacant room)
		self.db_set("billing_status", status, update_modified=False)
