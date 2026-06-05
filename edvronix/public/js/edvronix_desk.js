/**
 * Edvronix Desk Customizations
 * - Hides ERPNext / Frappe Framework branding from the desk UI
 * - Loaded on every desk page via app_include_js in hooks.py
 */

(function () {
	"use strict";

	// ── 1. Disable the "About" dialog (shows "Frappe Framework" title + Frappe copyright) ──
	frappe.provide("frappe.ui.misc");
	frappe.ui.misc.about = function () {
		/* Intentionally disabled — hides Frappe Framework/ERPNext branding */
	};

	// ── 2. Hide "About" menu item from the toolbar help/user menu ──
	$(document).on("toolbar_setup", function () {
		$("[data-item-name='about']").closest("li").hide();
	});

	// ── 3. Watch for ERPNext / Frappe text in module app-name badges ──
	//    Uses MutationObserver so it catches dynamically rendered elements too.
	var HIDDEN_BRANDS = ["ERPNext", "Frappe Framework", "Frappe", "erpnext", "frappe"];

	function hideBrandingText() {
		// Hide .header-subtitle that contains any of the brand names
		document.querySelectorAll(".header-subtitle").forEach(function (el) {
			var txt = el.textContent.trim();
			if (HIDDEN_BRANDS.indexOf(txt) !== -1) {
				el.style.setProperty("display", "none", "important");
			}
		});

		// Hide desktop icons labelled "ERPNext" on the /desk home page
		document.querySelectorAll(".desk-app-item, .app-icon-group").forEach(function (el) {
			var label = el.querySelector(".app-title, .icon-title, h4, .title");
			if (label && HIDDEN_BRANDS.indexOf(label.textContent.trim()) !== -1) {
				el.style.setProperty("display", "none", "important");
			}
		});
	}

	// Run once DOM is ready
	$(document).ready(function () {
		hideBrandingText();

		// Re-run on every Frappe page change (SPA navigation)
		$(document).on("page-change", hideBrandingText);
	});

	// MutationObserver catches anything rendered after page load
	var observer = new MutationObserver(function () {
		hideBrandingText();
	});

	function startObserver() {
		if (document.body) {
			observer.observe(document.body, { childList: true, subtree: true });
		}
	}

	if (document.body) {
		startObserver();
	} else {
		document.addEventListener("DOMContentLoaded", startObserver);
	}

	// ── 4. Clear cached voucher report scripts when Edvronix Settings are saved ──
	// Frappe caches report JS in frappe.query_reports[name] for the session.
	// After changing Primary Brand Color, the old cached script would still render
	// the old color. We clear the cache on settings save so the next print always
	// picks up the fresh color from the server.
	$(document).on("form-save", function (e, frm) {
		if (frm && frm.doctype === "Edvronix Settings") {
			var voucherReports = [
				"Fee Vouher in Bulk with Bank",
				"Fee Vouher in Bulk with Bank Test",
			];
			voucherReports.forEach(function (r) {
				if (frappe.query_reports && frappe.query_reports[r]) {
					delete frappe.query_reports[r];
				}
			});
		}
	});
})();
