app_version = "0.0.1"
app_name = "customer_statement"
app_title = "Customer Statement"
app_publisher = "SurgiShop"
app_description = "Accounting Customer Statement Report"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "gary.starr@surgishop.com"
app_license = "MIT"

# --- Client Script Registration ---
# This forces the browser to look in the standard built asset path
app_include_js = [
    "/assets/customer_statement/js/customer_statement_client.js"
]

# --- Fixtures ---
# Export workspace so the report link appears in Accounting workspace
fixtures = [
    {
        "doctype": "Workspace",
        "filters": {
            "name": "Accounting"
        }
    }
]
