app_version = "0.0.1"

app_name = "customer_statement"
app_title = "Customer Statement"
app_publisher = "SurgiShop"
app_description = "Accounting Customer Statement Report"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "gary.starr@surgishop.com"
app_license = "MIT"

# --- Report Registration (REQUIRED FIX) ---
# This hook tells Frappe to look in the 'report' folder for a report named 'customer_statement'
app_reports = [
    "customer_statement" 
]
# ------------------------------------------

# Client scripts - loaded on all pages
# This will load the JavaScript file directly
app_include_js = [
    "customer_statement/public/js/customer_statement_client.js"
]

# Fixtures - Workspaces (for report link in workspace)
fixtures = [
    {
        "doctype": "Workspace",
        "filters": {
            "name": "Accounting"
        }
    }
]
