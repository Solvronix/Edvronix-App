// Copyright (c) 2026, Solvronix and contributors
// For license information, please see license.txt

frappe.query_reports["Parent Wise Voucher in Bulk"] = {
    filters: [
        {
            "fieldname": "academic_year",
            "label": __("Academic Year"),
            "fieldtype": "Link",
            "options": "Academic Year",
            "default": frappe.defaults.get_user_default("academic_year")
        },
        {
            "fieldname": "month",
            "label": __("Month"),
            "fieldtype": "Select",
            "options": "January\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember"
        },
    ],
    onload: function (report) {
        report.page.add_inner_button(__("Print Bulk Voucher"), function () {

            let data = frappe.query_report.data || [];
            let filters = report.get_values();

            if (!data.length) {
                frappe.msgprint(__("No data to print. Please click 'Refresh' after selecting filters."));
                return;
            }

            generate_print_html(data, filters);
        });
    }
};

function generate_print_html(data, filters) {
    let academic_year = filters.academic_year || "2025-26";
    let fee_month_filter = filters.month || "";

    // Group data by UNIQUE Guardian ID instead of Name
    let grouped = {};
    data.forEach(row => {
        // We use guardian_id as the key to prevent mixing same-named parents
        let key = row.guardian_id;

        if (!grouped[key]) {
            grouped[key] = {
                parent_name: row.parent_name,
                parent_id: row.guardian_id,
                rows: []
            };
        }
        grouped[key].rows.push(row);
    });

    // ... (rest of your helper functions like getFeeMonth remain the same)

    // Get previous month of the due date
    function getFeeMonth(due_date) {
        if (!due_date) return "";
        let d = frappe.datetime.str_to_obj(due_date);
        d.setMonth(d.getMonth() - 1);
        return d.toLocaleString('default', { month: 'long', year: 'numeric' });
    }

    let html = `
    <html>
    <head>
        <title>Fee Challan - Al-Faisal School System</title>
        <style>
            body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #2d3748; margin: 0; padding: 10px; line-height: 1.3; }
			@media print {
    					.voucher-wrapper {
						page-break-inside: avoid;  /* Prevent splitting of each voucher */
						break-inside: avoid;       /* For modern browsers */
					}

			/* Optional: keep perforation line together with the card */
			.perforation-line {
				page-break-inside: avoid;
			}
		}
			.voucher-wrapper-parent {
				page-break-inside: avoid;
				break-inside: avoid;

            .voucher-wrapper { 
                border: 1.5px solid #1a3a5f; 
                padding: 20px; 
                margin-bottom: 20px; 
                position: relative; 
                background-color: #fff;
                box-sizing: border-box;
            }

            .voucher-wrapper::before {
                content: "AL-FAISAL"; 
                position: absolute; 
                top: 50%; 
                left: 50%;
                transform: translate(-50%, -50%) rotate(-45deg);
                font-size: 80px; 
                color: rgba(26, 58, 95, 0.03); 
                font-weight: bold; 
                z-index: 0;
            }

            .copy-tag { 
                position: absolute; 
                top: 0; right: 0; 
                background: #1a3a5f; color: #fff; 
                padding: 5px 18px; font-size: 10px; font-weight: bold; text-transform: uppercase; 
                letter-spacing: 1px; border-bottom-left-radius: 6px; 
            }

            .header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid #1a3a5f; padding-bottom: 10px; margin-bottom: 15px; position: relative; z-index:1; }
            .school-brand { display: flex; align-items: center; }
            .school-details { margin-left: 12px; }
            .school-name { font-size: 18px; font-weight: 900; color: #1a3a5f; margin: 0; letter-spacing: -0.5px; }
            .contact-info { font-size: 8.5px; color: #4a5568; margin-top: 2px; line-height: 1.2; }

            .challan-meta { text-align: right; margin-top: 8px; }
            .challan-title { font-size: 16px; font-weight: 700; color: #1a3a5f; margin-bottom: 3px; }
            
            .info-bar { display: grid; grid-template-columns: 1fr 2fr 1fr 1fr; gap: 10px; margin-bottom: 15px; }
            .info-item { border-bottom: 1px solid #e2e8f0; padding: 3px 0; }
            .info-label { font-size: 8px; color: #718096; text-transform: uppercase; font-weight: bold; }
            .info-val { font-size: 11px; font-weight: 600; color: #1a202c; }

            table { width: 100%; border-collapse: collapse; margin-bottom: 15px; z-index:1; position: relative; }
            th { background: #f8fafc; border: 1px solid #e2e8f0; padding: 6px; text-align: left; font-size: 9px; color: #1a3a5f; text-transform: uppercase; }
            td { border: 1px solid #e2e8f0; padding: 6px; font-size: 10px; color: #2d3748; }

            .footer-grid { display: flex; justify-content: space-between; gap: 10px; margin-top: auto; }
            .policy-section { flex: 1.5; font-size: 8.5px; background: #fdf2f2; border: 1px solid #feb2b2; padding: 8px; border-radius: 4px; }
            .policy-title { color: #c53030; font-weight: bold; margin-bottom: 3px; text-transform: uppercase; }
            
            .summary-box { flex: 1; }
            .amount-table { width: 100%; border: 1px solid #1a3a5f; border-radius: 4px; overflow: hidden; font-size: 10px; }
            .amount-row { display: flex; justify-content: space-between; padding: 4px 6px; }
            .amount-total { background: #1a3a5f; color: #fff; font-weight: bold; font-size: 12px; padding: 6px; }

            .signatures { display: flex; justify-content: space-between; margin-top: 15px; }
            .sig-box { border-top: 1px solid #1a202c; width: 120px; text-align: center; font-size: 9px; padding-top: 4px; font-weight: 600; }

            .perforation-line { border-top: 2px dashed #a0aec0; margin: 10px 0; text-align: center; position: relative; }
            .perforation-line span { position: absolute; top: -8px; left: 50%; transform: translateX(-50%); background: #fff; padding: 0 10px; font-size: 9px; color: #718096; font-weight: 600; }
            
            .bank-details-box {
                background: #f1f5f9; 
                border: 1px solid #1a3a5f; 
                padding: 8px; 
                margin-bottom: 12px; 
                border-radius: 4px; 
                display: flex; 
                justify-content: space-between; 
                align-items: center;
                position: relative;
                z-index: 1;
            }
        </style>
    </head>
    <body>`;

    Object.values(grouped).forEach(parent => {
        let first_row = parent.rows[0];
        let display_due_date = frappe.datetime.str_to_user(first_row.due_date);
        let fee_month_text = fee_month_filter ? fee_month_filter : getFeeMonth(first_row.due_date);

        let total_val = parent.rows.reduce((sum, r) => sum + flt(r.outstanding || 0), 0);
        let current_val = parent.rows.reduce((sum, r) => (r.due_date === first_row.due_date ? sum + flt(r.outstanding) : sum), 0);
        let arrear_val = total_val - current_val;
        html += `<div class="voucher-wrapper-parent">`; // Ensure each parent starts on a new page

        ["Parent Copy", "Office Copy"].forEach((copy, idx) => {
            html += `
            <div class="voucher-wrapper">
                <div class="copy-tag">${copy}</div>
                <div class="header">
                    <div class="school-brand">
                        <img src="/files/apple-icon-precomposed.png" style="height:55px;">
                        <div class="school-details">
                            <h1 class="school-name">AL-FAISAL SCHOOL SYSTEM</h1>
                            <div class="contact-info">
                                Ghuman Town near Sabzi Mandi, Lahore Road, Sheikhupura<br>
                                Ph: 056 3792 111 | Mob: +92 300 4468803 <br> Email: accounts@alfss.edu.pk | Web: https://www.alfss.edu.pk
                            </div>
                        </div>
                    </div>
                    <div class="challan-meta">
                        <div class="challan-title">FEE CHALLAN</div>
                        <div class="info-label">Academic Session</div>
                        <div class="info-val">${academic_year}</div>
                    </div>
                </div>

                <div class="bank-details-box">
                    <div>
                        <div style="font-size: 8px; color: #1a3a5f; font-weight: bold; text-transform: uppercase;">Bank Account Details</div>
                        <div style="font-size: 11px; font-weight: 700; color: #1a3a5f;">Faysal Bank Limited (IBB Sheikhupura)</div>
                        <div style="font-size: 10px; color: #2d3748;"><b>A/C Title:</b> Edvronix School System</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 8px; color: #1a3a5f; font-weight: bold; text-transform: uppercase;">IBAN</div>
                        <div style="font-size: 11px; font-weight: bold; font-family: monospace; letter-spacing: 0.5px;">PK87 FAYS 3056 3010 0000 8624</div>
                    </div>
                </div>

                <div class="info-bar">
                    <div class="info-item">
                        <div class="info-label">Parent ID</div>
                        <div class="info-val">${parent.parent_id}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Guardian / Parent Name</div>
                        <div class="info-val">${parent.parent_name}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Billing Month</div>
                        <div class="info-val">${fee_month_text}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Due Date</div>
                        <div class="info-val">${display_due_date}</div>
                    </div>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th style="width: 16%;">Student ID</th>
                            <th style="width: 16%;">Student Name & Program</th>
                            <th style="width: 20%;">Section</th>
                            <th>Invoice No.</th>
                            <th>Status</th>
                            <th style="text-align:right">Amount (PKR)</th>
                        </tr>
                    </thead>
                    <tbody>`;

            parent.rows.forEach(r => {
                html += `
                <tr>
                    <td>${r.student_id || "N/A"}</td>
                    <td><b>${r.student_name}</b><br><small style="color:#718096;">${r.program || "General Program"}</small></td>
                    <td>${r.student_category || "N/A"}</td>
                    <td>${r.invoice_id || "N/A"}</td>
                    <td>${r.status || "Unpaid"}</td>
                    <td style="text-align:right; font-weight:600;">${format_currency(r.outstanding, "")}</td>
                </tr>`;
            });

            html += `
                    </tbody>
                </table>

                <div class="footer-grid">
                    <div class="policy-section">
                        <div class="policy-title">Fine & Payment Policy</div>
                        • Payment must be deposited by the <b>Due Date</b>.<br>
                        • Late payment fine (11th to 20th): <b>PKR 100/-</b><br>
                        • Late payment fine (After 20th): <b>PKR 200/-</b>
                    </div>
                    <div class="summary-box">
                        <div class="amount-table">
                            <div class="amount-row"><span>Previous Arrears</span> <span>${format_currency(arrear_val, "")}</span></div>
                            <div class="amount-row"><span>Current Month Fee</span> <span>${format_currency(current_val, "")}</span></div>
                            <div class="amount-total">
                                <div style="font-size:9px; font-weight:normal; text-transform:uppercase;">Total Payable Amount</div>
                                <div style="display:flex; justify-content:space-between;"><span>PKR</span> <span>${format_currency(total_val, "")}</span></div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="signatures">
                    <div class="sig-box">Depositor Signature</div>
                    <div class="sig-box">Authorized Officer / Bank Stamp</div>
                </div>
            </div>`;

            if (idx === 0) {
                html += `<div class="perforation-line"><span>✂ SEPARATE HERE</span></div>`;
            }
        });
        html += `</div>`; // Close voucher-wrapper-parent
    });

    html += `<script>window.onload=function(){window.print();}</script></body></html>`;

    let w = window.open("", "_blank");
    w.document.write(html);
    w.document.close();
}