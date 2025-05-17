$(document).ready(function() {
    // Handle the delete profile action
    $('.delete-profile').click(function() {
        const profileName = $(this).data('profile');
        $('#deleteProfileName').text(profileName);
        $('#deleteProfileForm').attr('action', '/delete_profile/' + profileName);
        $('#deleteProfileModal').modal('show');
    });
    
    // Handle the edit profile action to populate the edit modal
    $('.edit-profile').click(function() {
        const profileName = $(this).data('profile');
        const server = $(this).data('server');
        const port = $(this).data('port');
        const useTls = $(this).data('tls');
        const useSsl = $(this).data('ssl');
        const username = $(this).data('username');
        
        // Populate the edit form
        $('#editProfileName').val(profileName);
        $('#editServer').val(server);
        $('#editPort').val(port);
        
        // Set security options
        if (useTls === true) {
            $('#editSecurityTLS').prop('checked', true);
        } else if (useSsl === true) {
            $('#editSecuritySSL').prop('checked', true);
        } else {
            $('#editSecurityNone').prop('checked', true);
        }
        
        // Set authentication options
        if (username && username.length > 0) {
            $('#editUseAuthentication').prop('checked', true);
            $('#editUsername').val(username);
            $('#editPassword').val(''); // Clear password field
            $('#editAuthFields').show();
        } else {
            $('#editUseAuthentication').prop('checked', false);
            $('#editUsername').val('');
            $('#editPassword').val('');
            $('#editAuthFields').hide();
        }
    });
    
    // Handle the test profile connection
    $('.test-profile').click(function() {
        const profileName = $(this).data('profile');
        
        // Show test connection modal
        $('#testConnectionModal').modal('show');
        $('#testConnectionStatus').text('Testing connection...');
        $('#testConnectionDetails').addClass('d-none');
        $('#testConnectionCapabilities').empty();
        
        // Send test request
        $.ajax({
            url: '/test_connection',
            type: 'POST',
            data: {
                profile: profileName
            },
            success: function(response) {
                if (response.success) {
                    $('#testConnectionStatus').html('<div class="alert alert-success"><i class="fas fa-check-circle me-2"></i>' + response.message + '</div>');
                    
                    // Show capabilities if available
                    if (response.capabilities && response.capabilities.length > 0) {
                        $('#testConnectionCapabilities').empty();
                        response.capabilities.forEach(function(capability) {
                            $('#testConnectionCapabilities').append('<li>' + capability + '</li>');
                        });
                        $('#testConnectionDetails').removeClass('d-none');
                    }
                } else {
                    $('#testConnectionStatus').html('<div class="alert alert-danger"><i class="fas fa-times-circle me-2"></i>Connection failed: ' + (response.error || 'Unknown error') + '</div>');
                }
            },
            error: function(xhr, status, error) {
                $('#testConnectionStatus').html('<div class="alert alert-danger"><i class="fas fa-times-circle me-2"></i>Error testing connection: ' + error + '</div>');
            }
        });
    });
    
    // Prevent using both TLS and SSL at the same time in the add profile form
    $('#use_tls').change(function() {
        if ($(this).is(':checked')) {
            $('#use_ssl').prop('checked', false);
        }
    });
    
    $('#use_ssl').change(function() {
        if ($(this).is(':checked')) {
            $('#use_tls').prop('checked', false);
        }
    });
    
    // Dynamically update port based on security selection
    $('#use_tls, #use_ssl').change(function() {
        if ($('#use_ssl').is(':checked')) {
            $('#port').val('465');
        } else if ($('#use_tls').is(':checked')) {
            $('#port').val('587');
        } else {
            $('#port').val('25');
        }
    });
    
    // Security options for edit modal
    $('input[name="security"]').change(function() {
        if ($(this).val() === 'ssl') {
            $('#editPort').val('465');
        } else if ($(this).val() === 'tls') {
            $('#editPort').val('587');
        } else {
            $('#editPort').val('25');
        }
    });
    
    // Toggle authentication fields in edit modal
    $('#editUseAuthentication').change(function() {
        if ($(this).is(':checked')) {
            $('#editAuthFields').show();
        } else {
            $('#editAuthFields').hide();
            $('#editUsername').val('');
            $('#editPassword').val('');
        }
    });
    
    // Handle edit profile form submission
    $('#editProfileForm').submit(function(e) {
        e.preventDefault();
        
        // Get form data
        const profileName = $('#editProfileName').val();
        const server = $('#editServer').val();
        const port = $('#editPort').val();
        
        // Determine security settings
        let use_tls = false;
        let use_ssl = false;
        
        if ($('#editSecurityTLS').is(':checked')) {
            use_tls = true;
        } else if ($('#editSecuritySSL').is(':checked')) {
            use_ssl = true;
        }
        
        // Get authentication settings
        let username = '';
        let password = '';
        
        if ($('#editUseAuthentication').is(':checked')) {
            username = $('#editUsername').val();
            password = $('#editPassword').val();
        }
        
        // Send the profile data to server
        $.ajax({
            url: '/add_profile',
            type: 'POST',
            data: {
                name: profileName,
                server: server,
                port: port,
                security: use_ssl ? 'ssl' : (use_tls ? 'tls' : 'none'),
                username: username,
                password: password
            },
            success: function(response) {
                if (response.success) {
                    // Close the modal and reload the page
                    $('#editProfileModal').modal('hide');
                    location.reload();
                } else {
                    alert('Error updating profile: ' + (response.message || 'Unknown error'));
                }
            },
            error: function(xhr, status, error) {
                alert('Error updating profile: ' + error);
            }
        });
    });
});
