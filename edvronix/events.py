# import frappe
# from frappe.utils import flt

# GENDER_COST_CENTER_MAP = {
#     "Male": "AFSS - Boys School - ALFSS",
#     "Female": "AFSS - Girls School - ALFSS"
# }

# def override_invoice_rates(doc, method=None):
#     """
#     Intercepts the invoice before it is even saved to the database.
#     This prevents the 'stuck' loading and forces 0 rates.
#     """
#     if not doc.student:
#         return

#     # 1. Get student gender and map cost center
#     gender = frappe.db.get_value("Student", doc.student, "gender")
#     cost_center = GENDER_COST_CENTER_MAP.get(gender)

#     # 2. Get latest Program Enrollment fees (allowing 0)
#     enrollment = frappe.get_all(
#         "Program Enrollment",
#         filters={
#             "student": doc.student,
#             "docstatus": 1,
#             "fee_locked": 1
#         },
#         fields=["tuition_fee", "transport_fee", "exam_fee"],
#         order_by="creation desc",
#         limit=1
#     )

#     if not enrollment:
#         return

#     enr = enrollment[0]

#     # 3. Update the items BEFORE they are saved
#     for item in doc.items:
#         # Clean strings for comparison
#         name = (item.item_name or "").lower()
#         code = (item.item_code or "").lower()
        
#         target_rate = None

#         if "tuition" in name or "tuition" in code:
#             target_rate = enr.tuition_fee
#         elif "transport" in name or "transport" in code:
#             target_rate = enr.transport_fee
#         elif "exam" in name or "exam" in code:
#             target_rate = enr.exam_fee

#         if target_rate is not None:
#             # We use flt() to ensure 0 is passed as 0.0
#             val = flt(target_rate)
            
#             item.rate = val
#             item.amount = flt(item.qty) * val
            
#             # This is the secret: stop Frappe from looking up the price list
#             item.price_list_rate = val
#             item.base_price_list_rate = val
            
#             if cost_center:
#                 item.cost_center = cost_center

#     # 4. Tell Frappe NOT to run its own price calculations
#     doc.ignore_pricing_rule = 1
#     doc.calculate_taxes_and_totals()



import frappe
from frappe.utils import flt

GENDER_COST_CENTER_MAP = {
    "Male": "AFSS - Boys School - ALFSS",
    "Female": "AFSS - Girls School - ALFSS"
}

def override_invoice_rates(doc, method=None):
    """
    Overrides invoice item rates for tuition fee only,
    based on the latest Program Enrollment for the student.
    """
    if not doc.student:
        return

    # 1. Get student gender and map cost center
    gender = frappe.db.get_value("Student", doc.student, "gender")
    cost_center = GENDER_COST_CENTER_MAP.get(gender)

    # 2. Get latest Program Enrollment fees (only tuition)
    enrollment = frappe.get_all(
        "Program Enrollment",
        filters={
            "student": doc.student,
            "docstatus": 1
        },
        fields=["tuition_fee"],
        order_by="creation desc",
        limit=1
    )

    if not enrollment:
        return

    tuition_fee = enrollment[0].tuition_fee

    # 3. Update only tuition items BEFORE they are saved
    for item in doc.items:
        name = (item.item_name or "").lower()
        code = (item.item_code or "").lower()
        
        if "tuition" in name or "tuition" in code:
            val = flt(tuition_fee)
            
            item.rate = val
            item.amount = flt(item.qty) * val
            
            item.price_list_rate = val
            item.base_price_list_rate = val
            
            if cost_center:
                item.cost_center = cost_center

    # 4. Prevent Frappe from running price list logic and recalc totals
    doc.ignore_pricing_rule = 1
    doc.calculate_taxes_and_totals()