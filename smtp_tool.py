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
        
        # Create a log capture function with better formatting
        def log_smtp(smtp_instance, prefix=""):
            original_debug = smtp_instance._print_debug
            
            def custom_debug(self, *args):
                message = " ".join(str(a) for a in args)
                # Clean up the message for better readability
                if message.startswith("send: b'") and message.endswith("'"):
                    # Extract content between b' and '
                    content = message[8:-1]
                    # Decode escape sequences for better readability
                    content = content.replace('\\r\\n', '\n').replace('\\n', '\n')
                    message = f"send: {content}"
                elif message.startswith("reply: b'") and message.endswith("'"):
                    # Extract content between b' and '
                    content = message[9:-1]
                    # Decode escape sequences
                    content = content.replace('\\r\\n', '\n').replace('\\n', '\n')
                    message = f"reply: {content}"
                elif message.startswith("data: b'") and message.endswith("'"):
                    # Extract content between b' and '
                    content = message[8:-1]
                    content = content.replace('\\r\\n', '\n').replace('\\n', '\n')
                    message = f"data: {content}"
                
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
            
            # Process custom headers
            
            # Add all custom headers to the message
            for header_name, header_value in custom_headers.items():
                try:
                    msg[header_name] = header_value
                    logging.info(f"Added custom header: {header_name}")
                except Exception as e:
                    logging.warning(f"Failed to add custom header {header_name}: {e}")
            
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
        
        # Create a log capture function with better formatting
        def log_smtp(smtp_instance, prefix=""):
            original_debug = smtp_instance._print_debug
            
            def custom_debug(self, *args):
                message = " ".join(str(a) for a in args)
                # Clean up the message for better readability
                if message.startswith("send: b'") and message.endswith("'"):
                    # Extract content between b' and '
                    content = message[8:-1]
                    # Decode escape sequences for better readability
                    content = content.replace('\\r\\n', '\n').replace('\\n', '\n')
                    message = f"send: {content}"
                elif message.startswith("reply: b'") and message.endswith("'"):
                    # Extract content between b' and '
                    content = message[9:-1]
                    # Decode escape sequences
                    content = content.replace('\\r\\n', '\n').replace('\\n', '\n')
                    message = f"reply: {content}"
                elif message.startswith("data: b'") and message.endswith("'"):
                    # Extract content between b' and '
                    content = message[8:-1]
                    content = content.replace('\\r\\n', '\n').replace('\\n', '\n')
                    message = f"data: {content}"
                
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
    
    # Removed Word and Excel attachment creation functions
        
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
        

    
    # Removed functions: create_dkim_test_email, create_dmarc_test_email, create_spf_dkim_dmarc_test_email
  