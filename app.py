import os
import logging
import logging.handlers
import socket
import time
import uuid
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from smtp_tool import SMTPTool
from config_manager import ConfigManager
from email_validator import validate_email

# Configure logging
# Get log directory from environment variable or default to current directory
log_dir = os.environ.get('SMTP_LOG_DIR', '.')
log_level = os.environ.get('LOG_LEVEL', 'DEBUG').upper()

# Create log directory if it doesn't exist
os.makedirs(log_dir, exist_ok=True)

# Configure logging with rotating file handler for better log management
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, "smtp_tool.log"),
            maxBytes=10485760,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-for-development")
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max upload size

# Initialize config manager
config_manager = ConfigManager()

# Initialize SMTP tool
smtp_tool = SMTPTool()

# Initialize default templates if none exist
def init_default_templates():
    templates = config_manager.get_templates()
    if not templates:
        # Plain text template
        config_manager.add_template({
            'name': 'Plain Text Example',
            'subject': 'Test Email - Plain Text',
            'body_type': 'plain',
            'body': """Hello,

This is a sample plain text email for testing SMTP servers.

Features to note:
- No formatting
- Simple text content
- Can be used to test basic email delivery

Regards,
SMTP Testing Tool"""
        })
        
        # HTML template
        config_manager.add_template({
            'name': 'HTML Example',
            'subject': 'Test Email - HTML Format',
            'body_type': 'html',
            'body': """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>HTML Email Test</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
    <header style="background-color: #4a69bd; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">HTML Email Test</h1>
    </header>
    
    <div style="padding: 20px;">
        <p>This is a <strong>sample HTML email</strong> for testing SMTP servers.</p>
        
        <h2 style="color: #4a69bd; border-bottom: 1px solid #ddd; padding-bottom: 10px;">Features to note:</h2>
        
        <ul style="list-style-type: circle; padding-left: 20px;">
            <li>HTML formatting</li>
            <li>CSS styling</li>
            <li>Unicode support: こんにちは (Hello)</li>
        </ul>
        
        <div style="background-color: #f8f9fa; border-left: 4px solid #4a69bd; margin: 20px 0; padding: 15px;">
            This is an example information box to show more complex HTML.
        </div>
        
        <p>You can test how your email client renders various HTML elements:</p>
        
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <tr style="background-color: #4a69bd; color: white;">
                <th style="padding: 10px; border: 1px solid #ddd;">Element</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Support</th>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">Tables</td>
                <td style="padding: 10px; border: 1px solid #ddd;">✓</td>
            </tr>
            <tr style="background-color: #f2f2f2;">
                <td style="padding: 10px; border: 1px solid #ddd;">Styled text</td>
                <td style="padding: 10px; border: 1px solid #ddd;">✓</td>
            </tr>
        </table>
    </div>
    
    <footer style="background-color: #f2f2f2; padding: 15px; text-align: center; font-size: 12px;">
        <p>This email was sent from the SMTP Testing Tool</p>
    </footer>
</body>
</html>"""
        })
        
        # EICAR Test
        config_manager.add_template({
            'name': 'EICAR Antivirus Test',
            'subject': 'EICAR Antivirus Test File',
            'body_type': 'plain',
            'body': """This email contains the EICAR antivirus test file as an attachment.

The EICAR test file is a standard test file developed by the European Institute for Computer Antivirus Research to safely test antivirus software without using actual malware.

When this email is delivered, most antivirus systems should detect the attachment as a threat, even though it's completely harmless.

Note: Your email system or antivirus might block this email entirely.
"""
        })
        
        # Individual test templates for each authentication mechanism
        # SPF Test
        config_manager.add_template({
            'name': 'SPF Test',
            'subject': 'SPF Authentication Test',
            'body_type': 'plain',
            'body': """This is a test email specifically for checking SPF validation.

The Sender Policy Framework (SPF) is an email authentication method designed to detect email spoofing.
When this email is received, the receiving server should check whether the sending server is authorized
to send email on behalf of the domain in the From address.

If properly implemented, this test message will help verify SPF functionality.
"""
        })
        
        # DKIM Test
        config_manager.add_template({
            'name': 'DKIM Test',
            'subject': 'DKIM Authentication Test',
            'body_type': 'plain',
            'body': """This is a test email specifically for checking DKIM validation.

DomainKeys Identified Mail (DKIM) provides a digital signature that lets the recipient verify
that an email was actually sent by the claimed sender, and that the message wasn't altered in transit.

When checking this test email, examine the headers to verify DKIM signatures.
"""
        })

        # DMARC Test
        config_manager.add_template({
            'name': 'DMARC Test',
            'subject': 'DMARC Authentication Test',
            'body_type': 'plain',
            'body': """This is a test email specifically for checking DMARC validation.

Domain-based Message Authentication, Reporting, and Conformance (DMARC) works with SPF and DKIM
to help email receivers determine if the email is legitimately from the sender domain.

When checking this test email, examine the headers for DMARC validation results.
"""
        })
        
        # Combined SPF/DKIM/DMARC - Internal use only, not shown in templates page
        config_manager.add_template({
            'name': '_SPF_DKIM_DMARC_Combined',
            'subject': 'Combined SPF/DKIM/DMARC Authentication Test',
            'body_type': 'plain',
            'body': """This is a comprehensive test email for checking all email authentication mechanisms.

This email tests:
1. SPF (Sender Policy Framework) validation 
2. DKIM (DomainKeys Identified Mail) signatures
3. DMARC (Domain-based Message Authentication, Reporting, and Conformance) compliance

When checking this email, examine the full headers to see the validation results for all three mechanisms.
"""
        })
        
        logger.info("Initialized default email templates")

