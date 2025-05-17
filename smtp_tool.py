import smtplib
import ssl
import os
import logging
import mimetypes
import socket
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email.utils import formataddr, formatdate, make_msgid
from email import encoders
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Configure logging
logger = logging.getLogger(__name__)

# Set up file logging
log_dir = os.environ.get('SMTP_LOG_DIR', '.')
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'smtp_tool.log')

# Add file handler to SMTP tool logger
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

class SMTPTool:
    """Class for handling SMTP operations including sending emails and testing connections"""
    
    def __init__(self):
        """Initialize the SMTP Tool"""
        self.eicar_string = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
        
    def send_email(self, server, port, use_tls, use_ssl, username, password, 
                   sender, recipients, cc=None, bcc=None, subject='', body='', 
                   body_type='plain', attachments=None, custom_headers=None,
                   hostname=None, ehlo_as=None, helo_as=None, mail_options=None):
        """
        Send an email using the provided SMTP server and credentials
        
        Args:
            server (str): SMTP server address
            port (int): SMTP server port
            use_tls (bool): Whether to use STARTTLS
            use_ssl (bool): Whether to use SSL/TLS connection
            username (str): SMTP username for authentication
            password (str): SMTP password for authentication
            sender (str): Email sender address
            recipients (list): List of recipient email addresses
            cc (list, optional): List of CC email addresses
            bcc (list, optional): List of BCC email addresses
            subject (str, optional): Email subject
            body (str, optional): Email body
            body_type (str, optional): Email body type ('plain' or 'html')
            attachments (list, optional): List of attachment file paths
            custom_headers (dict, optional): Dictionary of custom headers
            hostname (str, optional): Hostname to use for SMTP connection
            ehlo_as (str, optional): Domain to use in EHLO command
            helo_as (str, optional): Domain to use in HELO command
            mail_options (list, optional): Mail options for SMTP sendmail
            
        Returns:
            dict: Result of the operation with 'success' and optionally 'error' keys
        """
        smtp_log = []
        
        # Create a log capture function
        def log_smtp(smtp_instance, prefix=""):
            original_debug = smtp_instance._print_debug
            
            def custom_debug(self, *args):
                message = " ".join(str(a) for a in args)
                smtp_log.append(f"{prefix}{message}")
                return original_debug(self, *args)
            
            smtp_instance._print_debug = custom_debug
        
        try:
            # Initialize lists if None
            cc = cc or []
            bcc = bcc or []
            attachments = attachments or []
            custom_headers = custom_headers or {}
            mail_options = mail_options or []
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)
            if cc:
                msg['Cc'] = ', '.join(cc)
            msg['Subject'] = subject
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid(domain=hostname or socket.getfqdn())
            
            # Add custom headers with special handling - different approach
            logging.info(f"Email has {len(custom_headers)} custom headers to process")
            
            # Special handling for DKIM headers - force raw header insertion
            has_dkim = False
            dkim_value = None
            
            # First handle all headers
            for header_name, header_value in custom_headers.items():
                # Add all headers to the message using standard method
                msg[header_name] = header_value
                logging.info(f"Added header: {header_name}")
                
                # If it's a DKIM header, note that for special handling
                if header_name == 'DKIM-Signature':
                    has_dkim = True
                    dkim_value = header_value
                    logging.info("DKIM header detected, will get special handling")
            
            # Special handling for DKIM - explicitly add it last
            if has_dkim and dkim_value:
                # Force raw header - this is a workaround for some email libraries
                raw_headers = msg.as_string().split('\n\n')[0]
                logging.info(f"Current headers: {raw_headers}")
                
                # Ensure it's in the raw message too
                if 'DKIM-Signature' not in raw_headers:
                    logging.info("DKIM header not found in raw headers, adding manually")
                    # Use standard method to add DKIM header
                    try:
                        # Standard way to add a header
                        msg['DKIM-Signature'] = dkim_value
                        logging.info("Added DKIM header via standard method")
                    except Exception as e:
                        logging.warning(f"Failed to add DKIM header: {e}")
                
                # Log the attempt
                logging.info(f"DKIM header processing complete with value: {dkim_value}")
            
            # Attach the body with proper handling of HTML content
            if body_type == 'html':
                # Ensure content has proper HTML structure
                if not body.strip().startswith('<!DOCTYPE') and not body.strip().startswith('<html'):
                    body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
