import frappe

def execute(filters=None):
    if not filters: 
        filters = {}
    
    # Pre-process filters to handle empty strings from the UI
    for key in ["academic_year", "month", "parent"]:
        if not filters.get(key):
            filters[key] = None

    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Parent ID", "fieldname": "parent_id", "fieldtype": "Link", "options": "Guardian", "width": 140},
        {"label": "Parent Name", "fieldname": "parent_name", "fieldtype": "Data", "width": 160},
        {"label": "Academic Year", "fieldname": "academic_year", "fieldtype": "Data", "width": 120},
        {"label": "Month", "fieldname": "month_name", "fieldtype": "Data", "width": 100},
        {"label": "Total Amount", "fieldname": "total_amount", "fieldtype": "Currency", "width": 110},
        {"label": "Total Paid", "fieldname": "total_paid", "fieldtype": "Currency", "width": 110},
        {"label": "Total Unpaid", "fieldname": "total_unpaid", "fieldtype": "Currency", "width": 110},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
    ]

def get_data(filters):
    # Build the query with proper conditions
    conditions = ["si.docstatus = 1"]
    values = {}
    
    # Add filters dynamically
    if filters.get("month"):
        conditions.append("MONTHNAME(si.posting_date) = %(month)s")
        values["month"] = filters["month"]
    
    if filters.get("parent"):
        conditions.append("sg.guardian = %(parent)s")
        values["parent"] = filters["parent"]
    
    if filters.get("academic_year"):
        conditions.append("pe.academic_year = %(academic_year)s")
        values["academic_year"] = filters["academic_year"]
        # Force inner join when academic year is specified
        enrollment_join = "INNER JOIN"
    else:
        enrollment_join = "LEFT JOIN"
        values["academic_year"] = None
    
    query = f"""
        SELECT
            sg.guardian AS parent_id,
            g.guardian_name AS parent_name,
            COALESCE(pe.academic_year, 'N/A') AS academic_year,
            MONTHNAME(si.posting_date) AS month_name,
            SUM(si.grand_total) AS total_amount,
            SUM(COALESCE(si.grand_total - si.outstanding_amount, 0)) AS total_paid,
            SUM(COALESCE(si.outstanding_amount, 0)) AS total_unpaid,
            CASE 
                WHEN SUM(COALESCE(si.outstanding_amount, 0)) <= 0 THEN 'Paid'
                WHEN SUM(COALESCE(si.outstanding_amount, 0)) >= SUM(si.grand_total) THEN 'Unpaid'
                ELSE 'Partially Paid'
            END AS status
        FROM `tabSales Invoice` si
        INNER JOIN `tabStudent Guardian` sg ON sg.parent = si.customer
        LEFT JOIN `tabGuardian` g ON g.name = sg.guardian
        {enrollment_join} `tabProgram Enrollment` pe ON pe.student = si.student 
            AND pe.academic_year = COALESCE(%(academic_year)s, pe.academic_year)
        WHERE {' AND '.join(conditions)}
        GROUP BY 
            sg.guardian, 
            pe.academic_year, 
            YEAR(si.posting_date),
            MONTH(si.posting_date)
        ORDER BY 
            si.posting_date DESC
    """
    
    return frappe.db.sql(query, values, as_dict=1)