init_default_templates()

@app.route('/')
def index():
    """Render the main page for sending emails"""
    smtp_profiles = config_manager.get_profiles()
    email_templates = config_manager.get_templates()
    settings = config_manager.get_settings()
    
    # Get saved email addresses
    saved_senders = settings.get('saved_senders', [])
    saved_recipients = settings.get('saved_recipients', [])
    default_sender = settings.get('default_sender', '')
    
    return render_template('index.html', 
                          smtp_profiles=smtp_profiles,
                          email_templates=email_templates,
                          saved_senders=saved_senders,
                          saved_recipients=saved_recipients,
                          default_sender=default_sender)

# Global request cache for duplicate prevention
_request_cache = {}

@app.route('/send_email', methods=['POST'])
def send_email():
    """API endpoint to send an email"""
    # Simple semaphore lock to prevent duplicate submissions
    lock_file = '/tmp/email_sending_lock'
    
    try:
        # Check if lock exists and is recent (within 5 seconds)
        if os.path.exists(lock_file):
            mod_time = os.path.getmtime(lock_file)
            if time.time() - mod_time < 5:
                logger.warning(f"Duplicate submission prevented by lock file")
                return jsonify({'success': True, 'message': 'Email already sent (duplicate prevented)'})
                
        # Create new lock file
        with open(lock_file, 'w') as f:
            f.write(str(time.time()))
    except Exception as e:
        logger.error(f"Error with lock file: {str(e)}")
    
    # Get body type for HTML processing
    body_type = request.form.get('body_type', 'plain')
    if body_type == 'html':
        logger.info("Processing HTML email")
    
    try:
        # Get form data
        profile_name = request.form.get('profile')
        sender = request.form.get('sender', '')
        recipients_str = request.form.get('recipients', '')
        recipients = recipients_str.split(',') if recipients_str else []
        
        cc_str = request.form.get('cc', '')
        cc = cc_str.split(',') if cc_str else []
        
        bcc_str = request.form.get('bcc', '')
        bcc = bcc_str.split(',') if bcc_str else []
        
        subject = request.form.get('subject', '')
        body_type = request.form.get('body_type', 'plain')
        body = request.form.get('body', '')
        
        # Validate email addresses
        all_recipients = recipients + cc + bcc
        for email in all_recipients + [sender]:
            if email and email.strip():
                try:
                    validate_email(email.strip())
                except Exception as e:
                    return jsonify({'success': False, 'message': f'Invalid email address: {email} - {str(e)}'})
        
        # Get profile configuration
        profile = config_manager.get_profile(profile_name)
        if not profile:
            return jsonify({'success': False, 'message': f'Profile {profile_name} not found'})
        
        # Get attachments
        attachments = []
        if 'attachments' in request.files:
            files = request.files.getlist('attachments')
            for file in files:
                if file.filename:
                    temp_path = os.path.join('/tmp', file.filename)
                    file.save(temp_path)
                    attachments.append(temp_path)
        
        # Check for special attachment
        special_attachment = request.form.get('special_attachment')
        if special_attachment:
            try:
                attachment_data = json.loads(special_attachment)
                attachment_type = attachment_data.get('type')
                
                if attachment_type == 'pdf':
                    filename, data = smtp_tool.create_pdf_attachment(
                        malformed=attachment_data.get('malformed', False),
                        active_content=attachment_data.get('active_content', False)
                    )
                    temp_path = os.path.join('/tmp', filename)
                    with open(temp_path, 'wb') as f:
                        f.write(data)
                    attachments.append(temp_path)
                
                # Word and Excel attachment types have been removed
                
                elif attachment_type == 'eicar':
                    filename, data = smtp_tool.create_eicar_attachment()
                    temp_path = os.path.join('/tmp', filename)
                    with open(temp_path, 'wb') as f:
                        f.write(data)
                    attachments.append(temp_path)
            
            except Exception as e:
                logger.exception(f"Failed to create special attachment: {str(e)}")
        
        # Get application settings
        settings = config_manager.get_settings()
        
        # Get any custom headers for SPF/DKIM tests
        custom_headers = {}
        if request.form.get('custom_headers'):
            try:
                custom_headers_str = request.form.get('custom_headers')
                if custom_headers_str:
                    custom_headers = json.loads(custom_headers_str)
            except Exception as e:
                logger.warning(f"Failed to parse custom headers: {str(e)}")
                
        # Send email using the SMTP tool
        result = smtp_tool.send_email(
            server=profile['server'],
            port=profile['port'],
            use_tls=profile['use_tls'],
            use_ssl=profile['use_ssl'],
            username=profile['username'],
            password=profile['password'],
            sender=sender,
            recipients=recipients,
            cc=cc,
            bcc=bcc,
            subject=subject,
            body=body,
            body_type=body_type,
            attachments=attachments,
            hostname=settings.get('send_hostname'),
            custom_headers=custom_headers
        )
        
        # Clean up temporary files
        for attachment in attachments:
            if os.path.exists(attachment):
                os.remove(attachment)
        
        if result['success']:
            # Log the successful email send
            log_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'profile': profile_name,
                'server': f"{profile['server']}:{profile['port']}",
                'sender': sender,
                'recipients': recipients,
                'cc': cc,
                'bcc': bcc,
                'subject': subject,
                'status': 'Success',
                'attachments': [os.path.basename(att) for att in attachments] if attachments else [],
                'message_id': result.get('message_id', ''),
                'smtp_log': result.get('smtp_log', [])
            }
            
            # Add any additional settings info if present
            if settings.get('log_message_content', False):
                log_entry['body'] = body
                log_entry['body_type'] = body_type
                
            config_manager.add_log_entry(log_entry)
            return jsonify({'success': True, 'message': 'Email sent successfully'})
        else:
            # Log the failed email send
            log_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'profile': profile_name,
                'server': f"{profile['server']}:{profile['port']}",
                'sender': sender,
                'recipients': recipients,
                'cc': cc,
                'bcc': bcc,
                'subject': subject,
                'status': 'Failed',
                'error': result['error'],
                'attachments': [os.path.basename(att) for att in attachments] if attachments else [],
                'smtp_log': result.get('smtp_log', [])
            }
            config_manager.add_log_entry(log_entry)
            return jsonify({'success': False, 'message': f'Failed to send email: {result["error"]}'})
    
    except Exception as e:
        logger.exception("Error sending email")
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'})

