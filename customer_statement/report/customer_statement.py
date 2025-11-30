import frappe
from frappe.utils import nowdate, getdate, flt
from frappe import _

# --- Core Logic Function ---

@frappe.whitelist()
def get_customer_statement(customer, from_date=None, to_date=None):
    """Calculates all statement details (transactions, balances) for a customer."""

    # 1. Date Handling
    from_date = getdate(from_date or "2000-01-01")
    to_date = getdate(to_date or nowdate())

    try:
        customer_doc = frappe.get_doc("Customer", customer)
    except frappe.DoesNotExistError:
        frappe.throw(f"Customer {customer} not found.")
        return {}

    # 2. Opening Balance Calculation (transactions before start date)
    opening_balance_tuple = frappe.db.sql("""
        SELECT SUM(debit) - SUM(credit)
        FROM `tabGL Entry`
        WHERE party_type = 'Customer'
          AND party = %s
          AND posting_date < %s
    """, (customer, from_date))

    opening_balance = flt(opening_balance_tuple[0][0]) if opening_balance_tuple else 0
    running_balance = opening_balance

    # Add Balance Forward row
    rows = [{
        "date": from_date,
        "description": _("Balance Forward"),
        "amount": 0,
        "balance": running_balance,
        "voucher_type": "",
        "voucher_no": ""
    }]

    # 3. GL Entries (transactions within date range)
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
            "balance": running_balance,
            "voucher_type": entry.voucher_type,
            "voucher_no": entry.voucher_no
        })

    # 4. Final Data Structure (passed to Print Format)
    return {
        "customer": {
            "name": customer_doc.name,
            "customer_name": customer_doc.customer_name,
            "address": get_customer_address(customer_doc.name),
        },
        "rows": rows,
        "filters": {"from_date": from_date, "to_date": to_date},
        "opening_balance": opening_balance,
        "ending_balance": running_balance,
        "statement_no": frappe.generate_hash(length=6),
        "statement_date": nowdate(),
    }


# --- Standard Report Entry Point (Execute) ---

def execute(filters=None):
    """Entry point for Script Report. Returns (columns, data)."""

    customer = filters.get("customer")
    from_date = filters.get("start_date")
    to_date = filters.get("end_date")

    if not customer:
        frappe.throw(_("Please select a Customer."))

    # Guard: ensure customer is a string, not dict
    if isinstance(customer, dict):
        customer = customer.get("name")

    full_data = get_customer_statement(customer, from_date, to_date)

    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": _("Description"), "fieldname": "description", "fieldtype": "Data", "width": 250},
        {"label": _("Amount (Change)"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Balance"), "fieldname": "balance", "fieldtype": "Currency", "width": 120},
    ]

    return columns, full_data["rows"]


# --- Helper Functions --------------------------------------------------------

def build_description(entry):
    """Generates a user-friendly description for the GL Entry."""
    vt = entry.voucher_type
    vn = entry.voucher_no

    desc = f"{vt} #{vn}"
    if vt == "Sales Invoice":
        desc = f"Invoice #{vn}"
    elif vt == "Payment Entry":
        desc = f"Payment #{vn}"
    elif vt == "Journal Entry" and entry.remarks:
        desc = entry.remarks

    return desc


def get_customer_address(customer):
    """Fetches the primary Address details for the customer."""
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
