import frappe
from frappe.utils import nowdate, getdate, flt

@frappe.whitelist()
def get_customer_statement(customer, from_date=None, to_date=None):
    """Return a dict with customer statement details for use in client scripts or print formats."""
    if not from_date:
        from_date = "2000-01-01"
    if not to_date:
        to_date = nowdate()

    from_date = getdate(from_date)
    to_date = getdate(to_date)

    customer_doc = frappe.get_doc("Customer", customer)

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

    aging = calculate_aging(customer, to_date)

    return {
        "customer": {
            "name": customer_doc.name,
            "customer_name": customer_doc.customer_name,
            "address": get_customer_address(customer_doc.name),
        },
        "rows": rows,
        "opening_balance": opening_balance,
        "ending_balance": running_balance,
        "summary": aging,
        "statement_no": frappe.generate_hash(length=6),
        "statement_date": nowdate(),
    }


def execute(filters=None):
    """Standard entry point for Frappe Script Reports."""
    customer = filters.get("customer")
    from_date = filters.get("start_date")
    to_date = filters.get("end_date")

    data = get_customer_statement(customer, from_date, to_date)

    columns = [
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": "Description", "fieldname": "description", "fieldtype": "Data", "width": 250},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": "Balance", "fieldname": "balance", "fieldtype": "Currency", "width": 120},
    ]

    return columns, data["rows"]


# --- Helpers ---------------------------------------------------------------

def build_description(entry):
    vt = entry.voucher_type
    vn = entry.voucher_no
    if vt == "Sales Invoice":
        return f"Invoice #{vn}"
    elif vt == "Payment Entry":
        return f"Payment #{vn}"
    elif vt in ["Credit Note", "Sales Invoice"] and entry.credit > entry.debit:
        return f"Credit Memo #{vn}"
    else:
        return f"{vt} #{vn}"


def get_customer_address(customer):
    link = frappe.db.get_value(
        "Dynamic Link",
        {"link_doctype": "Customer", "link_name": customer, "parenttype": "Address"},
        "parent",
    )
    if not link:
        return {}
    addr = frappe.get_doc("Address", link)
    return {
        "address_line1": addr.address_line1,
        "address_line2": addr.address_line2,
        "city": addr.city,
        "state": addr.state,
        "pincode": addr.pincode,
        "country": addr.country,
    }


def calculate_aging(customer, as_of_date):
    today = getdate(as_of_date)
    buckets = {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "over_90": 0, "total_due": 0}

    invoices = frappe.db.get_list(
        "Sales Invoice",
        filters={"customer": customer, "outstanding_amount": [">", 0]},
        fields=["posting_date", "outstanding_amount"],
    )

    for inv in invoices:
        days = (today - inv.posting_date).days
        amt = flt(inv.outstanding_amount)
        if days <= 30:
            buckets["current"] += amt
        elif days <= 60:
            buckets["1_30"] += amt
        elif days <= 90:
            buckets["31_60"] += amt
        elif days <= 120:
            buckets["61_90"] += amt
        else:
            buckets["over_90"] += amt
        buckets["total_due"] += amt

    return buckets
