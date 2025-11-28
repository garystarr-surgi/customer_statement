app_version = "0.0.1"

app_name = "customer_statement"
app_title = "Customer Statement"
app_publisher = "SurgiShop"
app_description = "Accounting Customer Statement Report"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "gary.starr@surgishop.com"
app_license = "MIT"

# Client scripts - loaded on all pages
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