</head>
<body>
  {body}
</body>
</html>"""
                # Log that we're sending HTML content
                logging.info(f"Sending email with HTML body type, length: {len(body)}")
                
            # Create the MIME part with the correct content type
            msg.attach(MIMEText(body, body_type))
            
            # Attach files
            for attachment_path in attachments:
                if os.path.exists(attachment_path):
                    with open(attachment_path, 'rb') as f:
                        attachment_data = f.read()
                        
                    attachment_filename = os.path.basename(attachment_path)
                    content_type, encoding = mimetypes.guess_type(attachment_path)
                    if content_type is None or encoding is not None:
                        content_type = 'application/octet-stream'
                    
                    maintype, subtype = content_type.split('/', 1)
                    attachment = MIMEApplication(attachment_data, subtype)
                    
                    attachment.add_header('Content-Disposition', 'attachment', 
                                         filename=attachment_filename)
                    msg.attach(attachment)
            
            # Connect to the SMTP server
            if use_ssl:
                context = ssl.create_default_context()
                smtp = smtplib.SMTP_SSL(server, port, local_hostname=hostname, context=context)
            else:
                smtp = smtplib.SMTP(server, port, local_hostname=hostname)
            
            # Enable logging
            smtp.set_debuglevel(1)
            log_smtp(smtp)
                
            # Use EHLO/HELO with custom domain if specified
            if ehlo_as:
                smtp.ehlo(ehlo_as)
            elif helo_as:
                smtp.helo(helo_as)
            
            # Use TLS if requested
            if use_tls and not use_ssl:
                context = ssl.create_default_context()
                smtp.starttls(context=context)
                # Need to EHLO again after STARTTLS
                if ehlo_as:
                    smtp.ehlo(ehlo_as)
            
            # Authenticate if credentials are provided
            if username and password:
                smtp.login(username, password)
            
            # Send the email
            all_recipients = recipients + cc + bcc
            smtp.sendmail(sender, all_recipients, msg.as_string(), mail_options=mail_options)
            
            # Close the connection
            smtp.quit()
            
            logger.info(f"Email sent successfully to {', '.join(recipients)}")
            return {
                'success': True,
                'smtp_log': smtp_log,
                'message_id': msg['Message-ID']
            }
            
        except Exception as e:
            logger.exception(f"Failed to send email: {str(e)}")
            return {
                'success': False, 
                'error': str(e),
                'smtp_log': smtp_log
            }
    
    def test_connection(self, server, port, use_tls, use_ssl, username, password, 
                        hostname=None, ehlo_as=None, helo_as=None):
        """
        Test the connection to an SMTP server
        
        Args:
            server (str): SMTP server address
            port (int): SMTP server port
            use_tls (bool): Whether to use STARTTLS
            use_ssl (bool): Whether to use SSL/TLS connection
            username (str): SMTP username for authentication
            password (str): SMTP password for authentication
            hostname (str, optional): Hostname to use for SMTP connection
            ehlo_as (str, optional): Domain to use in EHLO command
            helo_as (str, optional): Domain to use in HELO command
            
        Returns:
            dict: Result of the operation with 'success' and optionally 'error' keys
        """
        smtp_log = []
        
        # Create a log capture function
        def log_smtp(smtp_instance, prefix=""):
            original_debug = smtp_instance._print_debug
            
            def custom_debug(self, *args):
                message = " ".join(str(a) for a in args)
                smtp_log.append(f"{prefix}{message}")
                return original_debug(self, *args)
            
            smtp_instance._print_debug = custom_debug
            
        try:
            # Connect to the SMTP server
            if use_ssl:
                context = ssl.create_default_context()
                smtp = smtplib.SMTP_SSL(server, port, local_hostname=hostname, context=context)
            else:
                smtp = smtplib.SMTP(server, port, local_hostname=hostname)
            
            # Enable logging
            smtp.set_debuglevel(1)
            log_smtp(smtp)
            
            # Use EHLO/HELO with custom domain if specified
            if ehlo_as:
                server_info = smtp.ehlo(ehlo_as)
            elif helo_as:
                server_info = smtp.helo(helo_as)
                # Get capabilities after HELO (some servers may not support this)
                try:
                    server_info = smtp.ehlo()
                except:
                    pass
            else:
                server_info = smtp.ehlo()
            
            # Use TLS if requested
            if use_tls and not use_ssl:
                context = ssl.create_default_context()
                smtp.starttls(context=context)
                # Need to EHLO again after STARTTLS
                if ehlo_as:
                    server_info = smtp.ehlo(ehlo_as)
                else:
                    server_info = smtp.ehlo()
            
            # Authenticate if credentials are provided
            if username and password:
                smtp.login(username, password)
            
            # Check the server capabilities
            capabilities = []
            if hasattr(server_info, '__getitem__') and len(server_info) > 1:
                for item in server_info[1]:
                    if isinstance(item, bytes):
                        item = item.decode('utf-8')
                    capabilities.append(item)
            
            # Close the connection
            smtp.quit()
            
            logger.info(f"Successfully connected to SMTP server {server}:{port}")
            return {
                'success': True, 
                'message': 'Connection successful', 
                'capabilities': capabilities,
                'smtp_log': smtp_log
            }
            
        except Exception as e:
            logger.exception(f"Failed to connect to SMTP server: {str(e)}")
            return {
                'success': False, 
                'error': str(e),
                'smtp_log': smtp_log
            }
    
    def create_eicar_attachment(self):
        """Create an EICAR test file attachment for antivirus testing
        
        Returns:
            tuple: (filename, attachment_data) for the EICAR test file
        """
        filename = "eicar.com"
        return filename, self.eicar_string.encode('utf-8')
    
    def create_pdf_attachment(self, filename="test.pdf", malformed=False, active_content=False):
        """Create a PDF attachment
        
        Args:
            filename (str): Name for the PDF file
            malformed (bool): Whether to create a malformed PDF
            active_content (bool): Whether to include active content
        
        Returns:
            tuple: (filename, attachment_data) for the PDF
        """
        buffer = BytesIO()
        
        if malformed:
            # Create a malformed PDF
            buffer.write(b"%PDF-1.7\n")
            buffer.write(b"1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n")
            buffer.write(b"2 0 obj\n<</Type/Pages/Kids[]/Count 0>>\nendobj\n")
            # Missing xref table and trailer
            buffer.write(b"This PDF is intentionally malformed for testing")
        else:
            # Create a normal PDF
            pdf = canvas.Canvas(buffer, pagesize=letter)
            pdf.drawString(100, 750, "Test PDF Document")
            pdf.drawString(100, 700, "Generated for SMTP Testing")
            
            if active_content:
                # Add clear indicators that this has active content
                pdf.setFillColorRGB(1, 0, 0)  # Red text
                pdf.drawString(100, 650, "WARNING: This PDF contains simulated active content!")
                pdf.setFillColorRGB(0, 0, 0)  # Back to black text
                pdf.drawString(100, 630, "This PDF simulates having JavaScript that would:")
                pdf.drawString(120, 610, "- Auto-execute when the document is opened")
                pdf.drawString(120, 590, "- Potentially access network resources")
                pdf.drawString(120, 570, "- Could attempt to exploit reader vulnerabilities")
                
                # Draw a fake button as a visual indicator
                pdf.setFillColorRGB(1, 0, 0)  # Red fill
                pdf.rect(100, 500, 200, 40, fill=1)
                pdf.setFillColorRGB(1, 1, 1)  # White text
                pdf.drawString(125, 520, "SIMULATED MALICIOUS BUTTON")
                
                # Add JavaScript indicator in metadata
                pdf.setAuthor("SMTP Testing Tool - Security Test")
                pdf.setTitle("TEST - PDF with Active Content")
                pdf.setSubject("SECURITY TEST - JavaScript simulation")
                pdf.setKeywords("security test javascript active content")
                
                # Add special comment to indicate this is a test file with simulated active content
                # This helps email security systems recognize it as potentially malicious
                buffer.write(b"%OpenAction <</S/JavaScript/JS(app.alert('This is a simulated JavaScript alert. In a real malicious PDF, arbitrary code could run here.\\nThis file is used for testing email security systems.'))>>")
            
            pdf.save()
        
        buffer.seek(0)
        return filename, buffer.getvalue()
    

        
    def create_spf_test_email(self, recipient):
        """Create an email specifically to test SPF validation
        
        Args:
            recipient (str): Recipient email address
            
        Returns:
            dict: Email data with sender, subject, body, and headers
        """
        # Use a sender domain that's likely to have strict SPF
        email_data = {
            'sender': 'spf-test@gmail.com',
            'recipients': [recipient],
            'subject': 'SPF Test Email',
            'body': """This is a test email specifically for checking SPF validation.
            
