frappe.query_reports["Fee Vouher in Bulk with Bank"] = {
    filters: [
        {
            "fieldname": "academic_year",
            "label": __("Academic Year"),
            "fieldtype": "Link",
            "options": "Academic Year",
            "reqd": 1
        },
        {
            "fieldname": "month",
            "label": __("Month"),
            "fieldtype": "Select",
            "options": "January\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember",
            "reqd": 1
        },
        {
            "fieldname": "guardian",
            "label": __("Guardian"),
            "fieldtype": "Link",
            "options": "Guardian"
        }
    ],

    onload: function (report) {

        report.page.set_primary_action(__('Refresh'), function () {
            let filters = report.get_values();

            if (!filters.month) {
                frappe.msgprint(__('Please select Month first.'));
                return;
            }

            report.refresh();
        });

        report.page.add_inner_button(__("Print Bulk Voucher"), function () {
            let data = frappe.query_report.data || [];
            let filters = report.get_values();

            if (!filters.month) {
                frappe.msgprint(__('Please select Month first.'));
                return;
            }

            if (!data.length) {
                frappe.msgprint(__("Please click Refresh after selecting filters."));
                return;
            }

            generate_print_html(data, filters);
        });
    }
};


function generate_print_html(data, filters) {
    frappe.call({
        method: "edvronix.edvronix_app.doctype.edvronix_settings.edvronix_settings.get_edvronix_settings",
        callback: function (r) {
            let settings = r.message || {};
            _build_and_print(data, filters, settings);
        }
    });
}


