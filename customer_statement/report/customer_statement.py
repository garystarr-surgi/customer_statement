import frappe
from frappe.utils import nowdate, getdate, flt, escape
from frappe import _

# --- Core Logic Function ---

@frappe.whitelist()
def get_customer_statement(customer, from_date=None, to_date=None):
    """Calculates all statement details (transactions, balances, aging) for a customer."""
    
    # 1. Date Handling
    # Safely convert dates
    from_date = getdate(from_date or "2000-01-01")
    to_date = getdate(to_date or nowdate())

    try:
        customer_doc = frappe.get_doc("Customer", customer)
    except frappe.DoesNotExistError:
        frappe.throw(f"Customer {customer} not found.")
        return {}

    # 2. Opening Balance Calculation (All transactions before the start date)
    opening_balance_tuple = frappe.db.sql("""
        SELECT SUM(debit) - SUM(credit)
        FROM `tabGL Entry`
        WHERE party_type = 'Customer'
          AND party = %s
          AND posting_date < %s
    """, (customer, from_date))
    
    opening_balance = flt(opening_balance_tuple[0][0])
    
    running_balance = opening_balance
    
    # Add the Balance Forward row
    rows = [{
        "date": from_date,
        "description": _("Balance Forward"),
        "amount": 0,  
        "balance": running_balance,
        "voucher_type": "",
        "voucher_no": ""
    }]

    # 3. GL Entries (Transactions within the date range)
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
        # Calculate the change in balance for this entry
        amount = flt(entry.debit) - flt(entry.credit)
        running_balance += amount
        
        # Use helper function (defined below)
        desc = build_description(entry) 
        
        rows.append({
            "date": entry.posting_date,
            "description": desc,
            "amount": amount, 
            "balance": running_balance,
            "voucher_type": entry.voucher_type,
            "voucher_no": entry.voucher_no
        })
    
    # Use helper functions (defined below)
    aging = calculate_aging(customer, to_date)
    
    # 4. Final Data Structure (Passed to the Print Format)
    return {
        "customer": {
            "name": customer_doc.name,
            "customer_name": customer_doc.customer_name,
            "address": get_customer_address(customer_doc.name),
        },
        "rows": rows, # List of transaction rows
        "filters": {"from_date": from_date, "to_date": to_date},
        "opening_balance": opening_balance,
        "ending_balance": running_balance,
        "summary": aging,
        "statement_no": frappe.generate_hash(length=6),
        "statement_date": nowdate(),
    }


# --- Standard Report Entry Point (Execute) ---

def execute(filters=None):
    """Standard entry point for Frappe Script Reports. Returns (columns, data)."""
    
    # CRITICAL FIX: Use 'start_date' and 'end_date' as defined in the JSON file
    customer = filters.get("customer")
    from_date = filters.get("start_date") 
    to_date = filters.get("end_date")
    
    if not customer:
        # Ensures the report cannot run without the required filter
        frappe.throw(_("Please select a Customer."))

    # 1. Call the core logic function
    # full_data now contains the complete dictionary (customer, rows, summary, etc.)
    full_data = get_customer_statement(customer, from_date, to_date)

    # 2. Define Columns for the report grid (what the user sees on screen)
    # This must match your JSON file's "columns" array.
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": _("Description"), "fieldname": "description", "fieldtype": "Data", "width": 250},
        {"label": _("Amount (Change)"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Balance"), "fieldname": "balance", "fieldtype": "Currency", "width": 120},
    ]

    # 3. Return columns and the list of transaction rows
    # The Print Format will receive the full_data structure as `data[0]`
    return columns, full_data["rows"]


# --- Helper Functions --------------------------------------------------------------------

def build_description(entry):
    """Generates a user-friendly description for the GL Entry."""
    vt = entry.voucher_type
    vn = entry.voucher_no
    
    # Default description
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


def calculate_aging(customer, as_of_date):
    """Calculates the current aging buckets for outstanding invoices."""
    today = getdate(as_of_date)
    # Keys must match the fieldnames defined in your JSON summary_columns
    buckets = {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "over_90": 0, "total_due": 0} 

    invoices = frappe.db.get_list(
        "Sales Invoice",
        filters={"customer": customer, "outstanding_amount": [">", 0]},
        fields=["posting_date", "outstanding_amount"],
    )

    for inv in invoices:
        days = (today - inv.posting_date).days
        amt = flt(inv.outstanding_amount)
        
        # Calculate aging based on days past due (assuming 0-day terms for simplicity)
        if days <= 0:
            buckets["current"] += amt
        elif days <= 30:
            buckets["1_30"] += amt
        elif days <= 60:
            buckets["31_60"] += amt
        elif days <= 90:
            buckets["61_90"] += amt
        else:
            buckets["over_90"] += amt
        
        buckets["total_due"] += amt

    return buckets
