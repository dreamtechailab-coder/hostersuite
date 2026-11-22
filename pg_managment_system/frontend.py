"""Serve the built HostelSuite Vue app (``pg-management-frontend/dist``) at ``/hostelsuite``.

Registered as a ``page_renderer`` hook, so no reverse-proxy change is needed: the
web server already forwards unknown paths to Frappe, and the SPA shares Frappe's
origin (session cookie + CSRF work as-is).

* ``/hostelsuite/<file>`` → that file from ``dist`` (JS/CSS/icons/sw.js/manifest)
* anything else under ``/hostelsuite`` → ``index.html`` (client-side routing)

Hashed build assets get a long cache lifetime; ``index.html``, the service worker
and the manifest are never cached so a new deploy is picked up immediately.
"""

import mimetypes
import os
from pathlib import Path

from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file

import frappe
from frappe.website.page_renderers.base_renderer import BaseRenderer

FRONTEND_ROUTE = "hostelsuite"
DIST_DIR = Path(__file__).resolve().parent.parent / "pg-management-frontend" / "dist"
NO_CACHE = {"index.html", "sw.js", "push-sw.js", "manifest.webmanifest", "offline.html", "registerSW.js"}

mimetypes.add_type("application/manifest+json", ".webmanifest")


class FrontendPage(BaseRenderer):
	__slots__ = ("file_path",)

	def can_render(self):
		if self.path != FRONTEND_ROUTE and not self.path.startswith(FRONTEND_ROUTE + "/"):
			return False
		self.file_path = self._resolve_file()
		return self.file_path is not None

	def _resolve_file(self) -> Path | None:
		if not DIST_DIR.is_dir():
			return None
		rel = self.path[len(FRONTEND_ROUTE) :].lstrip("/")
		if rel:
			# Frappe strips ".html" before resolving, so try it both ways.
			for candidate in (rel, rel + ".html"):
				path = (DIST_DIR / candidate).resolve()
				if path.is_relative_to(DIST_DIR) and path.is_file():
					return path
			# a missing *file* (has an extension) is a real 404, not an SPA route
			if "." in os.path.basename(rel):
				return None
		index = DIST_DIR / "index.html"
		return index if index.is_file() else None

	def render(self):
		f = open(self.file_path, "rb")  # closed by Frappe's response middleware
		response = Response(wrap_file(frappe.local.request.environ, f), direct_passthrough=True)
		response.mimetype = mimetypes.guess_type(self.file_path.name)[0] or "application/octet-stream"
		if self.file_path.name == "sw.js":
			# nginx strips the trailing slash, so the SW must control "/hostelsuite" too
			response.headers["Service-Worker-Allowed"] = "/" + FRONTEND_ROUTE
		if self.file_path.name in NO_CACHE:
			response.headers["Cache-Control"] = "no-cache"
		elif self.file_path.parent.name == "assets":
			response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
		else:
			response.headers["Cache-Control"] = "public, max-age=86400"
		return response
