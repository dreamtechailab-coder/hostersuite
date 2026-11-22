"""End-to-end business workflow tests.

Run: bench --site <site> run-tests --module pg_managment_system.tests.test_workflows
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, getdate, today

from pg_managment_system.api import payment as payment_api
from pg_managment_system.api import resource, tenant as tenant_api
from pg_managment_system.services.billing import build_invoice
from pg_managment_system.utils import month_bounds

MANAGER = "pg-test-manager@example.com"


def make_property(name):
	if frappe.db.exists("PG Property", name):
		return frappe.get_doc("PG Property", name)
	prop = frappe.get_doc({"doctype": "PG Property", "property_name": name, "city": "Bengaluru"}).insert()
	bld = frappe.get_doc({"doctype": "PG Building", "property": prop.name, "building_name": "Block A"}).insert()
	flr = frappe.get_doc({"doctype": "PG Floor", "property": prop.name, "building": bld.name, "floor_name": "Ground"}).insert()
	frappe.get_doc(
		{"doctype": "PG Room", "property": prop.name, "building": bld.name, "floor": flr.name, "room_number": "101",
		 "room_type": "Double", "capacity": 2, "rent_per_bed": 9000, "security_deposit": 9000}
	).insert()
	return prop


def make_tenant(prop, name, mobile):
	return frappe.get_doc(
		{"doctype": "PG Tenant", "full_name": name, "mobile": mobile, "property": prop, "id_type": "Aadhaar",
		 "id_number": "123412341234"}
	).insert()


class TestPGWorkflows(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.prop = make_property("_Test PG Alpha")
		cls.other = make_property("_Test PG Beta")
		cls.room = frappe.get_value("PG Room", {"property": cls.prop.name}, "name")
		if not frappe.db.exists("User", MANAGER):
			user = frappe.get_doc({"doctype": "User", "email": MANAGER, "first_name": "Mgr", "send_welcome_email": 0})
			user.append("roles", {"role": "PG Manager"})
			user.insert(ignore_permissions=True)
		frappe.get_doc({"doctype": "User Permission", "user": MANAGER, "allow": "PG Property",
						"for_value": cls.prop.name}).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_room_creates_beds_and_capacity_change(self):
		beds = frappe.get_all("PG Bed", filters={"room": self.room}, pluck="bed_label", order_by="bed_label")
		self.assertEqual(beds, ["A", "B"])
		room = frappe.get_doc("PG Room", self.room)
		room.capacity = 3
		room.save()
		self.assertEqual(frappe.db.count("PG Bed", {"room": self.room}), 3)
		room.capacity = 2
		room.save()
		self.assertEqual(frappe.db.count("PG Bed", {"room": self.room}), 2)

	def test_full_lifecycle(self):
		t = make_tenant(self.prop.name, "Ravi Kumar", "9876500001")
		bed = frappe.get_value("PG Bed", {"room": self.room, "bed_label": "A"}, "name")
		booking = frappe.get_doc({"doctype": "PG Booking", "tenant": t.name, "property": self.prop.name, "room": self.room,
								  "bed": bed, "expected_check_in": today(), "advance_amount": 1000}).insert()
		tenant_api.confirm_booking(booking.name)
		self.assertEqual(frappe.db.get_value("PG Bed", bed, "status"), "Reserved")

		# another tenant cannot take the reserved bed
		t2 = make_tenant(self.prop.name, "Someone Else", "9876500002")
		with self.assertRaises(frappe.ValidationError):
			tenant_api.check_in(t2.name, bed)

		start, _end = month_bounds(today())
		res = tenant_api.check_in(t.name, bed, check_in_date=str(start), booking=booking.name)
		occ = res["data"]["occupancy"]["name"]
		self.assertEqual(frappe.db.get_value("PG Bed", bed, "status"), "Occupied")
		self.assertEqual(frappe.db.get_value("PG Booking", booking.name, "status"), "Checked In")
		self.assertEqual(frappe.db.get_value("PG Tenant", t.name, "status"), "Active")

		# electricity: meter + reading split to the single occupant
		meter = frappe.get_doc({"doctype": "PG Electricity Meter", "property": self.prop.name, "room": self.room,
								"meter_number": "_TM-1", "rate_per_unit": 8, "initial_reading": 100}).insert()
		reading = frappe.get_doc({"doctype": "PG Meter Reading", "meter": meter.name, "property": self.prop.name,
								  "period_start": start, "period_end": today(), "current_reading": 150}).insert()
		reading.submit()
		self.assertEqual(reading.amount, 400)
		self.assertEqual(len(reading.shares), 1)
		self.assertEqual(frappe.db.get_value("PG Electricity Meter", meter.name, "last_reading"), 150)

		inv = build_invoice(occ, today())
		self.assertEqual(inv.total_amount, 9400)  # rent 9000 + electricity 400
		self.assertEqual(frappe.db.get_value("PG Meter Reading", reading.name, "billing_status"), "Billed")
		# rent for the same period cannot be invoiced twice
		self.assertIsNone(build_invoice(occ, today()))

		# partial then full payment with idempotency
		p1 = payment_api.collect_payment(t.name, 4000, "Cash", client_request_id="test-req-1")
		again = payment_api.collect_payment(t.name, 4000, "Cash", client_request_id="test-req-1")
		self.assertEqual(p1["data"]["name"], again["data"]["name"])
		inv.reload()
		self.assertEqual(inv.outstanding_amount, 5400)
		self.assertIn(inv.status, ("Partially Paid", "Overdue"))
		payment_api.collect_payment(t.name, 5400, "UPI", reference_no="UTR123")
		inv.reload()
		self.assertEqual(inv.status, "Paid")

		# over-allocation is rejected
		with self.assertRaises(frappe.ValidationError):
			payment_api.collect_payment(t.name, 100, "Cash", allocations=[{"invoice": inv.name, "allocated_amount": 100}])

		# cancelling a payment restores the outstanding amount
		payment_api.cancel_payment(p1["data"]["name"])
		inv.reload()
		self.assertEqual(inv.outstanding_amount, 4000)

		# check-out frees the bed
		tenant_api.check_out(occ, check_out_date=today(), deposit_status="Refunded", deposit_refund_amount=9000)
		self.assertEqual(frappe.db.get_value("PG Bed", bed, "status"), "Vacant")
		self.assertEqual(frappe.db.get_value("PG Tenant", t.name, "status"), "Vacated")

	def test_meter_reading_cannot_go_backwards(self):
		meter = frappe.get_doc({"doctype": "PG Electricity Meter", "property": self.prop.name, "room": self.room,
								"meter_number": "_TM-2", "rate_per_unit": 8, "initial_reading": 500}).insert()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({"doctype": "PG Meter Reading", "meter": meter.name, "property": self.prop.name,
							"period_start": add_days(today(), -30), "period_end": today(), "current_reading": 400}).insert()

	def test_property_isolation_for_manager(self):
		other_tenant = make_tenant(self.other.name, "Hidden Tenant", "9876500009")
		frappe.set_user(MANAGER)
		names = [p.name for p in frappe.get_list("PG Property")]
		self.assertIn(self.prop.name, names)
		self.assertNotIn(self.other.name, names)
		tenants = resource.get_list("PG Tenant", page_size=100)["data"]
		self.assertNotIn(other_tenant.name, [r["name"] for r in tenants])
		with self.assertRaises(frappe.PermissionError):
			resource.get_doc("PG Tenant", other_tenant.name)
		with self.assertRaises(frappe.PermissionError):
			resource.save_doc("PG Tenant", {"full_name": "X", "mobile": "9876500010", "property": self.other.name})
		from pg_managment_system.api.dashboard import get_dashboard

		with self.assertRaises(frappe.PermissionError):
			get_dashboard(property=self.other.name)

	def test_id_number_is_masked_and_fields_whitelisted(self):
		t = make_tenant(self.prop.name, "Masked Person", "9876500011")
		data = resource.get_doc("PG Tenant", t.name)["data"]
		self.assertNotIn("id_number", data)
		self.assertEqual(data["id_number_masked"], "XXXX-XXXX-1234")
		# read-only computed fields are ignored on write
		res = resource.save_doc("PG Tenant", {"name": t.name, "full_name": "Masked P", "status": "Vacated"})
		self.assertEqual(res["data"]["status"], "Prospective")
		with self.assertRaises(frappe.PermissionError):
			resource.get_list("User")


class TestPGEndpoints(FrappeTestCase):
	"""Smoke-test every read endpoint used by the frontend (catches SQL/permission errors)."""

	def test_read_endpoints(self):
		frappe.set_user("Administrator")
		prop = make_property("_Test PG Alpha")
		from pg_managment_system.api import (dashboard, electricity, expense, finance, notifications, property as p,
											  rent, report, search, session, settings, users, whatsapp)

		calls = [
			(session.get_session, {}),
			(dashboard.get_dashboard, {}),
			(dashboard.get_dashboard, {"property": prop.name, "from_date": "2026-01-01", "to_date": "2026-12-31"}),
			(p.get_property_overview, {"name": prop.name}),
			(p.get_hierarchy, {"property": prop.name}),
			(p.get_room_board, {"property": prop.name}),
			(rent.get_rent_summary, {}),
			(electricity.get_meters, {}),
			(electricity.get_summary, {}),
			(electricity.get_bills, {}),
			(expense.get_summary, {}),
			(finance.get_receivables, {}),
			(finance.get_payables, {}),
			(finance.get_financial_summary, {}),
			(report.occupancy_report, {}),
			(report.revenue_report, {}),
			(report.expense_report, {}),
			(whatsapp.get_dashboard, {}),
			(search.global_search, {"q": "Test"}),
			(notifications.get_notifications, {}),
			(settings.get_settings, {}),
			(users.list_users, {}),
			(users.get_role_matrix, {}),
		]
		for fn, kwargs in calls:
			with self.subTest(fn=fn.__module__ + "." + fn.__name__):
				self.assertIn("data", fn(**kwargs))
		room = frappe.get_value("PG Room", {"property": prop.name}, "name")
		self.assertTrue(p.get_room_details(room)["data"]["beds"])
		for dt in resource.REGISTRY:
			with self.subTest(doctype=dt):
				resource.get_list(dt)
				resource.get_options(dt)


class TestTenantListMasking(FrappeTestCase):
	def test_list_masks_and_blocks_id_filter(self):
		frappe.set_user("Administrator")
		prop = make_property("_Test PG Alpha")
		t = make_tenant(prop.name, "List Masked", "9876500077")
		rows = resource.get_list("PG Tenant", filters={"name": t.name})["data"]
		self.assertEqual(rows[0]["id_number_masked"], "XXXX-XXXX-1234")
		self.assertNotIn("id_number", rows[0])
		with self.assertRaises(frappe.ValidationError):
			resource.get_list("PG Tenant", filters={"id_number": ["like", "%1234"]})
