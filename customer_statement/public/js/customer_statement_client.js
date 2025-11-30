frappe.ui.form.on('Customer', {
    refresh: function(frm) {
        // Only show the button if the document is saved and not new
        if (frm.doc.docstatus === 0 && !frm.is_new()) {
            
            // Add the 'Statement' button next to the primary action buttons
            frm.add_custom_button(__('Statement'), function() {
                
                // Get the current customer's name
                const customer_name = frm.doc.name;
                
                // Open the custom report with filters pre-filled
                // NOTE: 'Customer Statement' must exactly match the name of your report in the JSON file
                frappe.set_route('query-report', 'Customer Statement', {
                    // Pass the customer name to the report's 'customer' filter
                    customer: customer_name,
                    // Pass current date and a default start date (e.g., 1 year ago)
                    start_date: frappe.datetime.add_months(frappe.datetime.get_today(), -12),
                    end_date: frappe.datetime.get_today()
                });
                
            }, __('View Report'), 'btn-default'); // Added to the 'View Report' group
        }
    }
});
