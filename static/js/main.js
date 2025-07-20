$(document).ready(function() {
    // Delete sender from dropdown with improved error handling
    $(document).on('click', '.delete-sender-item', function(e) {
        e.preventDefault();
        e.stopPropagation(); // Prevent dropdown from closing
        
        // Use closest to ensure we get the button regardless of if the icon or button was clicked
        const button = $(this);
        const email = button.data('email');
        
        if (confirm('Are you sure you want to delete this sender: ' + email + '?')) {
            console.log('Deleting sender:', email);
            
            $.ajax({
                url: '/delete_sender',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ email: email }),
                success: function(response) {
                    if (response.success) {
                        // Remove item from dropdown
                        button.closest('li').remove();
                        console.log('Sender deleted successfully:', email);
                        
                        // Show a toast or alert
                        alert('Sender deleted successfully');
                    } else {
                        console.error('Failed to delete sender:', response.message);
                        alert('Error: ' + (response.message || 'Failed to delete sender'));
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Error deleting sender:", email, "Status:", status, "Error:", error);
                    console.error("Response text:", xhr.responseText);
                    alert('Error deleting sender email. Check console for details.');
                }
            });
        }
    });
    
    // Delete recipient from dropdown with improved error handling
    $(document).on('click', '.delete-recipient-item', function(e) {
        e.preventDefault();
        e.stopPropagation(); // Prevent dropdown from closing
        
        // Use 'this' to reference the clicked element directly
        const button = $(this);
        const email = button.data('email');
        
        if (confirm('Are you sure you want to delete this recipient: ' + email + '?')) {
            console.log('Deleting recipient:', email);
            
            $.ajax({
                url: '/delete_recipient',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ email: email }),
                success: function(response) {
                    if (response.success) {
                        // Remove item from dropdown
                        button.closest('li').remove();
                        console.log('Recipient deleted successfully:', email);
                        
                        // Show a toast or alert
                        alert('Recipient deleted successfully');
                    } else {
                        console.error('Failed to delete recipient:', response.message);
                        alert('Error: ' + (response.message || 'Failed to delete recipient'));
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Error deleting recipient:", email, "Status:", status, "Error:", error);
                    console.error("Response text:", xhr.responseText);
                    alert('Error deleting recipient email. Check console for details.');
                }
            });
        }
    });
    
    // Handle special test emails
    $(document).on('click', '.special-test', function(e) {
        e.preventDefault();
        const testType = $(this).data('test');
        console.log('Special test clicked:', testType);
        
        // Check if a profile is selected first before making the AJAX call
        if (!$('#profile').val()) {
            // Create a more informative popup alert with proper contrast
            const alertHTML = `
                <div class="position-fixed top-0 start-50 translate-middle-x p-3" style="z-index: 1050">
                    <div class="toast show bg-dark border border-secondary" role="alert" aria-live="assertive" aria-atomic="true">
                        <div class="toast-header bg-secondary text-white">
                            <i class="fas fa-info-circle me-2"></i>
                            <strong class="me-auto">Profile Required</strong>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
                        </div>
                        <div class="toast-body text-white">
                            <p>Please select an SMTP profile before using test emails.</p>
                            <p class="mb-0 text-light"><small>The test email requires server settings to function properly.</small></p>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove any existing toasts first
            $('.toast-container').remove();
            
            // Append the toast to the body
            $('body').append(alertHTML);
            
            // Set a timeout to remove the toast after 5 seconds
            setTimeout(function() {
                $('.toast').toast('hide');
                setTimeout(function() {
                    $('.toast-container').remove();
                }, 500);
            }, 5000);
            
            return;
        }
        
        // Special test handler endpoint
        $.ajax({
            url: '/get_test_data',
            type: 'GET',
            data: {
                test_type: testType
            },
            success: function(response) {
                if (response.success) {
                    const testData = response.test_data;
                    
                    // Fill the form with test data
                    if (testData.sender) $('#sender').val(testData.sender);
                    if (testData.recipients) $('#recipients').val(testData.recipients.join(', '));
                    if (testData.subject) $('#subject').val(testData.subject);
                    if (testData.body) $('#body').val(testData.body);
                    
                    // Set body type
                    if (testData.body_type === 'html') {
                        $('#htmlToggle').prop('checked', true);
                        $('#body_type').val('html');
                    } else {
                        $('#htmlToggle').prop('checked', false);
                        $('#body_type').val('plain');
                    }
                    
                    // Set custom fields if any
                    if (testData.cc) $('#cc').val(testData.cc.join(', '));
                    if (testData.bcc) $('#bcc').val(testData.bcc.join(', '));
                    
                    // Provide feedback
                    alert('Test data loaded. Review and click "Send Email" to proceed.');
                    
                    // If we need to handle special attachments, store that info
                    if (testData.special_attachment) {
                        $('#emailForm').data('special-attachment', testData.special_attachment);
                        
                        // Show indicator that a special attachment will be included
                        let attachmentType = testData.special_attachment.type;
                        let attachmentName = '';
                        
                        switch(attachmentType) {
                            case 'pdf':
                                attachmentName = testData.special_attachment.malformed 
                                    ? 'Malformed PDF' 
                                    : (testData.special_attachment.active_content ? 'PDF with Active Content' : 'PDF');
                                break;
                            case 'docx':
                                attachmentName = 'DOCX Document';
                                break;
                            case 'xlsx':
                                attachmentName = 'Excel Spreadsheet';
                                break;
                            case 'eicar':
                                attachmentName = 'EICAR Test File';
                                break;
                            default:
                                attachmentName = attachmentType.toUpperCase();
                                break;
                        }
                        
                        // Update attachment indicator
                        $('#specialAttachmentBadge')
                            .text(attachmentName)
                            .removeClass('d-none')
                            .addClass('d-inline-flex');
                            
                        // For EICAR and active content, add warning class
                        if (attachmentType === 'eicar' || 
                            (attachmentType === 'pdf' && testData.special_attachment.active_content) ||
                            testData.special_attachment.malformed) {
                            $('#specialAttachmentBadge').removeClass('bg-info').addClass('bg-warning');
                        } else {
                            $('#specialAttachmentBadge').removeClass('bg-warning').addClass('bg-info');
                        }
                    } else {
                        $('#emailForm').removeData('special-attachment');
                        $('#specialAttachmentBadge').addClass('d-none').removeClass('d-inline-flex');
                    }
                } else {
                    alert('Error loading test data: ' + response.message);
                }
            },
            error: function(xhr, status, error) {
                alert('Error loading test data');
                console.error('Error loading test data:', error);
            }
        });
    });
    
    // Track form submission to prevent duplicates
    let isSubmitting = false;
    
    // Handle form submission via AJAX - with enhanced duplicate protection
    $('#emailForm').submit(function(e) {
        e.preventDefault();
        
        // Disable the submit button immediately to prevent multiple clicks
        $('#sendButton').prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>Sending...');
        
        // Abort immediately if already submitting 
        if (isSubmitting) {
            console.log('Preventing duplicate submission');
            return false;
        }
        
        // Set submission flag 
        isSubmitting = true;
        
        // Generate a unique ID for this specific submission
        const uniqueId = Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        
        // Create form data object
        const formData = new FormData(this);
        
        // Add client ID for server-side duplicate prevention
        formData.append('client_id', uniqueId);
        
        // Set the body type based on HTML toggle and ensure the correct Content-Type
        const isHtml = $('#htmlToggle').is(':checked');
        if (isHtml) {
            console.log('Sending as HTML');
            formData.set('body_type', 'html');
            
            // Make sure HTML content is properly formatted
            const bodyContent = $('#body').val();
            // ALWAYS format the content with proper HTML tags to ensure it renders as HTML
            const formattedHtml = bodyContent.includes('<html>') ? bodyContent : 
                `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
</head>
<body>
  ${bodyContent.replace(/\n/g, '<br>')}
</body>
</html>`;
            formData.set('body', formattedHtml);
            console.log('Formatted HTML content');
        } else {
            console.log('Sending as plain text');
            formData.set('body_type', 'plain');
        }
        
        // Add special attachment data if present
        const specialAttachment = $(this).data('special-attachment');
        if (specialAttachment) {
            formData.set('special_attachment', JSON.stringify(specialAttachment));
        }
        
        // Sending indicator already set above, don't need to do it again
        
        // Send the email via AJAX
        $.ajax({
            url: '/send_email',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                // Reset the button and submission flag
                $('#sendButton').html('<i class="fas fa-paper-plane me-2"></i>Send Email').prop('disabled', false);
                isSubmitting = false;
                
                // Show status modal
                if (response.success) {
                    $('#statusModalHeader').removeClass('bg-danger').addClass('bg-success');
                    $('#statusModalTitle').text('Success');
                    $('#statusMessage').text(response.message);
                } else {
                    $('#statusModalHeader').removeClass('bg-success').addClass('bg-danger');
                    $('#statusModalTitle').text('Failed');
                    $('#statusMessage').text(response.message);
                }
                $('#statusModal').modal('show');
            },
            error: function(xhr, status, error) {
                // Reset the button and submission flag
                $('#sendButton').html('<i class="fas fa-paper-plane me-2"></i>Send Email').prop('disabled', false);
                isSubmitting = false;
                
                // Show error message
                $('#statusModalHeader').removeClass('bg-success').addClass('bg-danger');
                $('#statusModalTitle').text('Failed');
                $('#statusMessage').text('Email failed. Please try again.');
                $('#statusModal').modal('show');
                
                console.error('Error sending email:', error);
            }
        });
    });
    
    // Toggle HTML/plain text mode with visible feedback
    $('#htmlToggle').change(function() {
        if ($(this).is(':checked')) {
            console.log('HTML mode enabled');
            // Simply set the hidden field - this is what the server reads
            $('input[name="body_type"]').val('html');
            // Add a class to the textarea to visually indicate HTML mode
            $('#body').addClass('html-mode');
        } else {
            console.log('Plain text mode enabled');
            // Simply set the hidden field - this is what the server reads
            $('input[name="body_type"]').val('plain');
            // Remove the class when switching back to plain text
            $('#body').removeClass('html-mode');
        }
    });
    
    // Handle form reset - clear special attachment data
    $('button[type="reset"]').click(function() {
        // Clear the special attachment data
        $('#emailForm').removeData('special-attachment');
        $('#specialAttachmentBadge').addClass('d-none').removeClass('d-inline-flex');
    });
    
    // Load template when selected
    $('#template').on('change', function() {
        const templateName = $(this).val();
        if (!templateName) return;
        
        console.log('Template selected:', templateName);
        
        // Show loading indicator
        $('#body').prop('disabled', true);
        $('#subject').prop('disabled', true);
        
        // Load the template
        $.ajax({
            url: '/get_template/' + encodeURIComponent(templateName),
            type: 'GET',
            success: function(response) {
                console.log('Template response:', response);
                if (response.success) {
                    const template = response.template;
                    
                    // Fill in subject and body
                    $('#subject').val(template.subject);
                    $('#body').val(template.body);
                    
                    // Set HTML toggle based on template type
                    if (template.body_type === 'html') {
                        $('#htmlToggle').prop('checked', true);
                        $('#body_type').val('html');
                    } else {
                        $('#htmlToggle').prop('checked', false);
                        $('#body_type').val('plain');
                    }
                } else {
                    console.error('Template error:', response.message);
                    alert('Error loading template: ' + response.message);
                }
                
                // Reset inputs
                $('#body').prop('disabled', false);
                $('#subject').prop('disabled', false);
            },
            error: function(xhr, status, error) {
                console.error('Template error details:', {xhr, status, error});
                alert('Error loading template: ' + error);
                
                // Reset inputs
                $('#body').prop('disabled', false);
                $('#subject').prop('disabled', false);
            }
        });
    });
    
    // Test SMTP connection
    $('#testConnection').click(function() {
        const profile = $('#profile').val();
        if (!profile) {
            alert('Please select an SMTP profile first');
            return;
        }
        
        // Show connection test modal
        $('#connectionModal').modal('show');
        $('#connectionStatus').text('Testing connection...');
        $('#connectionDetails').addClass('d-none');
        $('#serverCapabilities').empty();
        
        // Send test request
        $.ajax({
            url: '/test_connection',
            type: 'POST',
            data: {
                profile: profile
            },
            success: function(response) {
                if (response.success) {
                    $('#connectionStatus').html('<div class="alert alert-success"><i class="fas fa-check-circle me-2"></i>' + response.message + '</div>');
                    
                    // Show capabilities if available
                    if (response.capabilities && response.capabilities.length > 0) {
                        $('#serverCapabilities').empty();
                        response.capabilities.forEach(function(capability) {
                            $('#serverCapabilities').append('<li>' + capability + '</li>');
                        });
                        $('#connectionDetails').removeClass('d-none');
                    }
                } else {
                    $('#connectionStatus').html('<div class="alert alert-danger"><i class="fas fa-times-circle me-2"></i>Connection failed: ' + (response.error || 'Unknown error') + '</div>');
                }
            },
            error: function(xhr, status, error) {
                $('#connectionStatus').html('<div class="alert alert-danger"><i class="fas fa-times-circle me-2"></i>Error testing connection: ' + error + '</div>');
            }
        });
    });
    
    // Handle saved sender selection
    $(document).on('click', '.saved-sender', function(e) {
        e.preventDefault();
        const email = $(this).data('email');
        $('#sender').val(email);
    });
    
    // Handle saved recipient selection
    $(document).on('click', '.saved-recipient', function(e) {
        e.preventDefault();
        const email = $(this).data('email');
        // Always replace entire field with selected recipient
        $('#recipients').val(email);
    });
    
    // Save current sender
    $(document).on('click', '#saveSender', function(e) {
        e.preventDefault();
        const email = $('#sender').val();
        if (!email) {
            alert('Please enter an email address first');
            return;
        }
        
        // Save the sender
        $.ajax({
            url: '/save_sender',
            type: 'POST',
            data: JSON.stringify({ email: email }),
            contentType: 'application/json',
            success: function(response) {
                if (response.success) {
                    alert('Sender saved successfully');
                    // Reload the page to update the dropdown
                    location.reload();
                } else {
                    alert('Error saving sender: ' + response.message);
                }
            },
            error: function() {
                alert('Error saving sender');
            }
        });
    });
    
    // Save current recipient
    $(document).on('click', '#saveRecipient', function(e) {
        e.preventDefault();
        const recipients = $('#recipients').val();
        if (!recipients) {
            alert('Please enter at least one recipient first');
            return;
        }
        
        // If multiple recipients, ask which one to save
        const recipientList = recipients.split(',').map(r => r.trim());
        let emailToSave = '';
        
        if (recipientList.length === 1) {
            // Only one recipient, save it
            emailToSave = recipientList[0];
        } else {
            // Multiple recipients, ask which one to save
            const recipient = prompt('Multiple recipients found. Please enter the one you want to save:');
            if (!recipient) return;
            emailToSave = recipient.trim();
        }
        
        if (!emailToSave) {
            alert('No recipient selected to save');
            return;
        }
        
        // Save the recipient
        $.ajax({
            url: '/save_recipient',
            type: 'POST',
            data: JSON.stringify({ email: emailToSave }),
            contentType: 'application/json',
            success: function(response) {
                if (response.success) {
                    alert('Recipient saved successfully');
                    // Reload the page to update the dropdown
                    location.reload();
                } else {
                    alert('Error saving recipient: ' + response.message);
                }
            },
            error: function() {
                alert('Error saving recipient');
            }
        });
    });
});
