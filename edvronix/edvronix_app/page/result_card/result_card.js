frappe.pages["result-card"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Result Card",
		single_column: true,
	});

	var current_data = null;

	page.set_primary_action("Load Results", load_results, "refresh");
	page.add_button(__("Print All"), print_all, { icon: "printer" });

	// ── CSS for the result card (used both in preview and in the print popup) ──
	var RC_CSS = [
		"* { margin:0; padding:0; box-sizing:border-box; }",
		"body { font-family: Arial, Helvetica, sans-serif; background:#fff; color:#000; }",

		// Card container
		".result-card-wrap {",
		"  width:190mm; min-height:257mm; margin:8mm auto; padding:8mm 10mm;",
		"  border:2.5px double #1a1a2e; page-break-after:always; break-after:page;",
		"}",
		".result-card-wrap:last-child { page-break-after:auto; break-after:auto; }",

		// Header
		".rc-header { display:flex; align-items:center; gap:12px;",
		"  padding-bottom:8px; border-bottom:3px double #1a1a2e; margin-bottom:9px; }",
		".rc-logo img { height:72px; width:auto; display:block; }",
		".rc-school-info { flex:1; text-align:center; }",
		".rc-school-name { font-size:17pt; font-weight:700; color:#1a1a2e;",
		"  letter-spacing:1.5px; text-transform:uppercase; line-height:1.2; }",
		".rc-school-addr { font-size:8.5pt; color:#444; margin-top:2px; }",
		".rc-card-title { display:inline-block; margin-top:5px; padding:2px 14px;",
		"  font-size:11.5pt; font-weight:700; color:#003366; letter-spacing:2px;",
		"  text-transform:uppercase; border:1.5px solid #003366; }",
		".rc-session { font-size:8.5pt; color:#555; margin-top:4px; }",

		// Student info grid
		".rc-info-table { width:100%; border-collapse:collapse; margin:8px 0; font-size:9.5pt; }",
		".rc-info-table td { padding:3px 7px; border:1px solid #bbb; }",
		".rc-info-table .lbl { font-weight:700; background:#f0f4ff; width:110px; }",
		".rc-info-table .val { font-weight:600; }",

		// Marks table
		".rc-marks-table { width:100%; border-collapse:collapse; margin:10px 0; font-size:9.5pt; }",
		".rc-marks-table th { background:#1a1a2e; color:#fff; padding:5px 7px;",
		"  text-align:center; border:1px solid #1a1a2e; font-size:8.5pt; font-weight:700; }",
		".rc-marks-table th.left { text-align:left; }",
		".rc-marks-table td { padding:4px 7px; border:1px solid #bbb; text-align:center; }",
		".rc-marks-table td.left { text-align:left; }",
		".rc-marks-table tbody tr:nth-child(even) { background:#f6f8fb; }",
		".rc-marks-table tfoot td { background:#1a1a2e; color:#fff; font-weight:700;",
		"  border:1px solid #1a1a2e; }",
		".t-pass { color:#28a745; font-weight:700; }",
		".t-fail { color:#dc3545; font-weight:700; }",

		// Summary bar
		".rc-summary { display:flex; border:1.5px solid #1a1a2e; margin:8px 0; }",
		".rc-sum-cell { flex:1; padding:6px 10px; text-align:center;",
		"  border-right:1px solid #adb5bd; }",
		".rc-sum-cell:last-child { border-right:none; }",
		".rc-sum-cell .lbl { display:block; font-size:7.5pt; color:#555;",
		"  text-transform:uppercase; letter-spacing:0.5px; }",
		".rc-sum-cell .val { display:block; font-size:12pt; font-weight:700; color:#1a1a2e; }",
		".rc-sum-cell .val.pass { color:#28a745; }",
		".rc-sum-cell .val.fail { color:#dc3545; }",

		// Signature area
		".rc-signatures { display:flex; justify-content:space-between;",
		"  margin-top:22px; padding-top:8px; border-top:1px dashed #aaa; font-size:8.5pt; }",
		".rc-sig { flex:1; text-align:center; }",
		".rc-sig-line { border-top:1px solid #333; margin:18px 12px 4px; }",

		"@media print {",
		"  body { padding:0; }",
		"  .result-card-wrap { margin:0 auto; }",
		"  -webkit-print-color-adjust: exact;",
		"  print-color-adjust: exact;",
		"}",
	].join("\n");

	// Inject preview styles once into the current Frappe page
	if (!document.getElementById("rc-preview-style")) {
		var s = document.createElement("style");
		s.id = "rc-preview-style";
		// preview: wrap cards in a white centered container
		s.innerHTML = RC_CSS + "\n"
			+ "#rc-cards-area .result-card-wrap {"
			+ "  box-shadow:0 1px 8px rgba(0,0,0,.12); margin-bottom:16px; }";
		document.head.appendChild(s);
	}

	// ── Page body ─────────────────────────────────────────────────────────────
	$(page.main).html(`
		<div style="padding:20px 24px">
			<div style="background:#f8f9fa;border:1px solid #e8eaed;border-radius:6px;
				padding:16px;margin-bottom:20px">
				<div style="display:flex;gap:16px;align-items:flex-end;flex-wrap:wrap">
					<div style="flex:1;min-width:170px">
						<div style="font-size:11px;font-weight:600;color:#6c757d;
							text-transform:uppercase;margin-bottom:4px">Exam</div>
						<select id="rc-exam" class="form-control" style="height:32px;font-size:13px">
							<option value="">Loading…</option>
						</select>
					</div>
					<div id="rc-class-wrap" style="flex:1;min-width:170px;display:none">
						<div style="font-size:11px;font-weight:600;color:#6c757d;
							text-transform:uppercase;margin-bottom:4px">Class / Program</div>
						<select id="rc-class" class="form-control" style="height:32px;font-size:13px">
							<option value="">— select class —</option>
						</select>
					</div>
					<div id="rc-section-wrap" style="flex:1;min-width:170px;display:none">
						<div style="font-size:11px;font-weight:600;color:#6c757d;
							text-transform:uppercase;margin-bottom:4px">Section</div>
						<select id="rc-section" class="form-control" style="height:32px;font-size:13px">
							<option value="">— select section —</option>
						</select>
					</div>
				</div>
			</div>
			<div id="rc-cards-area">
				<p style="color:#8d99a6;padding:20px 0">
					Select exam, class, and section, then click Load Results.
				</p>
			</div>
		</div>
	`);

	// ── Load exam names ───────────────────────────────────────────────────────
	frappe.call({
		method: "edvronix.edvronix_app.page.result_card.result_card.get_exam_names",
		callback: function (r) {
			var names = (r.message || []).map(function (x) { return x.assessment_name; });
			var $e = $("#rc-exam").empty().append('<option value="">— select exam —</option>');
			names.forEach(function (n) {
				$e.append(`<option value="${frappe.utils.escape_html(n)}">`
					+ `${frappe.utils.escape_html(n)}</option>`);
			});
		},
	});

	// ── Exam → load classes ───────────────────────────────────────────────────
	$(page.main).on("change", "#rc-exam", function () {
		var exam = $(this).val();
		$("#rc-class-wrap, #rc-section-wrap").hide();
		$("#rc-class").empty().append('<option value="">— select class —</option>');
		$("#rc-section").empty().append('<option value="">— select section —</option>');
		$("#rc-cards-area").html(
			'<p style="color:#8d99a6;padding:20px 0">Select class and section, then click Load Results.</p>'
		);
		current_data = null;
		if (!exam) return;

		frappe.call({
			method: "edvronix.edvronix_app.page.result_card.result_card.get_programs_for_exam",
			args: { exam_name: exam },
			callback: function (r) {
				var progs = r.message || [];
				var $c = $("#rc-class").empty().append('<option value="">— select class —</option>');
				progs.forEach(function (p) {
					$c.append(`<option value="${frappe.utils.escape_html(p.program)}">`
						+ `${frappe.utils.escape_html(p.program)}</option>`);
				});
				if (progs.length === 1) {
					$c.val(progs[0].program).trigger("change");
				}
				$("#rc-class-wrap").show();
			},
		});
	});

	// ── Class → load sections ─────────────────────────────────────────────────
	$(page.main).on("change", "#rc-class", function () {
		var prog = $(this).val();
		var exam = $("#rc-exam").val();
		$("#rc-section-wrap").hide();
		$("#rc-section").empty().append('<option value="">— select section —</option>');
		if (!prog || !exam) return;

		frappe.call({
			method: "edvronix.edvronix_app.page.result_card.result_card.get_sections_for_exam",
			args: { exam_name: exam, program: prog },
			callback: function (r) {
				var secs = r.message || [];
				var $s = $("#rc-section").empty();
				$s.append('<option value="ALL">— All Sections —</option>');
				secs.forEach(function (s) {
					$s.append(`<option value="${frappe.utils.escape_html(s.student_group)}">`
						+ `${frappe.utils.escape_html(s.student_group)}</option>`);
				});
				$("#rc-section-wrap").show();
			},
		});
	});

	// ── Load results ──────────────────────────────────────────────────────────
	function load_results() {
		var exam = $("#rc-exam").val();
		var section = $("#rc-section").val();
		if (!exam || !section) {
			frappe.msgprint(__("Please select an exam and section.")); return;
		}
		frappe.call({
			method: "edvronix.edvronix_app.page.result_card.result_card.get_result_cards_for_section",
			args: { exam_name: exam, student_group: section },
			freeze: true,
			freeze_message: __("Loading result cards…"),
			callback: function (r) {
				current_data = r.message;
				render_preview(current_data);
			},
		});
	}

	// ── Print: open clean popup and print only the cards ─────────────────────
	function print_all() {
		if (!current_data || !current_data.results || !current_data.results.length) {
			frappe.msgprint(__("Load results first.")); return;
		}
		var cards_html = build_cards_html(current_data);
		var win = window.open("", "_blank", "width=900,height=700");
		if (!win) {
			frappe.msgprint(__("Pop-up blocked. Please allow pop-ups for this site and try again."));
			return;
		}
		win.document.write(
			"<!DOCTYPE html><html><head>"
			+ "<meta charset='utf-8'>"
			+ "<title>Result Cards — " + frappe.utils.escape_html(
				(current_data.results[0] || {}).assessment_name || "") + "</title>"
			+ "<style>" + RC_CSS + "</style>"
			+ "</head><body>" + cards_html
			+ "<script>window.onload=function(){window.print();}<\/script>"
			+ "</body></html>"
		);
		win.document.close();
	}

	// ── Preview in page ───────────────────────────────────────────────────────
	function render_preview(data) {
		if (!data || !data.results || !data.results.length) {
			$("#rc-cards-area").html(
				'<p style="color:#8d99a6;padding:20px 0">No submitted results found for this selection.</p>'
			);
			return;
		}
		var cards = build_cards_html(data);
		$("#rc-cards-area").html(
			'<div style="padding:8px 0 14px;font-size:13px;color:#495057">'
			+ "<strong>" + data.results.length + "</strong> result card(s) loaded. "
			+ "Click <strong>Print All</strong> to print.</div>"
			+ cards
		);
	}

	// ── Build result card HTML (shared by preview + print popup) ─────────────
	function build_cards_html(data) {
		var info = data.school_info || {};
		var criteria = data.criteria || [];
		var total_max = criteria.reduce(function (s, c) { return s + (c.maximum_score || 0); }, 0);

		var logo = info.school_logo
			? '<div class="rc-logo"><img src="' + info.school_logo + '" alt="Logo"></div>'
			: "";

		return (data.results || []).map(function (r) {
			// Subject rows
			var subject_rows = criteria.map(function (c, idx) {
				var detail = (r.details || []).find(
					function (d) { return d.assessment_criteria === c.assessment_criteria; }
				) || {};
				var score = detail.score !== undefined && detail.score !== null ? detail.score : "—";
				var grade = detail.grade || "—";

				// Per-subject pass/fail based on passing_marks
				var remark = "";
				if (c.passing_marks) {
					remark = parseFloat(score || 0) >= c.passing_marks
						? '<span class="t-pass">Pass</span>'
						: '<span class="t-fail">Fail</span>';
				}

				return "<tr>"
					+ "<td>" + (idx + 1) + "</td>"
					+ "<td class='left'>" + frappe.utils.escape_html(c.assessment_criteria) + "</td>"
					+ "<td>" + c.maximum_score + "</td>"
					+ (c.passing_marks ? "<td>" + c.passing_marks + "</td>" : "")
					+ "<td style='font-weight:600'>" + score + "</td>"
					+ "<td>" + grade + "</td>"
					+ "<td>" + remark + "</td>"
					+ "</tr>";
			}).join("");

			// Extra "Passing" header column only when passing marks are present
			var has_passing = criteria.some(function (c) { return c.passing_marks; });
			var pass_th = has_passing ? "<th>Pass Marks</th>" : "";

			var res_cls = r.result === "PASS" ? "pass" : "fail";

			return '<div class="result-card-wrap">'

				// ── Header ────────────────────────────────────────────────────
				+ '<div class="rc-header">'
				+   logo
				+   '<div class="rc-school-info">'
				+     '<div class="rc-school-name">'
				+       frappe.utils.escape_html(info.school_name || "School")
				+     '</div>'
				+     (info.address
				?       '<div class="rc-school-addr">' + frappe.utils.escape_html(info.address) + '</div>'
				:       "")
				+     (info.phone
				?       '<div class="rc-school-addr">Tel: ' + frappe.utils.escape_html(info.phone) + '</div>'
				:       "")
				+     '<div class="rc-card-title">Student Result Card</div>'
				+     '<div class="rc-session">Exam: '
				+       frappe.utils.escape_html(r.assessment_name || "")
				+       ' &nbsp;|&nbsp; Session: '
				+       frappe.utils.escape_html(r.academic_year || "")
				+       ' &nbsp;|&nbsp; Term: '
				+       frappe.utils.escape_html(r.academic_term || "")
				+     '</div>'
				+   '</div>'
				+ '</div>'

				// ── Student info ──────────────────────────────────────────────
				+ '<table class="rc-info-table">'
				+   '<tr>'
				+     '<td class="lbl">Student Name</td>'
				+     '<td class="val">' + frappe.utils.escape_html(r.student_name || r.student) + '</td>'
				+     '<td class="lbl">Roll No.</td>'
				+     '<td class="val">' + frappe.utils.escape_html(r.roll_number || "—") + '</td>'
				+   '</tr>'
				+   '<tr>'
				+     '<td class="lbl">Class / Program</td>'
				+     '<td class="val">' + frappe.utils.escape_html(r.program || "—") + '</td>'
				+     '<td class="lbl">Section</td>'
				+     '<td class="val">' + frappe.utils.escape_html(r.student_group || "—") + '</td>'
				+   '</tr>'
				+ '</table>'

				// ── Marks table ───────────────────────────────────────────────
				+ '<table class="rc-marks-table">'
				+   '<thead><tr>'
				+     '<th style="width:28px">Sr.</th>'
				+     '<th class="left" style="min-width:120px">Subject</th>'
				+     '<th>Max Marks</th>'
				+     pass_th
				+     '<th>Obtained</th>'
				+     '<th>Grade</th>'
				+     '<th>Remarks</th>'
				+   '</tr></thead>'
				+   '<tbody>' + subject_rows + '</tbody>'
				+   '<tfoot><tr>'
				+     '<td colspan="2" class="left" style="padding-left:8px">TOTAL</td>'
				+     '<td>' + total_max + '</td>'
				+     (has_passing ? '<td>—</td>' : '')
				+     '<td>' + r.total_score + '</td>'
				+     '<td>' + (r.grade || "—") + '</td>'
				+     '<td class="t-' + res_cls + '">' + r.result + '</td>'
				+   '</tr></tfoot>'
				+ '</table>'

				// ── Summary bar ───────────────────────────────────────────────
				+ '<div class="rc-summary">'
				+   '<div class="rc-sum-cell">'
				+     '<span class="lbl">Percentage</span>'
				+     '<span class="val">' + r.percentage + '%</span>'
				+   '</div>'
				+   '<div class="rc-sum-cell">'
				+     '<span class="lbl">Grade</span>'
				+     '<span class="val">' + (r.grade || "—") + '</span>'
				+   '</div>'
				+   '<div class="rc-sum-cell">'
				+     '<span class="lbl">Position in Class</span>'
				+     '<span class="val">' + r.position + ' / ' + r.section_total + '</span>'
				+   '</div>'
				+   '<div class="rc-sum-cell">'
				+     '<span class="lbl">Result</span>'
				+     '<span class="val ' + res_cls + '">' + r.result + '</span>'
				+   '</div>'
				+ '</div>'

				// ── Signatures ────────────────────────────────────────────────
				+ '<div class="rc-signatures">'
				+   '<div class="rc-sig"><div class="rc-sig-line"></div>Class Teacher</div>'
				+   '<div class="rc-sig"><div class="rc-sig-line"></div>Principal</div>'
				+   '<div class="rc-sig"><div class="rc-sig-line"></div>Parent / Guardian</div>'
				+   '<div class="rc-sig"><div style="margin-top:18px">Date: ___________</div></div>'
				+ '</div>'

			+ '</div>';
		}).join("");
	}
};
