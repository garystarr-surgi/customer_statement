import frappe
from frappe.utils import nowdate, getdate, flt, escape

# --- Core Logic Function ---

@frappe.whitelist()
def get_customer_statement(customer, from_date=None, to_date=None):
    """Return a dict with customer statement details for use in client scripts or print formats."""
    
    # 1. Date Handling (Safety checks)
    if not from_date:
        from_date = "2000-01-01"
    if not to_date:
        to_date = nowdate()

    from_date = getdate(from_date)
    to_date = getdate(to_date)

    # Use try-except to safely handle cases where the Customer might not exist
    try:
        customer_doc = frappe.get_doc("Customer", customer)
    except frappe.DoesNotExistError:
        frappe.throw(f"Customer {customer} not found.")
        return {}

    # 2. Opening Balance Calculation
    opening_balance_tuple = frappe.db.sql("""
        SELECT SUM(debit) - SUM(credit)
        FROM `tabGL Entry`
        WHERE party_type = 'Customer'
          AND party = %s
          AND posting_date < %s
    """, (customer, from_date))
    
    opening_balance = flt(opening_balance_tuple[0][0])
    
    running_balance = opening_balance
    rows = [{
        "date": from_date,
        "description": "Balance Forward",
        "amount": 0,  # Amount is 0 for Balance Forward row, balance field holds the value
        "balance": running_balance
    }]

    # 3. GL Entries
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
        
        # Use a helper function (defined below)
        desc = build_description(entry) 
        
        rows.append({
            "date": entry.posting_date,
            "description": desc,
            # Amount field represents the change (debit - credit)
            "amount": amount, 
            "balance": running_balance,
            "voucher_type": entry.voucher_type, # Added for Print Format use
            "voucher_no": entry.voucher_no       # Added for Print Format use
        })
    
    # Use helper functions (defined below)
    aging = calculate_aging(customer, to_date)
    
    # 4. Final Data Structure (Passed to the Print Format)
    # The dictionary returned here is what your Jinja Print Format will access via `data[0]`
    final_data = {
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
    
    return final_data


# --- Standard Report Entry Point ---

def execute(filters=None):
    """Standard entry point for Frappe Script Reports. Returns (columns, data)."""
    
    # Safely retrieve filters
    customer = filters.get("customer")
    # Assuming your report's JSON filter fields are named 'customer', 'from_date', 'to_date'
    from_date = filters.get("from_date") 
    to_date = filters.get("to_date")
    
    if not customer:
        frappe.throw(_("Please select a Customer."))

    # 1. Call the core logic function
    # The result is the final_data dictionary
    full_data = get_customer_statement(customer, from_date, to_date)

    # 2. Define Columns for the report grid (what the user sees on screen)
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": _("Description"), "fieldname": "description", "fieldtype": "Data", "width": 250},
        {"label": _("Amount (Change)"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Balance"), "fieldname": "balance", "fieldtype": "Currency", "width": 120},
    ]

    # 3. FIX: Return columns and the list of transaction rows
    # The Print Format will receive the full_data structure as `data[0]`
    return columns, full_data["rows"]


# --- Helper Functions (Ensure these are defined in your file) ---

def build_description(entry):
    """Generates a user-friendly description for the GL Entry."""
    vt = entry.voucher_type
    vn = entry.voucher_no
    
    # Add logic to make the description specific based on voucher type
    if vt == "Sales Invoice":
        return f"Invoice #{vn}"
    elif vt == "Payment Entry":
        return f"Payment #{vn}"
    elif vt in ["Credit Note", "Journal Entry"] and entry.credit > entry.debit:
        return f"Credit Memo #{vn}"
    else:
        # Default to remarks if available, or just the voucher info
        return entry.remarks or f"{vt} #{vn}"


def get_customer_address(customer):
    """Fetches the primary Address details for the customer."""
    link = frappe.db.get_value(
        "Dynamic Link",
        {"link_doctype": "Customer", "link_name": customer, "parenttype": "Address"},
        "parent",
    )
    if not link:
        return {}
    
    # Only fetch and return relevant address fields for printing
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
    buckets = {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "over_90": 0, "total_due": 0}

    invoices = frappe.db.get_list(
        "Sales Invoice",
        filters={"customer": customer, "outstanding_amount": [">", 0]},
        fields=["posting_date", "outstanding_amount"],
    )

    for inv in invoices:
        days = (today - inv.posting_date).days
        amt = flt(inv.outstanding_amount)
        
        # Calculate aging based on days past due (assuming terms are 0 days)
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
