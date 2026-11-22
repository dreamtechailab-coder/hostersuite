# Copyright (c) 2026, Maharajan and contributors
# For license information, please see license.txt

import re

from frappe.model.document import Document

PLACEHOLDER = re.compile(r"{{\s*(\w+)\s*}}")


class PGWhatsAppTemplate(Document):
	def placeholders(self) -> list[str]:
		return PLACEHOLDER.findall(self.body or "")

	def render(self, context: dict) -> str:
		return PLACEHOLDER.sub(lambda m: str(context.get(m.group(1), "")), self.body or "")
