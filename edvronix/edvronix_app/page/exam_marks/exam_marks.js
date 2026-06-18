// Pre-fill exam when navigated from Exam Setup Tool or Exam Setup form
frappe.pages["exam-marks"].on_page_show = function () {
	var pending = frappe._em_pending_exam;
	if (pending) {
		frappe._em_pending_exam = null;
		var page_obj = frappe.pages["exam-marks"];
		page_obj._pending_section = frappe._em_pending_section || null;
		frappe._em_pending_section = null;
		if (page_obj._exam_ctrl) {
			page_obj._exam_ctrl.set_value(pending);
		} else {
			page_obj._pending_exam = pending;
		}
		return;
	}
	// Fallback: route_options (used by "Enter Marks →" from Exam Setup progress table)
	if (frappe.route_options && frappe.route_options.exam_name) {
		var opts = frappe.route_options;
		frappe.route_options = null;
		var page_obj2 = frappe.pages["exam-marks"];
		page_obj2._pending_section = opts.section || null;
		if (page_obj2._exam_ctrl) {
			page_obj2._exam_ctrl.set_value(opts.exam_name);
		} else {
			page_obj2._pending_exam = opts.exam_name;
		}
	}
};

frappe.pages["exam-marks"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Marks Entry",
		single_column: true,
	});

	// State
	var current_plan = null;
	var current_criteria = [];
	var current_students = [];
	var section_plan_map = {};

	page.set_primary_action("Save All", save_all, "save");

	// ── Page structure ────────────────────────────────────────────────────────
	$(page.main).html(`
		<div style="padding:20px 24px">

			<!-- Exam link + auto-filled info -->
			<div style="background:#f8f9fa;border:1px solid #e8eaed;border-radius:6px;
				padding:16px 20px;margin-bottom:4px">
				<div style="display:flex;gap:20px;align-items:flex-end;flex-wrap:wrap">
					<div style="min-width:260px;flex:1" id="em-exam-link-wrap"></div>
					<div id="em-section-wrap" style="min-width:220px;flex:1;display:none">
						<div style="font-size:11px;font-weight:600;color:#6c757d;
							text-transform:uppercase;margin-bottom:4px">Section</div>
						<select id="em-section" class="form-control"
							style="height:32px;font-size:13px">
							<option value="">— select section —</option>
						</select>
					</div>
				</div>

				<!-- Auto-populated info strip (initially hidden) -->
				<div id="em-exam-info" style="display:none;margin-top:12px;padding-top:12px;
					border-top:1px solid #e8eaed;gap:24px;flex-wrap:wrap;font-size:12px">
					<div><span style="color:#8d99a6">Program:</span>
						<strong id="em-info-program" style="margin-left:4px">—</strong></div>
					<div><span style="color:#8d99a6">Academic Year:</span>
						<strong id="em-info-year" style="margin-left:4px">—</strong></div>
					<div><span style="color:#8d99a6">Term:</span>
						<strong id="em-info-term" style="margin-left:4px">—</strong></div>
					<div><span style="color:#8d99a6">Sections:</span>
						<strong id="em-info-sections" style="margin-left:4px">—</strong></div>
				</div>
			</div>

			<!-- Marks table area -->
			<div id="em-table-area" style="margin-top:16px">
				<p style="color:#8d99a6;padding:10px 0">
					Select an exam to get started.
				</p>
			</div>
		</div>
	`);

	// ── Build Exam Link control ───────────────────────────────────────────────
	var exam_ctrl = frappe.ui.form.make_control({
		df: {
			fieldtype: "Link",
			fieldname: "exam",
			label: "Exam",
			options: "Exam Setup",
			placeholder: "Search exam…",
		},
		parent: document.getElementById("em-exam-link-wrap"),
		render_input: true,
	});
	exam_ctrl.refresh();

	// ── Exam selected — called by df.change (covers both user pick & set_value) ─
	function on_exam_selected() {
		var exam_name = exam_ctrl.get_value();
		section_plan_map = {};
		current_plan = null;
		$("#em-section").empty().append('<option value="">— select section —</option>');
		$("#em-section-wrap").hide();
		$("#em-exam-info").hide();
		$("#em-table-area").html('<p style="color:#8d99a6;padding:10px 0">Select an exam to get started.</p>');

		if (!exam_name) return;

		frappe.call({
			method: "edvronix.edvronix_app.page.exam_marks.exam_marks.get_exam_details",
			args: { exam_name: exam_name },
			callback: function (r) {
				var data = r.message;
				var meta = data.meta || {};
				var sections = data.sections || [];

				// Show auto-populated info strip as flex
				$("#em-info-program").text(meta.program || "—");
				$("#em-info-year").text(meta.academic_year || "—");
				$("#em-info-term").text(meta.academic_term || "—");
				$("#em-info-sections").text(sections.length ? sections.length + " section(s)" : "—");
				$("#em-exam-info").css("display", "flex");

				// Populate section dropdown
				var $sec = $("#em-section").empty().append('<option value="">— select section —</option>');
				sections.forEach(function (s) {
					section_plan_map[s.student_group] = s.plan_name;
					$sec.append(`<option value="${frappe.utils.escape_html(s.student_group)}">`
						+ `${frappe.utils.escape_html(s.student_group)}</option>`);
				});

				// Auto-select: deep-link section > single section > nothing
				var pending_sec = frappe.pages["exam-marks"]._pending_section;
				frappe.pages["exam-marks"]._pending_section = null;
				if (pending_sec && section_plan_map[pending_sec]) {
					$sec.val(pending_sec);
					current_plan = section_plan_map[pending_sec];
					load_marks_table();
				} else if (sections.length === 1) {
					$sec.val(sections[0].student_group);
					current_plan = sections[0].plan_name;
					load_marks_table();
				}
				$("#em-section-wrap").show();
			},
		});
	}

	// Wire up: Frappe calls df.change for both user autocomplete pick AND set_value()
	exam_ctrl.df.change = on_exam_selected;

	// Store reference for on_page_show pre-fill
	frappe.pages["exam-marks"]._exam_ctrl = exam_ctrl;

	// Apply pending exam set before the control was ready
	if (frappe.pages["exam-marks"]._pending_exam) {
		var pending = frappe.pages["exam-marks"]._pending_exam;
		frappe.pages["exam-marks"]._pending_exam = null;
		setTimeout(function () { exam_ctrl.set_value(pending); }, 100);
	}

	// ── Section changed ──────────────────────────────────────────────────────
	$(page.main).on("change", "#em-section", function () {
		var sg = $(this).val();
		if (!sg) { current_plan = null; return; }
		current_plan = section_plan_map[sg];
		load_marks_table();
	});

	// ── Load marks table ──────────────────────────────────────────────────────
	function load_marks_table() {
		if (!current_plan) return;
		frappe.call({
			method: "edvronix.edvronix_app.page.exam_marks.exam_marks.get_marks_data",
			args: { plan_name: current_plan },
			callback: function (r) {
				current_criteria = r.message.criteria || [];
				current_students = r.message.students || [];
				render_table(r.message.plan);
			},
		});
	}

	// ── Render spreadsheet ────────────────────────────────────────────────────
	function render_table(plan_info) {
		if (!current_students.length) {
			$("#em-table-area").html('<p style="color:#8d99a6;padding:10px 0">No students in this section.</p>');
			return;
		}
		var max_score = plan_info.maximum_score || 0;
		var has_existing = current_students.some(function (s) { return s.result_name; });

		var th = current_criteria.map(function (c) {
			return `<th style="min-width:78px;text-align:center;white-space:nowrap">
				${frappe.utils.escape_html(c.assessment_criteria)}<br>
				<small style="font-weight:400;color:#8d99a6">(${c.maximum_score})</small>
			</th>`;
		}).join("");

		var rows = current_students.map(function (s, idx) {
			var cells = current_criteria.map(function (c) {
				var v = (s.scores && s.scores[c.assessment_criteria] !== undefined)
					? s.scores[c.assessment_criteria] : "";
				return `<td style="padding:3px 4px">
					<input type="number" class="form-control input-xs mark-input"
						data-student="${frappe.utils.escape_html(s.student)}"
						data-criteria="${frappe.utils.escape_html(c.assessment_criteria)}"
						data-max="${c.maximum_score}"
						min="0" max="${c.maximum_score}" step="0.5" value="${v}"
						style="text-align:right;min-width:62px;padding:2px 6px">
				</td>`;
			}).join("");

			var init_total = 0;
			if (s.scores) current_criteria.forEach(function (c) {
				init_total += parseFloat(s.scores[c.assessment_criteria] || 0);
			});
			var pct = max_score ? Math.round(init_total / max_score * 100) : 0;

			return `<tr>
				<td style="text-align:center;color:#8d99a6;padding:4px 8px">${idx + 1}</td>
				<td style="padding:4px 8px;white-space:nowrap">
					${frappe.utils.escape_html(s.student_name || s.student)}</td>
				${cells}
				<td class="row-total" style="text-align:center;font-weight:600;padding:4px 8px">
					${init_total || ""}</td>
				<td class="row-pct" style="text-align:center;color:#8d99a6;padding:4px 8px">
					${init_total ? pct + "%" : ""}</td>
			</tr>`;
		}).join("");

		$("#em-table-area").html(`
			<div style="font-size:12px;color:#8d99a6;margin-bottom:8px">
				${current_students.length} students &nbsp;·&nbsp;
				${current_criteria.length} subjects &nbsp;·&nbsp; Max: ${max_score}
				${has_existing
					? '&nbsp;·&nbsp;<span style="color:#e2a03f">⚠ Existing results will be overwritten on Save All</span>'
					: ""}
			</div>
			<div style="overflow-x:auto">
				<table class="table table-bordered table-condensed marks-table"
					style="font-size:13px;white-space:nowrap">
					<thead style="background:#f5f7fa;position:sticky;top:0;z-index:1">
						<tr>
							<th style="width:40px">#</th>
							<th style="min-width:160px">Student</th>
							${th}
							<th style="width:70px;text-align:center">
								Total<br><small style="font-weight:400;color:#8d99a6">(${max_score})</small>
							</th>
							<th style="width:55px;text-align:center">%</th>
						</tr>
					</thead>
					<tbody>${rows}</tbody>
				</table>
			</div>
		`);
	}

	// ── Auto-calc totals on input ─────────────────────────────────────────────
	$(page.main).on("input", ".mark-input", function () {
		var row = $(this).closest("tr");
		var total = 0;
		row.find(".mark-input").each(function () { total += parseFloat($(this).val() || 0); });
		var max = 0;
		current_criteria.forEach(function (c) { max += c.maximum_score; });
		row.find(".row-total").text(total || "");
		row.find(".row-pct").text(total && max ? Math.round(total / max * 100) + "%" : "");
	});

	// ── Tab navigation ────────────────────────────────────────────────────────
	$(page.main).on("keydown", ".mark-input", function (e) {
		if (e.key === "Tab") {
			e.preventDefault();
			var inputs = $(page.main).find(".mark-input");
			inputs.eq(inputs.index(this) + (e.shiftKey ? -1 : 1)).focus().select();
		}
	});

	// ── Save all ──────────────────────────────────────────────────────────────
	function save_all() {
		if (!current_plan) { frappe.msgprint(__("Select an exam and section first.")); return; }
		var student_scores = {};
		$(page.main).find(".mark-input").each(function () {
			var stu = $(this).data("student"), crit = $(this).data("criteria");
			if (!student_scores[stu]) student_scores[stu] = {};
			student_scores[stu][crit] = Math.min(
				parseFloat($(this).val() || 0),
				parseFloat($(this).data("max") || 0)
			);
		});
		var marks_data = Object.keys(student_scores).map(function (stu) {
			return { student: stu, scores: student_scores[stu] };
		});
		if (!marks_data.length) { frappe.msgprint(__("No marks to save.")); return; }
		frappe.call({
			method: "edvronix.edvronix_app.page.exam_marks.exam_marks.save_marks",
			freeze: true,
			freeze_message: __("Saving marks…"),
			args: { plan_name: current_plan, marks_data: JSON.stringify(marks_data) },
			callback: function (r) {
				frappe.show_alert({
					message: __("{0} result(s) saved.", [(r.message || {}).saved || 0]),
					indicator: "green",
				});
				load_marks_table();
			},
		});
	}
};
