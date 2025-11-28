import frappe
from frappe.utils import nowdate, getdate, flt

def execute(filters=None):
    customer = filters.get("customer")
    from_date = filters.get("start_date") or "2000-01-01"
    to_date = filters.get("end_date") or nowdate()

    from_date = getdate(from_date)
    to_date = getdate(to_date)

    # Opening balance
    opening_balance = frappe.db.sql("""
        SELECT SUM(debit) - SUM(credit)
        FROM `tabGL Entry`
        WHERE party_type = 'Customer'
          AND party = %s
          AND posting_date < %s
    """, (customer, from_date))[0][0] or 0

    running_balance = opening_balance
    rows = [{
        "date": from_date,
        "description": "Balance Forward",
        "amount": opening_balance,
        "balance": running_balance
    }]

    # GL Entries
    gl_entries = frappe.db.get_list(
        "GL Entry",
        filters={
            "party_type": "Customer",
            "party": customer,
            "posting_date": ["between", [from_date, to_date]],
        },
        fields=["posting_date", "voucher_type", "voucher_no", "debit", "credit", "remarks"],
        order_by="posting_date asc, creation asc",
    )

    for entry in gl_entries:
        amount = flt(entry.debit) - flt(entry.credit)
        running_balance += amount
        desc = build_description(entry)
        rows.append({
            "date": entry.posting_date,
            "description": desc,
            "amount": amount,
            "balance": running_balance
        })

    # Return columns + data for the report UI
    columns = [
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": "Description", "fieldname": "description", "fieldtype": "Data", "width": 250},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": "Balance", "fieldname": "balance", "fieldtype": "Currency", "width": 120},
    ]

    return columns, rows
