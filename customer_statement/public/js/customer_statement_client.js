// Client Script for Customer Statement Button on Customer Form
frappe.ui.form.on("Customer", {
    refresh(frm) {
        // Add a custom button to the Customer form toolbar
        if (frm.doc.name) {
            frm.add_custom_button(__("Print Statement"), () => {
                generate_customer_statement(frm);
            }, __("Actions"));
        }
    }
});

function generate_customer_statement(frm) {
    // Check if the current document is saved (i.e., has a name)
    if (!frm.doc.name) {
        frappe.msgprint(__("Please save the Customer before printing the statement."));
        return;
    }

    // Show dialog to select date range
    var dialog = new frappe.ui.Dialog({
        title: __("Customer Statement"),
        fields: [
            {
                label: __("From Date"),
                fieldname: "from_date",
                fieldtype: "Date",
                default: frappe.datetime.add_months(frappe.datetime.get_today(), -12),
                reqd: 1
            },
            {
                label: __("To Date"),
                fieldname: "to_date",
                fieldtype: "Date",
                default: frappe.datetime.get_today(),
                reqd: 1
            }
        ],
        primary_action_label: __("Generate Statement"),
        primary_action: function() {
            var values = dialog.get_values();
            if (!values.from_date || !values.to_date) {
                frappe.msgprint({
                    title: __("Validation Error"),
                    message: __("Please select both From Date and To Date"),
                    indicator: "red"
                });
                return;
            }

            dialog.hide();

            frappe.call({
                // Correct method path: customer_statement.report.customer_statement.get_customer_statement
                method: "customer_statement.report.customer_statement.get_customer_statement",
                args: {
                    customer: frm.doc.name,
                    from_date: values.from_date,
                    to_date: values.to_date
                },
                callback(r) {
                    if (r.message) {
                        if (r.message.html_content) {
                            // Show statement in a dialog with print option
                            show_statement_dialog(r.message.html_content, r.message.data);
                        } else if (r.message.data) {
                            // If we have data but no HTML, show a message
                            frappe.msgprint({
                                title: __("Statement Generated"),
                                message: __("Statement data retrieved successfully"),
                                indicator: "green"
                            });
                            // Optionally open the report page
                            frappe.set_route("query-report", "Customer Statement", {
                                customer: frm.doc.name,
                                start_date: values.from_date,
                                end_date: values.to_date
                            });
                        } else {
                            frappe.msgprint(__("Failed to generate statement. Check server logs."));
                        }
                    }
                },
                error(r) {
                    frappe.msgprint({
                        title: __("Error"),
                        message: __("Failed to generate statement: ") + (r.message || "Unknown error"),
                        indicator: "red"
                    });
                },
                freeze: true,
                freeze_message: __("Generating Customer Statement...")
            });
        }
    });

    dialog.show();
}

function show_statement_dialog(html_content, data) {
    var title = __("Customer Statement");
    if (data && data.customer && data.customer.customer_name) {
        title += " - " + data.customer.customer_name;
    }

    var dialog = new frappe.ui.Dialog({
        title: title,
        size: "large",
        fields: [
            {
                fieldtype: "HTML",
                options: html_content || '<div class="alert alert-info">' + __("Statement data loaded successfully") + "</div>"
            }
        ]
    });

    // Add print button
    dialog.set_primary_action(__("Print"), function() {
        print_statement(html_content);
    });

    // Add option to open report page
    dialog.add_custom_action(__("Open Report"), function() {
        if (data && data.customer) {
            frappe.set_route("query-report", "Customer Statement", {
                customer: data.customer.name
            });
        }
        dialog.hide();
    });

    dialog.show();
}

function print_statement(html_content) {
    var print_window = window.open("", "_blank");
    if (print_window) {
        print_window.document.write("<!DOCTYPE html><html><head><title>Customer Statement</title></head><body>" + html_content + "</body></html>");
        print_window.document.close();
        print_window.focus();
        setTimeout(function() {
            print_window.print();
        }, 250);
    } else {
        frappe.msgprint(__("Please allow popups to print the statement"));
    }
}

