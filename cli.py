#!/usr/bin/env python3
import argparse
import sys
import os
import logging
from smtp_tool import SMTPTool
from config_manager import ConfigManager
from email_validator import validate_email

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("smtp_tool_cli.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function for the CLI interface"""
    parser = argparse.ArgumentParser(
        description='SMTP Testing and Email Sending Tool',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Send email command
    send_parser = subparsers.add_parser('send', help='Send an email')
    send_parser.add_argument('--profile', '-p', required=False, help='Profile name to use for sending')
    send_parser.add_argument('--server', '-s', required=False, help='SMTP server address')
    send_parser.add_argument('--port', '-P', type=int, default=25, help='SMTP server port (default: 25)')
    send_parser.add_argument('--tls', '-t', action='store_true', help='Use STARTTLS')
    send_parser.add_argument('--ssl', '-S', action='store_true', help='Use SSL/TLS')
    send_parser.add_argument('--username', '-u', help='SMTP username')
    send_parser.add_argument('--password', '-w', help='SMTP password')
    send_parser.add_argument('--from', '-f', dest='sender', required=True, help='Sender email address')
    send_parser.add_argument('--to', '-r', dest='recipients', required=True, 
                           help='Recipient email addresses (comma-separated)')
    send_parser.add_argument('--cc', '-c', help='CC email addresses (comma-separated)')
    send_parser.add_argument('--bcc', '-b', help='BCC email addresses (comma-separated)')
    send_parser.add_argument('--subject', '-j', default='', help='Email subject')
    send_parser.add_argument('--body', '-m', help='Email body text')
    send_parser.add_argument('--body-file', '-B', help='File containing email body')
    send_parser.add_argument('--html', '-H', action='store_true', help='Send as HTML email')
    send_parser.add_argument('--attachment', '-a', action='append', 
                           help='Email attachment file path (can be used multiple times)')
    send_parser.add_argument('--template', '-T', help='Use a saved email template')
    
    # Test connection command
    test_parser = subparsers.add_parser('test', help='Test SMTP server connection')
    test_parser.add_argument('--profile', '-p', required=False, help='Profile name to test')
    test_parser.add_argument('--server', '-s', required=False, help='SMTP server address')
    test_parser.add_argument('--port', '-P', type=int, default=25, help='SMTP server port (default: 25)')
    test_parser.add_argument('--tls', '-t', action='store_true', help='Use STARTTLS')
    test_parser.add_argument('--ssl', '-S', action='store_true', help='Use SSL/TLS')
    test_parser.add_argument('--username', '-u', help='SMTP username')
    test_parser.add_argument('--password', '-w', help='SMTP password')
    
    # Profile management commands
    profile_parser = subparsers.add_parser('profile', help='Manage SMTP profiles')
    profile_subparsers = profile_parser.add_subparsers(dest='profile_command', help='Profile command')
    
    # List profiles
    list_parser = profile_subparsers.add_parser('list', help='List saved profiles')
    
    # Add profile
    add_parser = profile_subparsers.add_parser('add', help='Add a new profile')
    add_parser.add_argument('--name', '-n', required=True, help='Profile name')
    add_parser.add_argument('--server', '-s', required=True, help='SMTP server address')
    add_parser.add_argument('--port', '-P', type=int, default=25, help='SMTP server port (default: 25)')
    add_parser.add_argument('--tls', '-t', action='store_true', help='Use STARTTLS')
    add_parser.add_argument('--ssl', '-S', action='store_true', help='Use SSL/TLS')
    add_parser.add_argument('--username', '-u', help='SMTP username')
    add_parser.add_argument('--password', '-w', help='SMTP password')
    
    # Delete profile
    delete_parser = profile_subparsers.add_parser('delete', help='Delete a profile')
    delete_parser.add_argument('name', help='Profile name to delete')
    
    # Template management commands
    template_parser = subparsers.add_parser('template', help='Manage email templates')
    template_subparsers = template_parser.add_subparsers(dest='template_command', help='Template command')
    
    # List templates
    list_template_parser = template_subparsers.add_parser('list', help='List saved templates')
    
    # Add template
    add_template_parser = template_subparsers.add_parser('add', help='Add a new template')
    add_template_parser.add_argument('--name', '-n', required=True, help='Template name')
    add_template_parser.add_argument('--subject', '-s', help='Email subject')
    add_template_parser.add_argument('--body', '-b', help='Email body text')
    add_template_parser.add_argument('--body-file', '-f', help='File containing email body')
    add_template_parser.add_argument('--html', '-H', action='store_true', help='Mark as HTML template')
    
    # Delete template
    delete_template_parser = template_subparsers.add_parser('delete', help='Delete a template')
    delete_template_parser.add_argument('name', help='Template name to delete')
    
    # Show template
    show_template_parser = template_subparsers.add_parser('show', help='Show a template')
    show_template_parser.add_argument('name', help='Template name to show')
    
    # Display logs command
    logs_parser = subparsers.add_parser('logs', help='Display email sending logs')
    logs_parser.add_argument('--clear', '-c', action='store_true', help='Clear logs')
    logs_parser.add_argument('--limit', '-l', type=int, default=20, help='Limit number of logs displayed')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize config manager
    config_manager = ConfigManager()
    
    # Initialize SMTP tool
    smtp_tool = SMTPTool()
    
    # No command specified, show help
    if not args.command:
        parser.print_help()
        return 1
    
    # Handle send command
    if args.command == 'send':
        # Get server details from profile or command line
        server = None
        port = None
        use_tls = None
        use_ssl = None
        username = None
        password = None
        
        if args.profile:
            profile = config_manager.get_profile(args.profile)
            if not profile:
                logger.error(f"Profile '{args.profile}' not found")
                return 1
            
            server = profile['server']
            port = profile['port']
            use_tls = profile['use_tls']
            use_ssl = profile['use_ssl']
            username = profile['username']
            password = profile['password']
        else:
            # Use command line arguments
            if not args.server:
                logger.error("Server address is required when not using a profile")
                return 1
            
            server = args.server
            port = args.port
            use_tls = args.tls
            use_ssl = args.ssl
            username = args.username
            password = args.password
        
        # Get email body
        body = ''
        body_type = 'html' if args.html else 'plain'
        
        if args.template:
            template = config_manager.get_template(args.template)
            if not template:
                logger.error(f"Template '{args.template}' not found")
                return 1
            
            if not args.subject:
                args.subject = template.get('subject', '')
            
            body = template.get('body', '')
            body_type = template.get('body_type', 'plain')
        
        if args.body:
            body = args.body
        
        if args.body_file:
            try:
                with open(args.body_file, 'r') as f:
                    body = f.read()
            except Exception as e:
                logger.error(f"Failed to read body file: {str(e)}")
                return 1
        
        # Parse recipients
        recipients = args.recipients.split(',')
        cc = args.cc.split(',') if args.cc else []
        bcc = args.bcc.split(',') if args.bcc else []
        
        # Validate email addresses
        all_recipients = recipients + cc + bcc
        for email in all_recipients + [args.sender]:
            if email.strip():
                try:
                    validate_email(email.strip())
                except Exception as e:
                    logger.error(f"Invalid email address '{email}': {str(e)}")
                    return 1
        
        # Send the email
        result = smtp_tool.send_email(
            server=server,
            port=port,
            use_tls=use_tls,
            use_ssl=use_ssl,
            username=username,
            password=password,
            sender=args.sender,
            recipients=recipients,
            cc=cc,
            bcc=bcc,
            subject=args.subject,
            body=body,
            body_type=body_type,
            attachments=args.attachment
        )
        
        if result['success']:
            logger.info("Email sent successfully")
            # Add to logs
            log_entry = {
                'timestamp': None,  # Will be added by ConfigManager
                'profile': args.profile if args.profile else 'CLI',
                'server': server,
                'sender': args.sender,
                'recipients': recipients,
                'cc': cc,
                'bcc': bcc,
                'subject': args.subject,
                'status': 'Success'
            }
            config_manager.add_log_entry(log_entry)
            return 0
        else:
            logger.error(f"Failed to send email: {result.get('error', 'Unknown error')}")
            # Add to logs
            log_entry = {
                'timestamp': None,  # Will be added by ConfigManager
                'profile': args.profile if args.profile else 'CLI',
                'server': server,
                'sender': args.sender,
                'recipients': recipients,
                'cc': cc,
                'bcc': bcc,
                'subject': args.subject,
                'status': 'Failed',
                'error': result.get('error', 'Unknown error')
            }
            config_manager.add_log_entry(log_entry)
            return 1
    
    # Handle test command
    elif args.command == 'test':
        # Get server details from profile or command line
        server = None
        port = None
        use_tls = None
        use_ssl = None
        username = None
        password = None
        
        if args.profile:
            profile = config_manager.get_profile(args.profile)
            if not profile:
                logger.error(f"Profile '{args.profile}' not found")
                return 1
            
            server = profile['server']
            port = profile['port']
            use_tls = profile['use_tls']
            use_ssl = profile['use_ssl']
            username = profile['username']
            password = profile['password']
        else:
            # Use command line arguments
            if not args.server:
                logger.error("Server address is required when not using a profile")
                return 1
            
            server = args.server
            port = args.port
            use_tls = args.tls
            use_ssl = args.ssl
            username = args.username
            password = args.password
        
        # Test the connection
        result = smtp_tool.test_connection(
            server=server,
            port=port,
            use_tls=use_tls,
            use_ssl=use_ssl,
            username=username,
            password=password
        )
        
        if result['success']:
            logger.info(f"Successfully connected to SMTP server {server}:{port}")
            if 'capabilities' in result:
                logger.info("Server capabilities:")
                for capability in result['capabilities']:
                    logger.info(f"- {capability}")
            return 0
        else:
            logger.error(f"Failed to connect to SMTP server: {result.get('error', 'Unknown error')}")
            return 1
    
    # Handle profile commands
    elif args.command == 'profile':
        if not args.profile_command:
            profile_parser.print_help()
            return 1
        
        # List profiles
        if args.profile_command == 'list':
            profiles = config_manager.get_profiles()
            if not profiles:
                logger.info("No profiles found")
            else:
                logger.info("Saved profiles:")
                for name, profile in profiles.items():
                    logger.info(f"- {name}:")
                    logger.info(f"  Server: {profile['server']}:{profile['port']}")
                    logger.info(f"  Security: {'SSL/TLS' if profile['use_ssl'] else 'STARTTLS' if profile['use_tls'] else 'None'}")
                    logger.info(f"  Authentication: {'Yes' if profile['username'] else 'No'}")
            return 0
        
        # Add profile
        elif args.profile_command == 'add':
            profile_data = {
                'name': args.name,
                'server': args.server,
                'port': args.port,
                'use_tls': args.tls,
                'use_ssl': args.ssl,
                'username': args.username,
                'password': args.password
            }
            
            config_manager.add_profile(profile_data)
            logger.info(f"Profile '{args.name}' added successfully")
            return 0
        
        # Delete profile
        elif args.profile_command == 'delete':
            if config_manager.delete_profile(args.name):
                logger.info(f"Profile '{args.name}' deleted successfully")
                return 0
            else:
                logger.error(f"Profile '{args.name}' not found")
                return 1
    
    # Handle template commands
    elif args.command == 'template':
        if not args.template_command:
            template_parser.print_help()
            return 1
        
        # List templates
        if args.template_command == 'list':
            templates = config_manager.get_templates()
            if not templates:
                logger.info("No templates found")
            else:
                logger.info("Saved templates:")
                for name, template in templates.items():
                    logger.info(f"- {name}:")
                    logger.info(f"  Subject: {template.get('subject', 'N/A')}")
                    logger.info(f"  Type: {'HTML' if template.get('body_type') == 'html' else 'Plain Text'}")
            return 0
        
        # Add template
        elif args.template_command == 'add':
            body = ''
            if args.body:
                body = args.body
            
            if args.body_file:
                try:
                    with open(args.body_file, 'r') as f:
                        body = f.read()
                except Exception as e:
                    logger.error(f"Failed to read body file: {str(e)}")
                    return 1
            
            template_data = {
                'name': args.name,
                'subject': args.subject or '',
                'body_type': 'html' if args.html else 'plain',
                'body': body
            }
            
            config_manager.add_template(template_data)
            logger.info(f"Template '{args.name}' added successfully")
            return 0
        
        # Delete template
        elif args.template_command == 'delete':
            if config_manager.delete_template(args.name):
                logger.info(f"Template '{args.name}' deleted successfully")
                return 0
            else:
                logger.error(f"Template '{args.name}' not found")
                return 1
        
        # Show template
        elif args.template_command == 'show':
            template = config_manager.get_template(args.name)
            if template:
                logger.info(f"Template: {args.name}")
                logger.info(f"Subject: {template.get('subject', 'N/A')}")
                logger.info(f"Type: {'HTML' if template.get('body_type') == 'html' else 'Plain Text'}")
                logger.info("Body:")
                logger.info(template.get('body', ''))
                return 0
            else:
                logger.error(f"Template '{args.name}' not found")
                return 1
    
    # Handle logs command
    elif args.command == 'logs':
        if args.clear:
            config_manager.clear_logs()
            logger.info("Logs cleared successfully")
            return 0
        
        logs = config_manager.get_logs()
        if not logs:
            logger.info("No logs found")
        else:
            logs = logs[-args.limit:] if len(logs) > args.limit else logs
            logger.info(f"Recent {len(logs)} log entries:")
            for log in logs:
                status_str = log.get('status', 'Unknown')
                if status_str == 'Success':
                    status_display = 'SUCCESS'
                else:
                    status_display = f"FAILED: {log.get('error', 'Unknown error')}"
                
                logger.info(f"[{log.get('timestamp', 'Unknown')}] {log.get('profile', 'N/A')} - {log.get('subject', 'N/A')} - {status_display}")
        return 0

if __name__ == "__main__":
    sys.exit(main())
