// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Parent Voucher Script Report"] = {
    onload: function (report) {
        report.page.add_inner_button(__("Print"), function () {

            let data = frappe.query_report.data || [];
            let filters = frappe.query_report.get_filter_values();

            if (!data.length) {
                frappe.msgprint(__("No data to print"));
                return;
            }

            let academic_year = filters.academic_year || "2025-26";
            let fee_month_filter = filters.month || "";

            // Group data by parent
            let grouped = {};
            data.forEach(row => {
                if (!grouped[row.parent_name]) {
                    grouped[row.parent_name] = {
                        parent_name: row.parent_name,
                        parent_id: row.guardian_id || "",
                        rows: []
                    };
                }
                grouped[row.parent_name].rows.push(row);
            });

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
                    @page { size: landscape; margin: 3mm; }
                    body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #2d3748; margin: 0; padding: 0; background: #fff; }

                    .page-wrapper { 
                        display: flex; 
                        flex-direction: row; 
                        justify-content: space-between; 
                        page-break-after: always; 
                        width: 100%;
                        height: 96vh; 
                        gap: 8px;
                        box-sizing: border-box;
                        padding: 5px;
                    }

                    .voucher-card { 
                        flex: 1;
                        border: 1.5px solid #1a3a5f; 
                        padding: 12px; 
                        position: relative; 
                        background-color: #fff;
                        box-sizing: border-box;
                        display: flex;
                        flex-direction: column;
                        height: 100%;
                    }

                    .voucher-card::before {
                        content: "AL-FAISAL"; 
                        position: absolute; 
                        top: 50%; left: 50%;
                        transform: translate(-50%, -50%) rotate(-45deg);
                        font-size: 50px; 
                        color: rgba(26, 58, 95, 0.03); 
                        font-weight: bold; 
                        z-index: 0;
                    }

                    .copy-tag { 
                        position: absolute; top: 0; right: 0; 
                        background: #1a3a5f; color: #fff; 
                        padding: 4px 12px; font-size: 8px; font-weight: bold; text-transform: uppercase; 
                        border-bottom-left-radius: 6px; z-index: 2;
                    }

                    .header { display: flex; justify-content: space-between; margin-top: 10px; align-items: flex-start; border-bottom: 2.5px solid #1a3a5f; padding-bottom: 8px; margin-bottom: 10px; position: relative; z-index:1; }
                    .school-brand { display: flex; align-items: center; }
                    .school-details { margin-left: 8px; }
                    .school-name { font-size: 11px; font-weight: 900; color: #1a3a5f; margin: 0; }
                    .contact-info { font-size: 6px; color: #4a5568; margin-top: 1px; line-height: 1.1; }

                    .challan-meta { text-align: right; }
                    .challan-title { font-size: 11px; font-weight: 700; color: #1a3a5f; }
                    
                    .bank-details-box {
                        background: #f1f5f9; border: 1px solid #1a3a5f; padding: 6px; 
                        margin-bottom: 10px; border-radius: 4px; display: flex; 
                        justify-content: space-between; align-items: center; z-index: 1; position: relative;
                    }

                    .info-bar { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 10px; z-index: 1; position: relative; }
                    .info-item { border-bottom: 1px solid #e2e8f0; padding: 2px 0; }
                    .info-label { font-size: 7px; color: #718096; text-transform: uppercase; font-weight: bold; }
                    .info-val { font-size: 8px; font-weight: 600; color: #1a202c; }

                    .student-table-container { flex-grow: 1; z-index: 1; position: relative; }
                    table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
                    th { background: #f8fafc; border: 1px solid #e2e8f0; padding: 4px; text-align: left; font-size: 7px; color: #1a3a5f; }
                    td { border: 1px solid #e2e8f0; padding: 4px; font-size: 7.5px; color: #2d3748; }

                    .footer-content { margin-top: auto; z-index: 1; position: relative; }
                    .footer-grid { display: flex; justify-content: space-between; gap: 8px; }
                    .policy-section { flex: 1.3; font-size: 7px; background: #fdf2f2; border: 1px solid #feb2b2; padding: 6px; border-radius: 4px; }
                    .summary-box { flex: 1; }
                    .amount-table { width: 100%; border: 1px solid #1a3a5f; border-radius: 4px; overflow: hidden; font-size: 8px; }
                    .amount-row { display: flex; justify-content: space-between; padding: 3px 5px; }
                    .amount-total { background: #1a3a5f; color: #fff; font-weight: bold; font-size: 9px; padding: 5px; }

                    .signatures { display: flex; justify-content: space-between; margin-top: 10px; }
                    .sig-box { border-top: 1px solid #1a202c; width: 45%; text-align: center; font-size: 7px; padding-top: 3px; font-weight: 600; }

                    @media print { .page-wrapper { height: 98vh; } }
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

                html += `<div class="page-wrapper">`;

                ["Bank Copy", "Office Copy", "Parent Copy"].forEach((copy) => {
                    html += `
                    <div class="voucher-card">
                        <div class="copy-tag">${copy}</div>
                        <div class="header">
                            <div class="school-brand">
                                <img src="/files/apple-icon-precomposed.png" style="height:35px;">
                                <div class="school-details">
                                    <h1 class="school-name">AL-FAISAL SCHOOL SYSTEM</h1>
                                    <div class="contact-info">
                                        Ghuman Town near Sabzi Mandi, Lahore Road,Sheikhupura<br>
                                        Ph: 056 3792 111 | Mob: +92 300 4468803<br>
                                        Email: accounts@alfss.edu.pk | Web: www.alfss.edu.pk

                                    </div>
                                </div>
                            </div>
                            <div class="challan-meta">
                                <div class="challan-title">FEE CHALLAN</div>
                                <div class="info-val" style="font-size: 7px;">${academic_year}</div>
                            </div>
                        </div>

                        <div class="bank-details-box">
                            <div>
                                <div style="font-size: 7px; color: #1a3a5f; font-weight: bold;">Bank Account Details</div>
                                <div style="font-size: 8px; font-weight: 700; color: #1a3a5f;">Faysal Bank Limited (IBB Sheikhupura)</div>
                                <div style="font-size: 7.5px;">A/C Title: Edvronix School System</div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 7px; font-weight: bold;">IBAN</div>
                                <div style="font-size: 8px; font-weight: bold; font-family: monospace;">PK87 FAYS 3056 3010 0000 8624</div>
                            </div>
                        </div>

                        <div class="info-bar">
                            <div class="info-item"><div class="info-label">Parent ID</div><div class="info-val">${parent.parent_id}</div></div>
                            <div class="info-item"><div class="info-label">Guardian</div><div class="info-val">${parent.parent_name}</div></div>
                            <div class="info-item"><div class="info-label">Billing Month</div><div class="info-val">${fee_month_text}</div></div>
                            <div class="info-item"><div class="info-label">Due Date</div><div class="info-val">${display_due_date}</div></div>
                        </div>

                        <div class="student-table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Student Name | Program</th>
                                        <th>Invoice</th>
                                        <th style="text-align:right">Amount</th>
                                    </tr>
                                </thead>
                                <tbody>`;

                    parent.rows.forEach(r => {
                        html += `
                        <tr>
                            <td><b>${r.student_name}</b><br><small>${r.program || "General"} | ${r.student_category || "N/A"}</small></td>
                            <td>${r.invoice_id || "N/A"}<br><small>${r.status}</small></td>
                            <td style="text-align:right; font-weight:600;">${format_currency(r.outstanding, "")}</td>
                        </tr>`;
                    });

                    html += `
                                </tbody>
                            </table>
                        </div>

                        <div class="footer-content">
                            <div class="footer-grid">
                                <div class="policy-section">
                                    <div style="color:#c53030; font-weight:bold; margin-bottom:2px;">Fine Policy</div>
                                    • Fine (11-20th): PKR 100/-<br>
                                    • Fine (After 20th): PKR 200/-
                                </div>
                                <div class="summary-box">
                                    <div class="amount-table">
                                        <div class="amount-row"><span>Arrears</span> <span>${format_currency(arrear_val, "")}</span></div>
                                        <div class="amount-row"><span>Current</span> <span>${format_currency(current_val, "")}</span></div>
                                        <div class="amount-total">
                                            <div style="display:flex; justify-content:space-between;"><span>TOTAL</span> <span>${format_currency(total_val, "")}</span></div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="signatures">
                                <div class="sig-box">Depositor Signature</div>
                                <div class="sig-box">Officer / Bank Stamp</div>
                            </div>
                        </div>
                    </div>`;
                });

                html += `</div>`;
            });

            html += `<script>window.onload=function(){window.print();}</script></body></html>`;

            let w = window.open("", "_blank");
            w.document.write(html);
            w.document.close();
        });
    }
};