@app.route('/settings')
def settings():
    """Render the settings page for managing SMTP profiles"""
    smtp_profiles = config_manager.get_profiles()
    app_settings = config_manager.get_settings()
    return render_template('settings.html', smtp_profiles=smtp_profiles, settings=app_settings)

@app.route('/advanced_settings')
def advanced_settings():
    """Render the advanced settings page"""
    app_settings = config_manager.get_settings()
    return render_template('advanced_settings.html', settings=app_settings)

@app.route('/save_sender', methods=['POST'])
def save_sender():
    """API endpoint to save a sender email address"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        # Validate email
        try:
            validate_email(email)
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)})
        
        # Save the sender
        if config_manager.add_saved_sender(email):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Failed to save sender'})
    except Exception as e:
        logger.error(f"Error saving sender: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/save_recipient', methods=['POST'])
def save_recipient():
    """API endpoint to save a recipient email address"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        # Validate email
        try:
            validate_email(email)
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)})
        
        # Save the recipient
        if config_manager.add_saved_recipient(email):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Failed to save recipient'})
    except Exception as e:
        logger.error(f"Error saving recipient: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/delete_sender', methods=['POST'])
def delete_sender():
    """API endpoint to delete a saved sender email address"""
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data received in delete_sender request")
            return jsonify({'success': False, 'message': 'No data provided'})
            
        email = data.get('email')
        if not email:
            logger.error("No email provided in delete_sender request")
            return jsonify({'success': False, 'message': 'No email provided'})
            
        logger.info(f"Attempting to delete sender email: {email}")
        
        # Delete the sender
        result = config_manager.remove_saved_sender(email)
        logger.info(f"Delete sender result: {result}")
        
        if result:
            return jsonify({'success': True, 'message': 'Email deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to delete sender'})
    except Exception as e:
        logger.error(f"Error deleting sender: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/delete_recipient', methods=['POST'])
def delete_recipient():
    """API endpoint to delete a saved recipient email address"""
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data received in delete_recipient request")
            return jsonify({'success': False, 'message': 'No data provided'})
            
        email = data.get('email')
        if not email:
            logger.error("No email provided in delete_recipient request")
            return jsonify({'success': False, 'message': 'No email provided'})
            
        logger.info(f"Attempting to delete recipient email: {email}")
        
        # Delete the recipient
        result = config_manager.remove_saved_recipient(email)
        logger.info(f"Delete recipient result: {result}")
        
        if result:
            return jsonify({'success': True, 'message': 'Email deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to delete recipient'})
    except Exception as e:
        logger.error(f"Error deleting recipient: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/addresses')
def addresses():
    """Render the email addresses management page"""
    settings = config_manager.get_settings()
    saved_senders = settings.get('saved_senders', [])
    saved_recipients = settings.get('saved_recipients', [])
    
    return render_template('addresses.html', 
                          saved_senders=saved_senders,
                          saved_recipients=saved_recipients)

@app.route('/update_settings', methods=['POST'])
def update_settings():
    """API endpoint to update application settings"""
    try:
        # Get form data
        settings_data = {
            'send_hostname': request.form.get('send_hostname', ''),
            'default_sender': request.form.get('default_sender', ''),
            'log_level': request.form.get('log_level', 'INFO'),
            'log_retention_days': int(request.form.get('log_retention_days', 30)),
            'log_smtp_traffic': request.form.get('log_smtp_traffic') == 'on',
            'log_message_content': request.form.get('log_message_content') == 'on',
            'max_attachment_size_mb': int(request.form.get('max_attachment_size_mb', 10))
        }
        
        # Validate data
        if not settings_data['send_hostname']:
            settings_data['send_hostname'] = socket.gethostname()
            
        # Update settings
        config_manager.update_settings(settings_data)
        flash('Settings updated successfully', 'success')
        return redirect(url_for('advanced_settings'))
    
    except Exception as e:
        logger.exception("Error updating settings")
        flash(f'Error updating settings: {str(e)}', 'danger')
        return redirect(url_for('advanced_settings'))

@app.route('/add_profile', methods=['POST'])
def add_profile():
    """API endpoint to add a new SMTP profile"""
    try:
        profile_data = {
            'name': request.form.get('name'),
            'server': request.form.get('server'),
            'port': int(request.form.get('port', 25)),
            'use_tls': request.form.get('use_tls') == 'on',
            'use_ssl': request.form.get('use_ssl') == 'on',
            'username': request.form.get('username', ''),
            'password': request.form.get('password', '')
        }
        
        # Validate profile data
        if not profile_data['name'] or not profile_data['server']:
            return jsonify({'success': False, 'message': 'Profile name and server are required'})
        
        # Add the profile
        config_manager.add_profile(profile_data)
        flash('SMTP profile added successfully', 'success')
        return redirect(url_for('settings'))
    
    except Exception as e:
        logger.exception("Error adding profile")
        flash(f'Error adding profile: {str(e)}', 'danger')
        return redirect(url_for('settings'))

@app.route('/delete_profile/<name>', methods=['POST'])
def delete_profile(name):
    """API endpoint to delete an SMTP profile"""
    try:
        config_manager.delete_profile(name)
        flash(f'Profile {name} deleted successfully', 'success')
        return redirect(url_for('settings'))
    except Exception as e:
        logger.exception("Error deleting profile")
        flash(f'Error deleting profile: {str(e)}', 'danger')
        return redirect(url_for('settings'))

@app.route('/templates')
def templates():
    """Render the templates page for managing email templates"""
    all_templates = config_manager.get_templates()
    
    # Filter out internal templates (marked with underscore prefix)
    email_templates = {k: v for k, v in all_templates.items() if not k.startswith('_')}
    
    # Debug log
    template_names = list(all_templates.keys())
    filtered_names = list(email_templates.keys())
    logger.info(f"All templates: {template_names}")
    logger.info(f"Filtered templates: {filtered_names}")
    
    return render_template('templates.html', email_templates=email_templates)

@app.route('/add_template', methods=['POST'])
def add_template():
    """API endpoint to add a new email template"""
    try:
        template_data = {
            'name': request.form.get('name'),
            'subject': request.form.get('subject'),
            'body_type': request.form.get('body_type', 'plain'),
            'body': request.form.get('body')
        }
        
        # Validate template data
        if not template_data['name'] or not template_data['body']:
            return jsonify({'success': False, 'message': 'Template name and body are required'})
        
        # Handle file attachment if provided
        attachment_file = request.files.get('attachment')
        if attachment_file and attachment_file.filename:
            try:
                # Create attachment directory if it doesn't exist
                attachment_dir = os.path.join(config_manager.config_dir, 'attachments')
                os.makedirs(attachment_dir, exist_ok=True)
                
                # Save the attachment
                attachment_path = os.path.join(attachment_dir, secure_filename(attachment_file.filename))
                attachment_file.save(attachment_path)
                
                # Add attachment info to template data
                template_data['attachment'] = {
                    'filename': secure_filename(attachment_file.filename),
                    'path': attachment_path
                }
                
                logger.info(f"Saved attachment {attachment_file.filename} for template {template_data['name']}")
            except Exception as att_error:
                logger.error(f"Error saving attachment: {str(att_error)}")
                # Continue without attachment if there's an error
        
        # Add the template
        config_manager.add_template(template_data)
        flash('Email template added successfully', 'success')
        return redirect(url_for('templates'))
    
    except Exception as e:
        logger.exception("Error adding template")
        flash(f'Error adding template: {str(e)}', 'danger')
        return redirect(url_for('templates'))

@app.route('/delete_template/<name>', methods=['POST'])
def delete_template(name):
    """API endpoint to delete an email template"""
    try:
        config_manager.delete_template(name)
        flash(f'Template {name} deleted successfully', 'success')
        return redirect(url_for('templates'))
    except Exception as e:
        logger.exception("Error deleting template")
        flash(f'Error deleting template: {str(e)}', 'danger')
        return redirect(url_for('templates'))

@app.route('/get_template/<name>')
def get_template(name):
    """API endpoint to get a specific email template"""
    try:
        template = config_manager.get_template(name)
        if template:
            return jsonify({'success': True, 'template': template})
        else:
            return jsonify({'success': False, 'message': f'Template {name} not found'})
    except Exception as e:
        logger.exception("Error getting template")
        return jsonify({'success': False, 'message': f'Error getting template: {str(e)}'})

@app.route('/logs')
def logs():
    """Render the logs page for viewing email sending history"""
    log_entries = config_manager.get_logs()
    return render_template('logs.html', log_entries=log_entries)

@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    """API endpoint to clear all logs"""
    try:
        config_manager.clear_logs()
        flash('Logs cleared successfully', 'success')
        return redirect(url_for('logs'))
    except Exception as e:
        logger.exception("Error clearing logs")
        flash(f'Error clearing logs: {str(e)}', 'danger')
        return redirect(url_for('logs'))

@app.route('/test_connection', methods=['POST'])
def test_connection():
    """API endpoint to test an SMTP connection"""
    try:
        profile_name = request.form.get('profile')
        profile = config_manager.get_profile(profile_name)
        
        if not profile:
            return jsonify({'success': False, 'message': f'Profile {profile_name} not found'})
        
        # Get application settings for hostname configuration
        settings = config_manager.get_settings()
        
        result = smtp_tool.test_connection(
            server=profile['server'],
            port=profile['port'],
            use_tls=profile['use_tls'],
            use_ssl=profile['use_ssl'],
            username=profile['username'],
            password=profile['password'],
            hostname=settings.get('send_hostname')
        )
        
        return jsonify(result)
    
    except Exception as e:
        logger.exception("Error testing connection")
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'})

@app.route('/get_test_data')
def get_test_data():
    """API endpoint to get test email data for special test emails"""
    try:
        test_type = request.args.get('test_type')
        settings = config_manager.get_settings()
        default_sender = settings.get('default_sender', f'smtp@{socket.getfqdn()}')
        
        # Get recipient from the first request parameter or use a default
        recipient = request.args.get('recipient', default_sender)
        
        # Base test data
        test_data = {
            'sender': default_sender,
            'recipients': [recipient],
            'cc': [],
            'bcc': [],
            'body_type': 'plain'
        }
        
        if test_type == 'pdf':
            # PDF attachment test
            test_data.update({
                'subject': 'PDF Attachment Test',
                'body': 'This email contains a standard PDF attachment generated for testing purposes.',
                'special_attachment': {
                    'type': 'pdf',
                    'malformed': False,
                    'active_content': False
                }
            })
        
        elif test_type == 'pdf-malformed':
            # Malformed PDF attachment test
            test_data.update({
                'subject': 'Malformed PDF Test',
                'body': 'This email contains a malformed PDF attachment intended for testing how systems handle invalid PDFs.',
                'special_attachment': {
                    'type': 'pdf',
                    'malformed': True,
                    'active_content': False
                }
            })
        
        elif test_type == 'pdf-active':
            # PDF with active content
            test_data.update({
                'subject': 'PDF with Active Content Test',
                'body': 'This email contains a PDF with simulated active content (JavaScript) for testing security policies.',
                'special_attachment': {
                    'type': 'pdf',
                    'malformed': False,
                    'active_content': True
                }
            })
        
        elif test_type == 'docx':
            # DOCX attachment test
            test_data.update({
                'subject': 'DOCX Attachment Test',
                'body': 'This email contains a DOCX (Word document) attachment generated for testing purposes.',
                'special_attachment': {
                    'type': 'docx',
                    'active_content': False
                }
            })
        
        elif test_type == 'xlsx':
            # XLSX attachment test
            test_data.update({
                'subject': 'XLSX Attachment Test',
                'body': 'This email contains an XLSX (Excel spreadsheet) attachment generated for testing purposes.',
                'special_attachment': {
                    'type': 'xlsx',
                    'active_content': False
                }
            })
        
        elif test_type == 'eicar':
            # EICAR antivirus test
            test_data.update({
                'subject': 'EICAR Antivirus Test File',
                'body': """This email contains the EICAR antivirus test file as an attachment.

The EICAR test file is a standard test file developed by the European Institute for Computer Antivirus Research to safely test antivirus software without using actual malware.

When this email is delivered, most antivirus systems should detect the attachment as a threat, even though it's completely harmless.

Note: Your email system or antivirus might block this email entirely.""",
                'special_attachment': {
                    'type': 'eicar'
                }
            })
        
        elif test_type == 'spf':
            # SPF test only
            spf_test = smtp_tool.create_spf_test_email(recipient)
            test_data.update(spf_test)
            
        elif test_type == 'dkim':
            # DKIM test only
            dkim_test = smtp_tool.create_dkim_test_email(recipient)
            # Log the DKIM header for debugging
            logger.info(f"DKIM test email created with headers: {dkim_test.get('custom_headers', {})}")
            test_data.update(dkim_test)
            
        elif test_type == 'dmarc':
            # DMARC test only
            dmarc_test = smtp_tool.create_dmarc_test_email(recipient)
            test_data.update(dmarc_test)
            
        elif test_type == 'spf-dkim-dmarc':
            # Combined SPF/DKIM/DMARC test
            combined_test = smtp_tool.create_spf_dkim_dmarc_test_email(recipient)
            test_data.update(combined_test)
            
        else:
            return jsonify({'success': False, 'message': f'Unknown test type: {test_type}'})
        
        return jsonify({'success': True, 'test_data': test_data})
    
    except Exception as e:
        logger.exception("Error getting test data")
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'})

@app.route('/health_check')
def health_check():
    """Simple health check endpoint for Docker and monitoring"""
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
