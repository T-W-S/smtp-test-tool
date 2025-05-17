// Fix for duplicate submissions and HTML email handling
document.addEventListener('DOMContentLoaded', function() {
    // 1. Fix HTML toggle functionality
    const htmlToggle = document.getElementById('htmlToggle');
    const bodyTypeField = document.getElementById('body_type');
    
    if (htmlToggle && bodyTypeField) {
        htmlToggle.addEventListener('change', function() {
            bodyTypeField.value = this.checked ? 'html' : 'plain';
            console.log("Body type set to: " + bodyTypeField.value);
        });
    }
    
    // 2. Add duplicate prevention with unique request ID
    const emailForm = document.getElementById('emailForm');
    if (emailForm) {
        // Add a hidden field for request ID if it doesn't exist
        let requestIdField = document.getElementById('request_id');
        if (!requestIdField) {
            requestIdField = document.createElement('input');
            requestIdField.type = 'hidden';
            requestIdField.id = 'request_id';
            requestIdField.name = 'request_id';
            emailForm.appendChild(requestIdField);
        }
        
        // Generate a unique ID for this page load
        const uniqueId = Date.now() + '-' + Math.random().toString(36).substring(2, 10);
        requestIdField.value = uniqueId;
        
        // Track form submission state
        let isSubmitting = false;
        
        // Override the form submission
        emailForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Prevent duplicate submissions
            if (isSubmitting) {
                console.log('Form already submitting, preventing duplicate');
                return false;
            }
            
            // Set submission flag and disable send button
            isSubmitting = true;
            const sendButton = document.getElementById('sendButton');
            if (sendButton) {
                sendButton.disabled = true;
                sendButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';
            }
            
            // Submit the form data via AJAX
            const formData = new FormData(this);
            
            fetch('/send_email', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Show result in a notification
                if (data.success) {
                    showNotification('success', data.message || 'Email sent successfully!');
                } else {
                    showNotification('error', data.error || 'Failed to send email');
                }
                
                // Reset form state after 2 seconds
                setTimeout(function() {
                    isSubmitting = false;
                    if (sendButton) {
                        sendButton.disabled = false;
                        sendButton.innerHTML = '<i class="fas fa-paper-plane me-2"></i>Send Email';
                    }
                }, 2000);
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('error', 'Network error when sending email');
                
                // Reset form state
                isSubmitting = false;
                if (sendButton) {
                    sendButton.disabled = false;
                    sendButton.innerHTML = '<i class="fas fa-paper-plane me-2"></i>Send Email';
                }
            });
        });
    }
    
    // Helper function to show notifications
    function showNotification(type, message) {
        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
        const alertIcon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-triangle';
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert ${alertClass} alert-dismissible fade show mt-3`;
        alertDiv.setAttribute('role', 'alert');
        alertDiv.innerHTML = `
            <i class="fas ${alertIcon} me-2"></i>${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Find the notifications area or create one
        let notificationsArea = document.getElementById('notifications');
        if (!notificationsArea) {
            notificationsArea = document.createElement('div');
            notificationsArea.id = 'notifications';
            notificationsArea.className = 'mt-3';
            const formContainer = document.querySelector('.card-body');
            if (formContainer) {
                formContainer.prepend(notificationsArea);
            }
        }
        
        notificationsArea.appendChild(alertDiv);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 300);
        }, 5000);
    }
});