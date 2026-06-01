# Copyright (c) 2026, Solvronix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EdvronixSettings(Document):
	pass


@frappe.whitelist()
def save_terms_template(template_name, content, applicable_for="All"):
	settings = frappe.get_single("Edvronix Settings")
	settings.append("terms_templates", {
		"template_name": template_name,
		"is_default": 1,
		"applicable_for": applicable_for,
		"content": content,
	})
	settings.save(ignore_permissions=True)
	frappe.db.commit()
	return {"success": True}


@frappe.whitelist()
def get_edvronix_settings():
	settings = frappe.get_single("Edvronix Settings")

	item_abbr = {}
	for row in settings.get("item_abbreviations", []):
		if row.item_name and row.abbreviation:
			item_abbr[row.item_name] = row.abbreviation

	late_fee_text = settings.late_fee_policy_text or (
		"After 10th date extra charges apply\nAfter 20th date additional charges apply"
	)

	return {
		"school_name": settings.school_name or "",
		"school_logo": settings.school_logo or "",
		"watermark_text": settings.watermark_text or settings.school_name or "",
		"address": settings.address or "",
		"phone": settings.phone or "",
		"mobile": settings.mobile or "",
		"email": settings.email or "",
		"website": settings.website or "",
		"bank_name": settings.bank_name or "",
		"account_title": settings.account_title or "",
		"account_number": settings.account_number or "",
		"iban": settings.iban or "",
		"branch_name": settings.branch_name or "",
		"late_fee_policy_text": late_fee_text,
		"late_fee_after_10": settings.late_fee_after_10 or 100,
		"late_fee_after_20": settings.late_fee_after_20 or 200,
		"item_abbreviations": item_abbr,
		"terms_templates": [
			{
				"template_name": row.template_name,
				"is_default": row.is_default,
				"applicable_for": row.applicable_for,
				"content": row.content,
			}
			for row in settings.get("terms_templates", [])
		],
	}
