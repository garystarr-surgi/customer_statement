app_version = "0.0.1"

app_name = "customer_statement"
app_title = "Customer Statement"
app_publisher = "SurgiShop"
app_description = "Accounting Customer Statement Report"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "gary.starr@surgishop.com"
app_license = "MIT"

# Fixtures - Workspaces (for report link in workspace)
# Note: Client Script is managed via Client Script doctype in Frappe Cloud, not via app_include_js
fixtures = [
    {
        "doctype": "Workspace",
        "filters": {
            "name": "Accounting"
        }
    }
]