function _build_and_print(data, filters, settings) {
    let academic_year = filters.academic_year || "";
    let fee_month_filter = filters.month || "";

    // School details from Edvronix Settings
    
            // Convert hex color to "R, G, B" for rgba() watermark usage
            function _hexToRgb(hex) {
                let r = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
                return r ? `${parseInt(r[1],16)}, ${parseInt(r[2],16)}, ${parseInt(r[3],16)}` : "26, 58, 95";
            }
            let primary_color = settings.primary_color || "#1a365d";
            let primary_rgb   = _hexToRgb(primary_color);

            let school_name    = settings.school_name    || "School";
    let school_logo    = settings.school_logo    || "";
    let watermark_text = settings.watermark_text || school_name;
    let address        = settings.address        || "";
    let phone          = settings.phone          || "";
    let mobile         = settings.mobile         || "";
    let email          = settings.email          || "";
    let website        = settings.website        || "";

    // Bank details from Edvronix Settings
    let bank_name      = settings.bank_name      || "";
    let branch_name    = settings.branch_name    || "";
    let account_title  = settings.account_title  || "";
    let account_number = settings.account_number || "";
    let iban           = settings.iban           || "";

    // Late fee policy from Edvronix Settings
    let late_fee_10 = settings.late_fee_after_10 || 100;
    let late_fee_20 = settings.late_fee_after_20 || 200;
    let late_fee_policy_text = settings.late_fee_policy_text
        ? settings.late_fee_policy_text
            .split('\n')
            .filter(l => l.trim())
            .map(l => `• ${l.trim()}`)
            .join('<br>')
        : `• After 10th date charges will be PKR ${late_fee_10}/-<br>• After 20th date charges will be PKR ${late_fee_20}/-`;

    // Item abbreviations from Edvronix Settings (key→value dict)
    let ITEM_ABBR = settings.item_abbreviations || {};

    // Contact info line
    let contact_parts = [];
    if (phone)   contact_parts.push(`Ph: ${phone}`);
    if (mobile)  contact_parts.push(`Mob: ${mobile}`);
    let contact_line1 = contact_parts.join(' | ');

    let contact_parts2 = [];
    if (email)   contact_parts2.push(`Email: ${email}`);
    if (website) contact_parts2.push(`Web: ${website}`);
    let contact_line2 = contact_parts2.join(' | ');

    // Bank display line
    let bank_display = bank_name + (branch_name ? ` (${branch_name})` : '');

    function getAmountDisplay(r) {
        let paid = flt(r.paid_amount || 0);
        let outstanding = flt(r.outstanding || 0);
        let total = paid + outstanding;

        if (outstanding === 0 && paid > 0) {
            return `<span style="color:green;">Paid: ${format_currency(paid, "")}</span>`;
        }
        if (paid === 0 && outstanding > 0) {
            return `<span>${format_currency(outstanding, "")}</span>`;
        }
        if (paid > 0 && outstanding > 0) {
            return `
            <div style="color:green;">Paid: ${format_currency(paid, "")}</div>
            <div>${format_currency(outstanding, "")}</div>
        `;
        }
        return format_currency(total, "");
    }

    // Group data by unique Guardian ID
    let grouped = {};
    data.forEach(row => {
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

    function getFeeMonth(due_date) {
        if (!due_date) return "";
        let d = frappe.datetime.str_to_obj(due_date);
        d.setMonth(d.getMonth() - 1);
        return d.toLocaleString('default', { month: 'long', year: 'numeric' });
    }

    let html = `
    <html>
    <head>
        <style>
            @page { size: landscape; margin: 5mm; }
            body {
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                color: #2d3748;
                margin: 0;
                padding: 0;
                background-color: #f7fafc;
            }

            .page-wrapper {
                display: flex;
                flex-direction: row;
                justify-content: space-between;
                page-break-after: always;
                width: 100%;
                height: 94vh;
                gap: 10px;
                box-sizing: border-box;
            }

            .voucher-wrapper {
                flex: 1;
                border: 1.5px solid ${primary_color};
                padding: 12px;
                position: relative;
                background-color: #fff;
                box-sizing: border-box;
                display: flex;
                flex-direction: column;
                height: 100%;
            }

            .voucher-wrapper::before {
                content: "${watermark_text}";
                position: absolute;
                top: 50%; left: 50%;
                transform: translate(-50%, -50%) rotate(-45deg);
                font-size: 60px;
                color: ${`rgba(${primary_rgb}, 0.03)`};
                font-weight: bold;
                z-index: 0;
            }

            .copy-tag {
                position: absolute; top: 0; right: 0;
                background: ${primary_color}; color: #fff;
                padding: 4px 12px; font-size: 9px; font-weight: bold; text-transform: uppercase;
                border-bottom-left-radius: 8px; z-index: 2;
            }

            .header { display: flex; margin-top: 10px; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid ${primary_color}; padding-bottom: 8px; margin-bottom: 5px; position: relative; z-index:1; }
            .school-name { font-size: 13px; font-weight: 900; color: ${primary_color}; margin: 0; }
            .contact-info { font-size: 7.5px; color: #4a5568; margin-top: 2px; line-height: 1.2; }
            .challan-title { font-size: 13px; font-weight: 700; color: ${primary_color}; text-align: right; }

            .bank-details-box {
                background: #f1f5f9; border: 1px solid ${primary_color}; padding: 6px;
                margin-bottom: 10px; border-radius: 4px; display: flex;
                justify-content: space-between; font-size: 8px; position: relative; z-index: 1;
            }

            .info-bar { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 10px; position: relative; z-index: 1; }
            .info-item { border-bottom: 1px solid #e2e8f0; padding: 3px 0; }
            .info-label { font-size: 8px; color: #718096; text-transform: uppercase; font-weight: bold; }
            .info-val { font-size: 9px; font-weight: 600; color: #1a202c; }

            .student-table-container { flex-grow: 1; z-index: 1; position: relative; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
            th { background: #f8fafc; border: 1px solid #e2e8f0; padding: 6px; text-align: left; font-size: 8px; color: ${primary_color}; text-transform: uppercase; }
            td { border: 1px solid #e2e8f0; padding: 6px; font-size: 9px; color: #2d3748; }

            .footer-content { margin-top: auto; }
            .footer-grid { display: flex; justify-content: space-between; gap: 8px; }
            .policy-section { flex: 1.2; font-size: 8px; background: #fdf2f2; border: 1px solid #feb2b2; padding: 8px; border-radius: 4px; }
            .amount-table { width: 100%; border: 1px solid ${primary_color}; border-radius: 4px; overflow: hidden; font-size: 10px; }
            .amount-row { display: flex; justify-content: space-between; padding: 4px 6px; }
            .amount-total { background: ${primary_color}; color: #fff; font-weight: bold; padding: 6px; }

            .signatures { display: flex; justify-content: space-between; margin-top: 15px; }
            .sig-box { border-top: 1.5px solid #1a202c; width: 45%; text-align: center; font-size: 9px; padding-top: 4px; font-weight: 600; }

            @media print {
                body { background-color: #fff; }
                .page-wrapper { height: 98vh; page-break-after: always; }
            }
        </style>
    </head>
    <body>`;


    Object.values(grouped).forEach(parent => {
        let first_row = parent.rows[0];
        let display_due_date = frappe.datetime.str_to_user(first_row.due_date);
        let fee_month_text = fee_month_filter ? fee_month_filter : getFeeMonth(first_row.due_date);

        let arrear_val = 0;
        let current_val = 0;
        let processed_invoices = new Set();

        parent.rows.forEach(r => {
            let outstanding = flt(r.outstanding || 0);
            current_val += outstanding;

            if (!processed_invoices.has(r.invoice_id)) {
                arrear_val += flt(r.arrears || 0);
                processed_invoices.add(r.invoice_id);
            }
        });

        let total_val = current_val + arrear_val;

        let rowCount = parent.rows.length;
        let zoom = rowCount <= 4 ? 1 : Math.max(0.55, 1 - (rowCount - 4) * 0.06);

        html += `<div class="page-wrapper">`;

        ["Bank Copy", "Office Copy", "Parent Copy"].forEach((copy_name) => {
            html += `
            <div class="voucher-wrapper" style="zoom: ${zoom};">
                <div class="copy-tag">${copy_name}</div>
                <div class="header">
                    <div style="display:flex; align-items:center;">
                        ${school_logo ? `<img src="${school_logo}" style="height:45px; margin-right:10px;">` : ''}
                        <div class="school-details">
                            <h1 class="school-name">${school_name}</h1>
                            <div class="contact-info">
                                ${address ? address + '<br>' : ''}
                                ${contact_line1 ? contact_line1 + '<br>' : ''}
                                ${contact_line2 || ''}
                            </div>
                        </div>
                    </div>
                    <div style="text-align:right">
                        <div class="challan-title">FEE CHALLAN</div>
                        <div style="font-size:9px; font-weight:bold;">${academic_year}</div>
                    </div>
                </div>

                <div class="bank-details-box">
                    <div>
                        <div style="font-size: 8px; color: ${primary_color}; font-weight: bold; text-transform: uppercase;">Bank Account Details</div>
                        <div style="font-size: 11px; font-weight: 700; color: ${primary_color};">${bank_display}</div>
                        <div style="font-size: 10px; color: #2d3748;"><b>A/C Title:</b> ${account_title}</div>
                        ${/* account_number ? `<div style="font-size: 10px; color: #2d3748;"><b>A/C No:</b> ${account_number}</div>` : */ ''}
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 8px; color: ${primary_color}; font-weight: bold; text-transform: uppercase;">IBAN</div>
                        <div style="font-size: 11px; font-weight: bold; font-family: monospace;">${iban}</div>
                    </div>
                </div>

                <div class="info-bar">
                    <div class="info-item"><div class="info-label">Parent ID</div><div class="info-val">${parent.parent_id}</div></div>
                    <div class="info-item"><div class="info-label">Billing Month</div><div class="info-val">${fee_month_text}</div></div>
                    <div class="info-item"><div class="info-label">Guardian Name</div><div class="info-val">${parent.parent_name}</div></div>
                    <div class="info-item"><div class="info-label">Due Date</div><div class="info-val">${display_due_date}</div></div>
                </div>

                <div class="student-table-container">
                    <table>
                        <thead>
                            <tr>
                                <th style="width: 28%;">Student / Class / Section</th>
                                <th>Invoice / Status</th>
                                <th>Item Details</th>
                                <th style="text-align:right">Amount</th>
                                <th style="text-align:right">Arrears</th>
                            </tr>
                        </thead>
                        <tbody>`;

            parent.rows.forEach(r => {
                let items_html = "";
                if (r.invoice_items) {
                    let rows = r.invoice_items.split('::').map(item_group => {
                        let [name, amt] = item_group.split('|');
                        return `<div style="display:flex; justify-content:space-between; font-size:8px; color:#4a5568;">
                        <span>${name}</span>
                        <span style="font-weight:bold;">${flt(amt).toLocaleString()}</span>
                    </div>`;
                    }).join('');
                    items_html = `<div>${rows}</div>`;
                } else {
                    items_html = "<div style='font-size:8px; color:red;'>No items found</div>";
                }

                let arrears_html = "";
                if (r.arrears_detail) {
                    arrears_html = r.arrears_detail.split('::').map(item_group => {
                        let [name, amt, mon] = item_group.split('|');
                        let label = (ITEM_ABBR[name] || name) + (mon ? ` (${mon})` : '');
                        return `<div style="display:flex; justify-content:space-between; font-size:8px; color:#c53030;">
                        <span>${label}</span>
                        <span style="font-weight:bold; margin-left:4px;">${flt(amt).toLocaleString()}</span>
                    </div>`;
                    }).join('');
                }

                html += `
    <tr>
        <td style="vertical-align: top;">
            <b>${r.student_name}</b><br>
            <small>${r.program || "General"}</small> <br> <small>${r.student_category || "General"}</small>
        </td>
        <td style="vertical-align: top; background-color: #fafafa;">
            <b>${r.invoice_id || "N/A"}</b><br>
            <small><i>${r.status || "N/A"}</i></small>
        </td>
        <td style="vertical-align: top;">
            ${items_html}
        </td>
        <td style="text-align:right; font-weight:700; vertical-align: top; font-size: 10px;">
            ${getAmountDisplay(r)}
        </td>
        <td style="vertical-align: top; font-weight:700; font-size: 10px; color:#c53030;">
            ${arrears_html || (r.arrears ? `<span style="float:right;">${format_currency(r.arrears, "")}</span>` : '')}
        </td>
    </tr>`;
            });

            html += `
                        </tbody>
                    </table>
                </div>

                <div class="footer-content">
                    <div class="footer-grid">
                        <div class="policy-section">
                            <div style="color:#c53030; font-weight:bold; margin-bottom:4px;">Late Payment Policy</div>
                            ${late_fee_policy_text}
                        </div>
                        <div style="flex:1;">
                            <div class="amount-table">
                                <div class="amount-row"><span>Arrears</span> <span>${format_currency(arrear_val, "")}</span></div>
                                <div class="amount-row"><span>Current</span> <span>${format_currency(current_val, "")}</span></div>
                                <div class="amount-total">
                                    <div style="display:flex; justify-content:space-between;"><span>TOTAL</span> <span>${format_currency(total_val, "")}</span></div>
                                </div>
                                <div class="amount-row" style="font-size:9px; color:#555;"><span>After 10th Date</span> <span>${format_currency(total_val + late_fee_10, "")}</span></div>
                                <div class="amount-row" style="font-size:9px; color:#555;"><span>After 20th Date</span> <span>${format_currency(total_val + late_fee_10 + late_fee_20, "")}</span></div>
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

    html += `<script>window.onload=function(){window.print();}<\/script></body></html>`;

    let w = window.open("", "_blank");
    w.document.write(html);
    w.document.close();
}
