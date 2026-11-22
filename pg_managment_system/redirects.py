"""Send PG business users to the Vue frontend instead of Frappe Desk.

Frappe's login flow always lands System Users on ``/app`` (Desk). This hook
intercepts any Desk page render for users who hold a PG role but are not
System Managers and redirects them to the Vue site.

The frontend URL comes from site config so it can differ per environment::

    bench --site <site> set-config pg_frontend_url "https://pg.example.com"
    bench --site <site> set-config pg_frontend_url "http://localhost:5173"   # dev

When unset it defaults to ``/`` (Vue app served at the root of the same
origin, with ``/app``, ``/api`` … reverse-proxied to Frappe).
"""

from urllib.parse import urlencode

import frappe
from frappe.website.page_renderers.base_renderer import BaseRenderer
from frappe.website.page_renderers.redirect_page import RedirectPage

from pg_managment_system.permissions import PG_ROLES

DESK_PREFIXES = ("/app", "/desk")
DESK_ROLES = frozenset({"System Manager"})


def get_frontend_url() -> str:
	return (frappe.conf.get("pg_frontend_url") or "/").strip()


def should_use_frontend(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user in ("Guest", "Administrator"):
		return False
	roles = set(frappe.get_roles(user))
	return bool(roles.intersection(PG_ROLES)) and not roles.intersection(DESK_ROLES)


def _is_desk_path(path: str) -> bool:
	return any(path == p or path.startswith(p + "/") for p in DESK_PREFIXES)


def redirect_desk_to_frontend(context):
	"""``update_website_context`` hook: bounce PG users from Desk to the Vue app."""
	request = getattr(frappe.local, "request", None)
	if not request or not _is_desk_path(request.path.rstrip("/") or "/"):
		return
	if not should_use_frontend():
		return

	# 302 (not frappe.redirect's 301) so browsers don't cache it permanently –
	# a user later granted System Manager must still be able to reach Desk.
	frappe.flags.redirect_location = get_frontend_url()
	raise frappe.Redirect(302)


def _safe_relative(path: str | None) -> str | None:
	"""Only same-site relative paths may be forwarded as a post-login target."""
	if path and path.startswith("/") and not path.startswith("//") and "\\" not in path:
		return path
	return None


class FrontendLoginPage(BaseRenderer):
	"""``page_renderer`` hook: replace Frappe's ``/login`` with the HostelSuite login.

	Active whenever the SPA is not mounted at the site root: either an absolute
	``pg_frontend_url`` (separate host) or a sub-path such as ``/hostelsuite``.
	When the SPA *is* at ``/`` the reverse proxy already serves ``/login`` from
	it, so redirecting here would loop.

	``/login?native=1`` keeps Frappe's own form reachable as an escape hatch
	(e.g. if the frontend is down).
	"""

	def can_render(self):
		if self.path != "login" or frappe.form_dict.get("native"):
			return False
		return get_frontend_url().rstrip("/") != ""

	def render(self):
		target = get_frontend_url().rstrip("/") + "/login"
		redirect = _safe_relative(frappe.form_dict.get("redirect-to"))
		if redirect and redirect not in ("/", "/app"):
			target += "?" + urlencode({"redirect": redirect})
		frappe.flags.redirect_location = target
		return RedirectPage(self.path, 302).render()
