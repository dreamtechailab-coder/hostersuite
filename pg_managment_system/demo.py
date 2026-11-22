"""Demo data for evaluating the PG Management System.

    bench --site <site> execute pg_managment_system.demo.create_demo_data

Creates two properties with rooms, ~24 tenants, occupancies, three months of
invoices/payments, electricity readings, expenses, a booking and a manager
user (demo.manager@example.com / password printed at the end). Idempotent:
does nothing if the demo properties already exist.
"""

import random
from datetime import date

import frappe
from frappe.utils import add_days, add_months, getdate, today

from pg_managment_system.utils import clamp_day, month_bounds

FIRST = ["Aarav", "Vivaan", "Aditya", "Arjun", "Sai", "Reyansh", "Krishna", "Ishaan", "Rohan", "Kabir", "Ananya", "Diya",
		 "Saanvi", "Aadhya", "Kiara", "Myra", "Priya", "Meera", "Nisha", "Riya", "Tara", "Zoya", "Neha", "Kavya"]
LAST = ["Sharma", "Iyer", "Reddy", "Nair", "Gupta", "Patel", "Rao", "Menon", "Das", "Singh", "Khan", "Joshi"]


def _get_or_create(doctype, filters, values):
	name = frappe.db.get_value(doctype, filters, "name")
	if name:
		return frappe.get_doc(doctype, name)
	return frappe.get_doc({"doctype": doctype, **filters, **values}).insert()


