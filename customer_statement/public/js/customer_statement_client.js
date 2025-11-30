frappe.ui.form.on('Customer', {
    refresh: function(frm) {
        // Only show the button if the document is saved (not new)
        if (!frm.is_new()) {

            // Add the 'Statement' button under the 'View Report' group
            frm.add_custom_button(__('Statement'), function() {

                // Get the current customer's name
                const customer_name = frm.doc.name;

                // Open the custom report with filters pre-filled
                // NOTE: 'Customer Statement' must exactly match the report name in your JSON file
                frappe.set_route('query-report', 'Customer Statement', {
                    customer: customer_name,
                    // Default to one year back from today
                    start_date: frappe.datetime.add_years(frappe.datetime.get_today(), -1),
                    end_date: frappe.datetime.get_today()
                });

            }, __('View Report'), 'btn-primary'); // Styled as a primary button
        }
    }
});
