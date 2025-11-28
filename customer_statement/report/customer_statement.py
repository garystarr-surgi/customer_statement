import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": _("Description"), "fieldname": "description", "fieldtype": "Data", "width": 250},
        {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Balance"), "fieldname": "balance", "fieldtype": "Currency", "width": 120},
    ]

    data = []

    # Balance Forward
    balance_forward = frappe.db.sql("""
        SELECT COALESCE(SUM(debit) - SUM(credit), 0)
        FROM `tabGL Entry`
        WHERE party=%s AND posting_date < %s AND is_cancelled=0
    """, (filters.get("customer"), filters.get("start_date")))[0][0]

    data.append({
        "date": filters.get("start_date"),
        "description": "Balance Forward",
        "amount": 0,
        "balance": balance_forward
    })

    # Transactions
    transactions = frappe.db.sql("""
        SELECT posting_date, voucher_type, voucher_no, debit, credit
        FROM `tabGL Entry`
        WHERE party=%s AND posting_date BETWEEN %s AND %s AND is_cancelled=0
        ORDER BY posting_date ASC, creation ASC
    """, (filters.get("customer"), filters.get("start_date"), filters.get("end_date")), as_dict=True)

    running_balance = balance_forward
    for t in transactions:
        amount = t["debit"] - t["credit"]
        running_balance += amount
        data.append({
            "date": t["posting_date"],
            "description": f"{t['voucher_type']} {t['voucher_no']}",
            "amount": amount,
            "balance": running_balance
        })

    return columns, data
