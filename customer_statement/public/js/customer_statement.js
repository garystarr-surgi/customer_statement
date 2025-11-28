// Client-side script for Customer Statement Report
frappe.ready(function() {
    // Wait for the report page to load
    setTimeout(function() {
        setup_customer_statement_report();
    }, 500);
});

function setup_customer_statement_report() {
    // Check if we're on the Customer Statement report page
    var report_name = frappe.get_route()[1];
    
    if (report_name === 'Customer Statement' || 
        window.location.pathname.includes('query-report/Customer Statement') ||
        $('.report-wrapper').length > 0) {
        
        // Add custom button after report filters are loaded
        add_custom_buttons();
        
        // Handle button clicks
        $(document).on('click', '.btn-generate-statement', function(e) {
            e.preventDefault();
            generate_statement_pdf();
        });
    }
}

function add_custom_buttons() {
    // Check if button already exists
    if ($('.btn-generate-statement').length > 0) {
        return;
    }
    
    // Try multiple locations to add the button
    var $target = null;
    
    // Try to find the standard report actions area
    if ($('.page-actions').length > 0) {
        $target = $('.page-actions');
    } else if ($('.form-actions').length > 0) {
        $target = $('.form-actions');
    } else if ($('.filter-section').length > 0) {
        $target = $('.filter-section');
    } else if ($('.report-filters').length > 0) {
        $target = $('.report-filters');
    }
    
    if ($target && $target.length > 0) {
        var $button = $('<button>', {
            class: 'btn btn-primary btn-generate-statement',
            type: 'button',
            style: 'margin-left: 10px;',
            html: '<i class="fa fa-file-pdf-o"></i> ' + __('Generate PDF Statement')
        });
        
        $target.append($button);
    } else {
        // Fallback: add button to the top of the page
        var $pageContent = $('.layout-main-section, .page-content');
        if ($pageContent.length > 0) {
            var $buttonContainer = $('<div>', {
                class: 'page-actions',
                style: 'margin-bottom: 15px; padding: 10px;'
            });
            
            var $button = $('<button>', {
                class: 'btn btn-primary btn-generate-statement',
                type: 'button',
                html: '<i class="fa fa-file-pdf-o"></i> ' + __('Generate PDF Statement')
            });
            
            $buttonContainer.append($button);
            $pageContent.prepend($buttonContainer);
        }
    }
}

function generate_statement_pdf() {
    // Get filter values from the report page
    var filters = get_report_filters();
    
    // Validate required fields
    if (!filters.customer) {
        frappe.msgprint({
            title: __('Validation Error'),
            message: __('Please select a Customer'),
            indicator: 'red'
        });
        return;
    }
    
    if (!filters.start_date || !filters.end_date) {
        frappe.msgprint({
            title: __('Validation Error'),
            message: __('Please select Start Date and End Date'),
            indicator: 'red'
        });
        return;
    }
    
    // Show loading indicator
    frappe.show_alert({
        message: __('Generating statement...'),
        indicator: 'blue'
    });
    
    // Call server method to generate statement
    frappe.call({
        method: 'customer_statement.report.customer_statement.get_customer_statement',
        args: {
            customer: filters.customer,
            from_date: filters.start_date,
            to_date: filters.end_date
        },
        callback: function(r) {
            frappe.hide_alert();
            if (r.message) {
                // If HTML content is returned, show it in a dialog or print it
                if (r.message.html_content) {
                    show_statement_dialog(r.message.html_content, r.message.data);
                } else if (r.message.data) {
                    show_statement_dialog('', r.message.data);
                } else {
                    frappe.msgprint({
                        title: __('Statement Generated'),
                        message: __('Statement data retrieved successfully'),
                        indicator: 'green'
                    });
                }
            }
        },
        error: function(r) {
            frappe.hide_alert();
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to generate statement: ') + (r.message || 'Unknown error'),
                indicator: 'red'
            });
        }
    });
}

function get_report_filters() {
    var filters = {};
    
    // Try to get filters from Frappe's report object
    if (window.frappe && frappe.report && frappe.report.get_filter_values) {
        try {
            filters = frappe.report.get_filter_values();
        } catch (e) {
            console.log('Could not get filters from frappe.report:', e);
        }
    }
    
    // Fallback: get from form fields directly
    if (!filters.customer) {
        var $customerField = $('[data-fieldname="customer"] input, input[data-fieldname="customer"], select[data-fieldname="customer"]');
        if ($customerField.length > 0) {
            filters.customer = $customerField.val();
        }
    }
    
    if (!filters.start_date) {
        var $startDateField = $('[data-fieldname="start_date"] input, input[data-fieldname="start_date"]');
        if ($startDateField.length > 0) {
            filters.start_date = $startDateField.val();
        }
    }
    
    if (!filters.end_date) {
        var $endDateField = $('[data-fieldname="end_date"] input, input[data-fieldname="end_date"]');
        if ($endDateField.length > 0) {
            filters.end_date = $endDateField.val();
        }
    }
    
    return filters;
}

function show_statement_dialog(html_content, data) {
    // Create and show a dialog with the statement
    var title = __('Customer Statement');
    if (data && data.customer && data.customer.customer_name) {
        title += ' - ' + data.customer.customer_name;
    }
    
    var dialog = new frappe.ui.Dialog({
        title: title,
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                options: html_content || '<div class="alert alert-info">' + __('Statement data loaded successfully') + '</div>'
            }
        ]
    });
    
    // Add print button
    dialog.set_primary_action(__('Print'), function() {
        print_statement(html_content);
    });
    
    dialog.show();
}

function print_statement(html_content) {
    // Open print dialog
    var print_window = window.open('', '_blank');
    if (print_window) {
        print_window.document.write('<!DOCTYPE html><html><head><title>Customer Statement</title></head><body>' + html_content + '</body></html>');
        print_window.document.close();
        print_window.focus();
        setTimeout(function() {
            print_window.print();
        }, 250);
    } else {
        frappe.msgprint(__('Please allow popups to print the statement'));
    }
}

