// When navigating here from the Exam Setup doctype form, pre-fill the exam name.
// frappe._es_pending_nav_exam avoids the routing conflict with the "Exam Setup" doctype.
frappe.pages["exam-tool"].on_page_show = function () {
	var pending = frappe._es_pending_nav_exam;
	if (pending) {
		frappe._es_pending_nav_exam = null;
		setTimeout(function () {
			$("#es-exam-name").val(pending).trigger("blur");
		}, 80);
	}
};

frappe.pages["exam-tool"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Exam Setup Tool",
		single_column: true,
	});

	page.set_primary_action("Create Exam Plans", create_exam_plans, "check");

	// ── Page HTML ─────────────────────────────────────────────────────────────
	$(page.main).html(`
		<div style="padding:20px 24px">

			<!-- Exam details form -->
			<div style="background:#f8f9fa;border:1px solid #e8eaed;border-radius:6px;padding:20px;margin-bottom:20px">
				<h6 style="font-weight:700;margin:0 0 16px 0;font-size:13px;color:#495057">EXAM DETAILS</h6>
				<div class="row">
					<div class="col-md-4" style="margin-bottom:12px">
						<label class="control-label" style="font-size:12px">Exam Name <span class="text-danger">*</span></label>
						<input id="es-exam-name" type="text" class="form-control"
							placeholder="e.g. First Term 2026" style="height:32px;font-size:13px">
					</div>
					<div class="col-md-4" style="margin-bottom:12px">
						<label class="control-label" style="font-size:12px">Academic Year <span class="text-danger">*</span></label>
						<select id="es-academic-year" class="form-control" style="height:32px;font-size:13px">
							<option value="">Loading…</option>
						</select>
					</div>
					<div class="col-md-4" style="margin-bottom:12px">
						<label class="control-label" style="font-size:12px">Academic Term <span class="text-danger">*</span></label>
						<select id="es-academic-term" class="form-control" style="height:32px;font-size:13px">
							<option value="">— select year first —</option>
						</select>
					</div>
					<div class="col-md-4" style="margin-bottom:12px">
						<label class="control-label" style="font-size:12px">Program <span class="text-danger">*</span></label>
						<select id="es-program" class="form-control" style="height:32px;font-size:13px">
							<option value="">Loading…</option>
						</select>
					</div>
					<div class="col-md-4" style="margin-bottom:12px">
						<label class="control-label" style="font-size:12px">Exam Date <span class="text-danger">*</span></label>
						<input id="es-exam-date" type="date" class="form-control" style="height:32px;font-size:13px">
					</div>
					<div class="col-md-4" style="margin-bottom:12px">
						<label class="control-label" style="font-size:12px">Grading Scale <span class="text-danger">*</span></label>
						<select id="es-grading-scale" class="form-control" style="height:32px;font-size:13px">
							<option value="">Loading…</option>
						</select>
					</div>
				</div>
			</div>

			<!-- Section Progress (shown after plans exist) -->
			<div id="es-progress-section" style="display:none;margin-bottom:20px">
				<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
					<h6 style="font-weight:700;margin:0;font-size:13px;color:#495057">SECTION PROGRESS</h6>
					<button class="btn btn-xs btn-default" id="es-refresh-progress">
						<i class="fa fa-refresh"></i> Refresh
					</button>
				</div>
				<table class="table table-bordered table-condensed" id="es-progress-table"
					style="font-size:13px;margin:0">
					<thead style="background:#f5f7fa">
						<tr>
							<th>Section</th>
							<th style="width:110px;text-align:center">Students</th>
							<th style="width:160px;text-align:center">Status</th>
							<th style="width:120px;text-align:center">Action</th>
						</tr>
					</thead>
					<tbody id="es-progress-tbody">
						<tr><td colspan="4" style="color:#8d99a6;text-align:center">Loading…</td></tr>
					</tbody>
				</table>
			</div>

			<!-- Two-column: subjects + sections -->
			<div class="row">
				<div class="col-md-7" style="margin-bottom:16px">
					<div style="background:#fff;border:1px solid #e8eaed;border-radius:6px;padding:16px">
						<h6 style="font-weight:700;margin:0 0 12px 0;font-size:13px;color:#495057">SUBJECTS</h6>
						<table class="table table-bordered table-condensed" id="es-subjects-table"
							style="font-size:13px;margin-bottom:8px">
							<thead style="background:#f5f7fa">
								<tr>
									<th>Assessment Criteria (Subject)</th>
									<th style="width:110px">Max Marks</th>
									<th style="width:110px">Passing Marks</th>
									<th style="width:32px"></th>
								</tr>
							</thead>
							<tbody id="es-subjects-tbody"></tbody>
						</table>
						<button class="btn btn-xs btn-default" id="es-add-subject">
							<i class="fa fa-plus"></i> Add Subject
						</button>
					</div>
				</div>

				<div class="col-md-5" style="margin-bottom:16px">
					<div style="background:#fff;border:1px solid #e8eaed;border-radius:6px;padding:16px">
						<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
							<h6 style="font-weight:700;margin:0;font-size:13px;color:#495057">SECTIONS</h6>
							<div style="font-size:12px">
								<a href="#" id="es-select-all">Select All</a> &nbsp;|&nbsp;
								<a href="#" id="es-deselect-all">Deselect All</a>
							</div>
						</div>
						<div id="es-sections-list">
							<p class="text-muted" style="font-size:12px">Select a program to see sections.</p>
						</div>
					</div>
				</div>
			</div>

		</div>
	`);

	// ── Populate dropdowns on load ────────────────────────────────────────────
	frappe.db.get_list("Academic Year", { limit: 20, order_by: "year_start_date desc" }).then(function (rows) {
		var $ay = $("#es-academic-year").empty().append('<option value="">— select —</option>');
		rows.forEach(function (r) {
			$ay.append(`<option value="${frappe.utils.escape_html(r.name)}">${frappe.utils.escape_html(r.name)}</option>`);
		});
	});

	frappe.db.get_list("Program", { limit: 50, order_by: "name" }).then(function (rows) {
		var $p = $("#es-program").empty().append('<option value="">— select —</option>');
		rows.forEach(function (r) {
			$p.append(`<option value="${frappe.utils.escape_html(r.name)}">${frappe.utils.escape_html(r.name)}</option>`);
		});
	});

	frappe.db.get_list("Grading Scale", { limit: 20, order_by: "name" }).then(function (rows) {
		var $gs = $("#es-grading-scale").empty().append('<option value="">— select —</option>');
		rows.forEach(function (r) {
			$gs.append(`<option value="${frappe.utils.escape_html(r.name)}">${frappe.utils.escape_html(r.name)}</option>`);
		});
	});

	// ── Academic year → load terms ───────────────────────────────────────────
	$(page.main).on("change", "#es-academic-year", function () {
		var ay = $(this).val();
		var $at = $("#es-academic-term").empty().append('<option value="">— loading… —</option>');
		if (!ay) { $at.empty().append('<option value="">— select year first —</option>'); return; }
		frappe.db.get_list("Academic Term", {
			filters: { academic_year: ay }, limit: 10, order_by: "term_start_date"
		}).then(function (rows) {
			$at.empty().append('<option value="">— select term —</option>');
			rows.forEach(function (r) {
				$at.append(`<option value="${frappe.utils.escape_html(r.name)}">${frappe.utils.escape_html(r.name)}</option>`);
			});
			// Apply pending term set by prefill_from_exam_setup
			var pending = frappe.pages["exam-tool"]._pending_term;
			if (pending) {
				frappe.pages["exam-tool"]._pending_term = null;
				$at.val(pending);
			}
		});
	});

	// ── Program → load sections ──────────────────────────────────────────────
	$(page.main).on("change", "#es-program", function () {
		load_sections();
	});

	function load_sections() {
		var prog = $("#es-program").val();
		var ay = $("#es-academic-year").val();
		if (!prog) {
			$("#es-sections-list").html('<p class="text-muted" style="font-size:12px">Select a program to see sections.</p>');
			return;
		}
		frappe.call({
			method: "edvronix.edvronix_app.page.exam_tool.exam_tool.get_sections",
			args: { program: prog, academic_year: ay || "" },
			callback: function (r) {
				var sections = r.message || [];
				if (!sections.length) {
					$("#es-sections-list").html('<p class="text-muted" style="font-size:12px">No student groups found for this program.</p>');
					return;
				}
				var html = sections.map(function (s) {
					var label = frappe.utils.escape_html(s.student_group_name || s.name);
					var val = frappe.utils.escape_html(s.name);
					return `<div style="margin-bottom:6px">
						<label style="font-weight:normal;cursor:pointer;font-size:13px">
							<input type="checkbox" class="es-section-cb" value="${val}" checked>
							&nbsp;${label}
						</label>
					</div>`;
				}).join("");
				$("#es-sections-list").html(html);
			},
		});
	}

	$(page.main).on("click", "#es-select-all", function (e) {
		e.preventDefault(); $(".es-section-cb").prop("checked", true);
	});
	$(page.main).on("click", "#es-deselect-all", function (e) {
		e.preventDefault(); $(".es-section-cb").prop("checked", false);
	});

	// ── Section Progress table ────────────────────────────────────────────────
	function load_progress(exam_name) {
		if (!exam_name) return;
		frappe.call({
			method: "edvronix.edvronix_app.page.exam_tool.exam_tool.get_section_progress",
			args: { exam_name: exam_name },
			callback: function (r) {
				var rows = r.message || [];
				if (!rows.length) {
					$("#es-progress-section").hide();
					return;
				}
				var STATUS_COLOR = { "Pending": "#dc3545", "Marks Entered": "#e2a03f", "Result Generated": "#2e7d32" };
				var STATUS_BG   = { "Pending": "#fff5f5", "Marks Entered": "#fff8e1", "Result Generated": "#f1f8f1" };
				var tbody = rows.map(function (row) {
					var color = STATUS_COLOR[row.status] || "#6c757d";
					var bg    = STATUS_BG[row.status] || "#f8f9fa";
					var pct   = row.total_students
						? Math.round(row.submitted_results / row.total_students * 100) : 0;
					var progress_bar = row.total_students ? `
						<div style="background:#e9ecef;border-radius:3px;height:4px;margin-top:3px">
							<div style="background:${color};width:${pct}%;height:4px;border-radius:3px"></div>
						</div>` : "";
					return `<tr style="background:${bg}">
						<td style="font-weight:500">${frappe.utils.escape_html(row.section)}</td>
						<td style="text-align:center">
							${row.submitted_results} / ${row.total_students}
							${progress_bar}
						</td>
						<td style="text-align:center">
							<span style="color:${color};font-weight:600;font-size:12px">
								${frappe.utils.escape_html(row.status)}
							</span>
						</td>
						<td style="text-align:center">
							<a href="#" class="es-enter-marks-link btn btn-xs btn-primary"
								data-exam="${frappe.utils.escape_html(exam_name)}"
								data-section="${frappe.utils.escape_html(row.section)}"
								style="font-size:11px">
								Enter Marks →
							</a>
						</td>
					</tr>`;
				}).join("");
				$("#es-progress-tbody").html(tbody);
				$("#es-progress-section").show();
			},
		});
	}

	// Refresh button
	$(page.main).on("click", "#es-refresh-progress", function () {
		load_progress($("#es-exam-name").val().trim());
	});

	// "Enter Marks →" deep-link
	$(page.main).on("click", ".es-enter-marks-link", function (e) {
		e.preventDefault();
		frappe._em_pending_exam = $(this).data("exam");
		frappe._em_pending_section = $(this).data("section");
		frappe.set_route("exam-marks");
	});

	// When exam_name loses focus: auto-fill all fields from existing Exam Setup record
	$(page.main).on("blur", "#es-exam-name", function () {
		var name = $(this).val().trim();
		if (!name) return;
		frappe.call({
			method: "edvronix.edvronix_app.page.exam_tool.exam_tool.get_exam_setup",
			args: { exam_name: name },
			callback: function (r) {
				if (r.message) {
					prefill_from_exam_setup(r.message);
				}
				load_progress(name);
			},
		});
	});

	function prefill_from_exam_setup(data) {
		if (data.academic_year) {
			var $ay = $("#es-academic-year");
			if ($ay.find('option[value="' + data.academic_year + '"]').length) {
				frappe.pages["exam-tool"]._pending_term = data.academic_term || null;
				$ay.val(data.academic_year).trigger("change");
			}
		}
		if (data.program) {
			var $prog = $("#es-program");
			if ($prog.find('option[value="' + data.program + '"]').length) {
				$prog.val(data.program);
				load_sections();
			}
		}
		if (data.exam_date) {
			$("#es-exam-date").val(data.exam_date);
		}
		if (data.grading_scale) {
			var $gs = $("#es-grading-scale");
			if ($gs.find('option[value="' + data.grading_scale + '"]').length) {
				$gs.val(data.grading_scale);
			}
		}
		if (data.subjects && data.subjects.length) {
			$("#es-subjects-tbody").empty();
			data.subjects.forEach(function (s) {
				add_subject_row(s.assessment_criteria, s.max_marks, s.passing_marks);
			});
		}
	}

	// ── Default subjects ──────────────────────────────────────────────────────
	var DEFAULT_SUBJECTS = [
		["English", 100, 40], ["Mathematics", 100, 40], ["Urdu", 100, 40],
		["Science", 100, 40], ["Social Studies", 100, 40], ["Islamiat", 100, 40],
	];
	DEFAULT_SUBJECTS.forEach(function (s) { add_subject_row(s[0], s[1], s[2]); });

	function add_subject_row(criteria, max, passing) {
		criteria = criteria || ""; max = max !== undefined ? max : 100; passing = passing !== undefined ? passing : 40;
		$("#es-subjects-tbody").append(`<tr>
			<td><input type="text" class="form-control input-xs es-criteria"
				placeholder="Subject name" value="${frappe.utils.escape_html(criteria)}"></td>
			<td><input type="number" class="form-control input-xs es-max" min="0" step="0.5" value="${max}"></td>
			<td><input type="number" class="form-control input-xs es-passing" min="0" step="0.5" value="${passing}"></td>
			<td style="text-align:center;vertical-align:middle">
				<a class="es-remove-row text-danger" style="cursor:pointer;font-size:16px;line-height:1">&times;</a>
			</td>
		</tr>`);
	}

	$(page.main).on("click", "#es-add-subject", function () { add_subject_row(); });
	$(page.main).on("click", ".es-remove-row", function () { $(this).closest("tr").remove(); });

	// ── Create exam plans ─────────────────────────────────────────────────────
	function create_exam_plans() {
		var exam_name = $("#es-exam-name").val().trim();
		var ay = $("#es-academic-year").val();
		var at = $("#es-academic-term").val();
		var prog = $("#es-program").val();
		var exam_date = $("#es-exam-date").val();
		var gs = $("#es-grading-scale").val();

		if (!exam_name || !ay || !at || !prog || !exam_date || !gs) {
			frappe.msgprint(__("Please fill all required fields: Exam Name, Academic Year, Term, Program, Date, Grading Scale."));
			return;
		}

		var subjects = [];
		$("#es-subjects-tbody tr").each(function () {
			var c = $(this).find(".es-criteria").val().trim();
			if (c) subjects.push({
				assessment_criteria: c,
				max_marks: parseFloat($(this).find(".es-max").val()) || 0,
				passing_marks: parseFloat($(this).find(".es-passing").val()) || 0,
			});
		});
		if (!subjects.length) { frappe.msgprint(__("Add at least one subject.")); return; }

		var sections = [];
		$(".es-section-cb:checked").each(function () { sections.push($(this).val()); });
		if (!sections.length) { frappe.msgprint(__("Select at least one section.")); return; }

		frappe.call({
			method: "edvronix.edvronix_app.page.exam_tool.exam_tool.create_exam_plans",
			freeze: true,
			freeze_message: __("Creating Assessment Plans…"),
			args: {
				exam_name: exam_name,
				academic_year: ay,
				academic_term: at,
				program: prog,
				sections: JSON.stringify(sections),
				exam_date: exam_date,
				grading_scale: gs,
				subjects: JSON.stringify(subjects),
			},
			callback: function (r) {
				var created = r.message || [];
				if (created.length) {
					var d = new frappe.ui.Dialog({
						title: __("Exam Plans Created"),
						fields: [{
							fieldtype: "HTML",
							options: `<div style="text-align:center;padding:16px 0 8px">
								<div style="font-size:48px;line-height:1;color:#2e7d32">✓</div>
								<p style="font-size:15px;margin:14px 0 4px">
									<strong>${created.length}</strong> Assessment Plan(s) created for
								</p>
								<p style="font-size:17px;font-weight:700;color:#5e64ff;margin:0 0 8px">
									${frappe.utils.escape_html(exam_name)}
								</p>
								<p style="font-size:12px;color:#8d99a6">
									${created.map(function(n) { return frappe.utils.escape_html(n); }).join(" &nbsp;·&nbsp; ")}
								</p>
							</div>`,
						}],
						primary_action_label: __("Enter Marks Now →"),
						primary_action: function () {
							d.hide();
							frappe._em_pending_exam = exam_name;
							frappe.set_route("exam-marks");
						},
						secondary_action_label: __("Done"),
						secondary_action: function () { d.hide(); },
					});
					d.show();
					load_progress(exam_name);
				} else {
					frappe.msgprint(__("No new plans created — plans for the selected sections may already exist."));
				}
			},
		});
	}
};