The From: address claims to be from gmail.com, but this email was not sent from Google's servers.
This should cause SPF (Sender Policy Framework) to fail because:
- Gmail has SPF records published in DNS
- This mail server is not authorized to send from gmail.com 
- The receiving server should detect this SPF failure

This test is useful for confirming that SPF checks are working properly on the receiving mail server.
""",
            'body_type': 'plain',
            'custom_headers': {
                'X-SMTP-Test': 'SPF-Test',
                'X-SPF-Test': 'This email should fail SPF validation'
            }
        }
        
        return email_data
        
    def create_dkim_test_email(self, recipient):
        """Create an email specifically to test DKIM validation
        
        Args:
            recipient (str): Recipient email address
            
        Returns:
            dict: Email data with sender, subject, body, and custom headers for DKIM testing
        """
        # Use a sender domain that's likely to enforce DKIM
        current_time = int(time.time())
        
        # Generate a more visible test signature matching real DKIM header format
        dkim_signature = f"""v=1; a=rsa-sha256; d=microsoft.com; s=s1024-meo;
        c=relaxed/relaxed; i=dkim-test@microsoft.com; t={current_time};
        h=from:subject:date:message-id:to:mime-version:content-type;
        bh=kMCKLEOZ9L1w0K1Y6XD/NwCjDt7lpmucjVRJ5RuL1fc=;
        b=Wm4raY1GPLYmqznZSNo0idkaM4Ua3ar5e5gqHSxkKFuGeNmGryeg+0zkoNpRsOCOGNvUGG547NF
        9c9xKAGnugj7XfnNvNpEhM3jU9KVbDyAIN2ai230UKwSA3EQ+7e4bjvipvwGx/NGXBjyqR0b/erke
        Jf9tSX6qAo+2FuurR8E="""
        
        logging.info(f"Created DKIM test email with signature: {dkim_signature}")
        
        email_data = {
            'sender': 'dkim-test@microsoft.com',
            'recipients': [recipient],
            'subject': 'DKIM Signature Test Email with Proper DKIM Header',
            'body': """This is a test email designed to show a realistic DKIM validation header.
            
