$(document).ready(function() {
    // Toggle HTML/plain text mode for templates
    $('#template_html_toggle').change(function() {
        if ($(this).is(':checked')) {
            $('#template_body_type').val('html');
        } else {
            $('#template_body_type').val('plain');
        }
    });
    
    // Handle the view template action
    $('.view-template').click(function() {
        const templateName = $(this).data('template');
        
        // Load the template details
        $.ajax({
            url: '/get_template/' + templateName,
            type: 'GET',
            success: function(response) {
                if (response.success) {
                    const template = response.template;
                    
                    // Set modal title
                    $('#viewTemplateTitle').text('Template: ' + templateName);
                    
                    // Set subject
                    $('#viewTemplateSubject').text(template.subject || '(No subject)');
                    
                    // Set body based on type
                    if (template.body_type === 'html') {
                        // Show HTML content in iframe
                        $('#viewTemplateBodyText').addClass('d-none');
                        const iframe = $('#viewTemplateBodyHtml');
                        iframe.removeClass('d-none');
                        
                        // Set iframe content
                        const iframeDocument = iframe[0].contentDocument || iframe[0].contentWindow.document;
                        iframeDocument.open();
                        iframeDocument.write(template.body);
                        iframeDocument.close();
                    } else {
                        // Show plain text content
                        $('#viewTemplateBodyHtml').addClass('d-none');
                        $('#viewTemplateBodyText').removeClass('d-none').text(template.body);
                    }
                    
                    // Show the modal
                    $('#viewTemplateModal').modal('show');
                    
                    // Setup use template button
                    $('#useTemplateButton').off('click').on('click', function() {
                        window.location.href = '/?template=' + encodeURIComponent(templateName);
                    });
                } else {
                    alert('Error loading template: ' + response.message);
                }
            },
            error: function(xhr, status, error) {
                alert('Error loading template');
                console.error('Error loading template:', error);
            }
        });
    });
    
    // Handle the edit template action (simplified - would open the template data in the add form)
    $('.edit-template').click(function() {
        const templateName = $(this).data('template');
        alert('Edit functionality would be implemented here for template: ' + templateName);
        // TODO: Implement the edit functionality
    });
    
    // Handle the delete template action
    $('.delete-template').click(function() {
        const templateName = $(this).data('template');
        $('#deleteTemplateName').text(templateName);
        $('#deleteTemplateForm').attr('action', '/delete_template/' + templateName);
        $('#deleteTemplateModal').modal('show');
    });
});