def create_demo_data(seed: int = 7):
	if frappe.db.exists("PG Property", "Sunrise PG Koramangala"):
		print("Demo data already present")
		return
	random.seed(seed)
	frappe.set_user("Administrator")
	props = [
		("Sunrise PG Koramangala", "Bengaluru", "Co-living", "KRM-01"),
		("Lotus Ladies PG", "Bengaluru", "Girls", "HSR-02"),
	]
	rooms_by_prop = {}
	for pname, city, ptype, code in props:
		p = frappe.get_doc({"doctype": "PG Property", "property_name": pname, "city": city, "property_type": ptype,
							"property_code": code, "phone": "9876543210", "address_line": "5th Block"}).insert()
		rooms_by_prop[p.name] = []
		for bname in ("Block A", "Block B") if code == "KRM-01" else ("Main",):
			b = frappe.get_doc({"doctype": "PG Building", "property": p.name, "building_name": bname}).insert()
			for level in range(1, 3):
				f = frappe.get_doc({"doctype": "PG Floor", "property": p.name, "building": b.name,
									"floor_name": f"Floor {level}", "floor_number": level}).insert()
				for i in range(1, 4):
					rtype, cap, rent = random.choice([("Single", 1, 14000), ("Double", 2, 9500), ("Triple", 3, 7500)])
					r = frappe.get_doc({"doctype": "PG Room", "property": p.name, "building": b.name, "floor": f.name,
										"room_number": f"{bname[-1]}{level}0{i}", "room_type": rtype, "capacity": cap,
										"rent_per_bed": rent, "security_deposit": rent, "is_ac": int(rent > 9000)}).insert()
					rooms_by_prop[p.name].append(r)
					frappe.get_doc({"doctype": "PG Electricity Meter", "property": p.name, "room": r.name,
									"meter_number": f"{code}-{r.room_number}", "rate_per_unit": 9,
									"initial_reading": random.randint(1000, 4000)}).insert()

	this_month = month_bounds(today())[0]
	start_month = add_months(this_month, -3)
	people = [(f, l) for f in FIRST for l in LAST]
	random.shuffle(people)
	occupancies = []
	for prop, rooms in rooms_by_prop.items():
		for room in rooms:
			for bed in frappe.get_all("PG Bed", filters={"room": room.name}, pluck="name"):
				if random.random() < 0.18:
					continue  # leave some vacancy
				first, last = people.pop()
				t = frappe.get_doc({"doctype": "PG Tenant", "full_name": f"{first} {last}",
									"mobile": f"9{random.randint(100000000, 999999999)}", "property": prop,
									"gender": "Female" if first in FIRST[10:] else "Male", "occupation": "Software Engineer",
									"id_type": "Aadhaar", "id_number": str(random.randint(10**11, 10**12 - 1))}).insert()
				check_in = add_days(start_month, random.randint(0, 75))
				occ = frappe.get_doc({"doctype": "PG Occupancy", "tenant": t.name, "property": prop, "room": room.name,
									  "bed": bed, "check_in_date": check_in, "monthly_rent": room.rent_per_bed,
									  "security_deposit": room.security_deposit, "rent_due_day": 5, "status": "Active"}).insert()
				occupancies.append(occ)

	# electricity readings for the previous months
	for m in range(3, 0, -1):
		ps, pe = month_bounds(add_months(this_month, -m))
		for meter in frappe.get_all("PG Electricity Meter", fields=["name", "last_reading"]):
			reading = frappe.get_doc({"doctype": "PG Meter Reading", "meter": meter.name, "reading_date": pe,
									  "period_start": ps, "period_end": pe,
									  "current_reading": float(frappe.db.get_value("PG Electricity Meter", meter.name, "last_reading")) + random.randint(60, 220)})
			reading.property = frappe.db.get_value("PG Electricity Meter", meter.name, "property")
			reading.insert()
			reading.submit()

	# invoices + payments for past months and the current month
	from pg_managment_system.services.billing import build_invoice

	for m in range(2, -1, -1):
		ps = add_months(this_month, -m)
		for occ in occupancies:
			if getdate(occ.check_in_date) > month_bounds(ps)[1]:
				continue
			inv = build_invoice(occ.name, ps, submit=False)
			if not inv:
				continue
			due = clamp_day(getdate(ps).year, getdate(ps).month, 5)
			inv.invoice_date = ps
			inv.due_date = max(due, getdate(occ.check_in_date))
			inv.save()
			inv.submit()
			# most tenants pay; current month partially collected
			roll = random.random()
			if m > 0 and roll < 0.88 or m == 0 and roll < 0.45:
				amount = inv.total_amount if roll < 0.8 or m == 0 else round(inv.total_amount * 0.5)
				pay_date = min(getdate(today()), add_days(inv.due_date, random.randint(-4, 6)))
				mode = random.choice(["UPI", "UPI", "Cash", "Bank Transfer"])
				frappe.get_doc({"doctype": "PG Payment", "tenant": occ.tenant, "property": occ.property, "amount": amount,
								"mode": mode, "reference_no": None if mode == "Cash" else f"UTR{random.randint(10**9, 10**10)}",
								"payment_date": pay_date,
								"allocations": [{"invoice": inv.name, "allocated_amount": amount}]}).insert().submit()
	frappe.db.sql("update `tabPG Rent Invoice` set status='Overdue' where docstatus=1 and outstanding_amount>0 and due_date < %s", today())

	# expenses
	cats = ["Electricity", "Water", "Internet", "Groceries", "Salaries", "Maintenance & Repairs", "Housekeeping"]
	for prop in rooms_by_prop:
		for m in range(3, -1, -1):
			ms = add_months(this_month, -m)
			for cat in cats:
				d = add_days(ms, random.randint(0, 25))
				if getdate(d) > getdate(today()):
					continue
				unpaid = m == 0 and random.random() < 0.3
				frappe.get_doc({"doctype": "PG Expense", "property": prop, "category": cat, "expense_date": d,
								"amount": random.choice([1800, 3500, 6200, 12000, 24000, 45000]) if cat != "Salaries" else 60000,
								"vendor": f"{cat} Services", "payment_status": "Unpaid" if unpaid else "Paid",
								"due_date": add_days(d, 10) if unpaid else None, "payment_mode": "UPI"}).insert()

	# a pending booking
	first, last = people.pop()
	prospect = frappe.get_doc({"doctype": "PG Tenant", "full_name": f"{first} {last}", "mobile": "9000011111",
							   "property": list(rooms_by_prop)[0]}).insert()
	vacant = frappe.get_value("PG Bed", {"status": "Vacant", "property": prospect.property}, ["name", "room"], as_dict=True)
	if vacant:
		frappe.get_doc({"doctype": "PG Booking", "tenant": prospect.name, "property": prospect.property, "room": vacant.room,
						"bed": vacant.name, "expected_check_in": add_days(today(), 5), "advance_amount": 2000}).insert()

	# manager restricted to the first property
	email = "demo.manager@example.com"
	password = frappe.generate_hash(length=12)
	if not frappe.db.exists("User", email):
		u = frappe.get_doc({"doctype": "User", "email": email, "first_name": "Demo", "last_name": "Manager",
							"send_welcome_email": 0, "new_password": password, "roles": [{"role": "PG Manager"}]})
		u.insert(ignore_permissions=True)
		frappe.get_doc({"doctype": "User Permission", "user": email, "allow": "PG Property",
						"for_value": list(rooms_by_prop)[0]}).insert(ignore_permissions=True)
	frappe.db.commit()
	print(f"Demo data created. Manager login: {email} / {password}")