The From: address claims to be from microsoft.com, and this email includes:
1. A properly formatted DKIM-Signature header for testing
2. The exact format matches real-world DKIM signatures

Because this is a test, the DKIM signature is invalid. In real emails:
- Microsoft signs all outgoing messages with their private key
- We don't have access to Microsoft's private signing keys
- Our test signature uses the correct format but incorrect values
- The receiving server should detect this DKIM validation failure

The DKIM header in this email follows the official format with:
- v=1 (version)
- a=rsa-sha256 (algorithm)
- d=microsoft.com (domain)
- s=s1024-meo (selector)
- c=relaxed/relaxed (canonicalization)
- h=from:subject:date... (headers included in signature)
- bh=... (body hash)
- b=... (signature value)
""",
            'body_type': 'plain',
            'custom_headers': {
                # The main DKIM header - formatted exactly like a real one
                'DKIM-Signature': dkim_signature
            }
        }
        
        return email_data
    
    def create_dmarc_test_email(self, recipient):
        """Create an email specifically to test DMARC validation
        
        Args:
            recipient (str): Recipient email address
            
        Returns:
            dict: Email data with sender, subject, body for DMARC testing
        """
        # Use a sender domain that's known to enforce DMARC
        email_data = {
            'sender': 'dmarc-test@paypal.com',
            'recipients': [recipient],
            'subject': 'DMARC Policy Test Email',
            'body': """This is a test email specifically for checking DMARC validation.
            
The From: address claims to be from paypal.com, but this email was not sent from PayPal's servers.
This should cause DMARC (Domain-based Message Authentication, Reporting & Conformance) to fail because:

1. PayPal has a strict DMARC policy published in DNS (p=reject)
2. Both SPF and DKIM will fail for this message:
   - SPF fails because this server is not authorized to send from paypal.com
   - DKIM fails because we don't have PayPal's private signing keys
3. The email should be marked as failing DMARC or potentially be rejected entirely

This test is helpful for confirming that DMARC protection is working properly.
""",
            'body_type': 'plain',
            'custom_headers': {
                'X-SMTP-Test': 'DMARC-Test',
                'X-DMARC-Test': 'This email should fail DMARC validation'
            }
        }
        
        return email_data
    
    def create_spf_dkim_dmarc_test_email(self, recipient):
        """Create an email to test SPF, DKIM, and DMARC validation
        
        Args:
            recipient (str): Recipient email address
            
        Returns:
            dict: Email data with sender, subject, body, and headers
        """
        # Use a sender domain that's likely to have strict SPF/DKIM/DMARC
        email_data = {
            'sender': 'security-test@microsoft.com',  # Spoofed sender from a major domain
            'recipients': [recipient],
            'subject': 'Combined SPF, DKIM, and DMARC Test Email',
            'body': """This is a comprehensive test email to check all three email authentication mechanisms:
SPF, DKIM, and DMARC together.
            
The From: address claims to be from microsoft.com, but this email was not sent from Microsoft's servers.

This should trigger failures in all three authentication methods:
1. SPF will fail because this server is not authorized to send from microsoft.com
2. DKIM will fail because we don't have Microsoft's private signing keys
3. DMARC will fail because both SPF and DKIM failed

Microsoft has strict email security policies, so this message would likely be rejected
or marked as suspicious by most mail servers.

This is purely for testing email authentication mechanisms.
""",
            'body_type': 'plain',
            'custom_headers': {
                'X-SMTP-Test': 'SPF-DKIM-DMARC-Test',
                'X-SPF-Test': 'This email should fail SPF validation',
                'X-DKIM-Test': 'This email should fail DKIM validation',
                'X-DMARC-Test': 'This email should fail DMARC validation',
                # Add realistic DKIM header
                'DKIM-Signature': """v=1; a=rsa-sha256; d=microsoft.com; s=s1024-meo;
        c=relaxed/relaxed; i=microsoft-noreply@microsoft.com; t=1744862738;
        h=from:subject:date:message-id:to:mime-version:content-type;
        bh=kMCKLEOZ9L1w0K1Y6XD/NwCjDt7lpmucjVRJ5RuL1fc=;
        b=Wm4raY1GPLYmqznZSNo0idkaM4Ua3ar5e5gqHSxkKFuGeNmGryeg+0zkoNpRsOCOGNvUGG547NF
        9c9xKAGnugj7XfnNvNpEhM3jU9KVbDyAIN2ai230UKwSA3EQ+7e4bjvipvwGx/NGXBjyqR0b/erke
        Jf9tSX6qAo+2FuurR8E="""
            }
        }
        
        return email_data
