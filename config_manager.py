import json
import os
import logging
import socket
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigManager:
    """Class for managing configuration settings, profiles, templates, and logs"""
    
    def __init__(self, config_dir=None):
        """
        Initialize the ConfigManager
        
        Args:
            config_dir (str, optional): Directory to store configuration files
        """
        if config_dir is None:
            # Use ~/.smtp_tool as the default config directory
            home_dir = os.path.expanduser("~")
            self.config_dir = os.path.join(home_dir, ".smtp_tool")
        else:
            self.config_dir = config_dir
        
        # Create config directory if it doesn't exist
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # Define paths for configuration files
        self.profiles_file = os.path.join(self.config_dir, "profiles.json")
        self.templates_file = os.path.join(self.config_dir, "templates.json")
        self.logs_file = os.path.join(self.config_dir, "logs.json")
        self.settings_file = os.path.join(self.config_dir, "settings.json")
        
        # Initialize configuration files if they don't exist
        self._initialize_config_files()
    
    def _initialize_config_files(self):
        """Initialize configuration files if they don't exist"""
        # Initialize profiles file
        if not os.path.exists(self.profiles_file):
            with open(self.profiles_file, 'w') as f:
                json.dump({}, f)
        
        # Initialize templates file
        if not os.path.exists(self.templates_file):
            with open(self.templates_file, 'w') as f:
                json.dump({}, f)
        
        # Initialize logs file
        if not os.path.exists(self.logs_file):
            with open(self.logs_file, 'w') as f:
                json.dump([], f)
        
        # Initialize settings file with default settings
        if not os.path.exists(self.settings_file):
            default_settings = {
                "send_hostname": socket.gethostname(),
                "default_sender": f"smtp@{socket.getfqdn()}",
                "saved_senders": [f"smtp@{socket.getfqdn()}", "test@example.com"],
                "saved_recipients": ["recipient@example.com"],
                "log_level": "INFO",
                "log_retention_days": 30,
                "log_smtp_traffic": True,
                "log_message_content": False,
                "max_attachment_size_mb": 10
            }
            with open(self.settings_file, 'w') as f:
                json.dump(default_settings, f, indent=2)
    
    def get_profiles(self):
        """
        Get all saved SMTP profiles
        
        Returns:
            dict: Dictionary of profiles
        """
        try:
            with open(self.profiles_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read profiles: {str(e)}")
            return {}
    
    def get_profile(self, name):
        """
        Get a specific SMTP profile by name
        
        Args:
            name (str): Name of the profile to retrieve
            
        Returns:
            dict: Profile data or None if not found
        """
        profiles = self.get_profiles()
        return profiles.get(name)
    
    def add_profile(self, profile_data):
        """
        Add or update an SMTP profile
        
        Args:
            profile_data (dict): Profile data to add
        """
        try:
            profiles = self.get_profiles()
            profiles[profile_data['name']] = {
                'server': profile_data['server'],
                'port': profile_data['port'],
                'use_tls': profile_data['use_tls'],
                'use_ssl': profile_data['use_ssl'],
                'username': profile_data['username'],
                'password': profile_data['password']
            }
            
            with open(self.profiles_file, 'w') as f:
                json.dump(profiles, f, indent=2)
                
            logger.info(f"Profile '{profile_data['name']}' saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save profile: {str(e)}")
            return False
    
    def delete_profile(self, name):
        """
        Delete an SMTP profile
        
        Args:
            name (str): Name of the profile to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            profiles = self.get_profiles()
            if name in profiles:
                del profiles[name]
                
                with open(self.profiles_file, 'w') as f:
                    json.dump(profiles, f, indent=2)
                
                logger.info(f"Profile '{name}' deleted successfully")
                return True
            else:
                logger.warning(f"Profile '{name}' not found")
                return False
        except Exception as e:
            logger.error(f"Failed to delete profile: {str(e)}")
            return False
    
    def get_templates(self):
        """
        Get all saved email templates
        
        Returns:
            dict: Dictionary of templates
        """
        try:
            with open(self.templates_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read templates: {str(e)}")
            return {}
    
    def get_template(self, name):
        """
        Get a specific email template by name
        
        Args:
            name (str): Name of the template to retrieve
            
        Returns:
            dict: Template data or None if not found
        """
        templates = self.get_templates()
        return templates.get(name)
    
    def add_template(self, template_data):
        """
        Add or update an email template
        
        Args:
            template_data (dict): Template data to add
        """
        try:
            templates = self.get_templates()
            templates[template_data['name']] = {
                'subject': template_data.get('subject', ''),
                'body_type': template_data.get('body_type', 'plain'),
                'body': template_data.get('body', '')
            }
            
            with open(self.templates_file, 'w') as f:
                json.dump(templates, f, indent=2)
                
            logger.info(f"Template '{template_data['name']}' saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save template: {str(e)}")
            return False
    
    def delete_template(self, name):
        """
        Delete an email template
        
        Args:
            name (str): Name of the template to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            templates = self.get_templates()
            if name in templates:
                del templates[name]
                
                with open(self.templates_file, 'w') as f:
                    json.dump(templates, f, indent=2)
                
                logger.info(f"Template '{name}' deleted successfully")
                return True
            else:
                logger.warning(f"Template '{name}' not found")
                return False
        except Exception as e:
            logger.error(f"Failed to delete template: {str(e)}")
            return False
    
    def get_logs(self):
        """
        Get all saved email sending logs
        
        Returns:
            list: List of log entries
        """
        try:
            with open(self.logs_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read logs: {str(e)}")
            return []
    
    def add_log_entry(self, log_entry):
        """
        Add a log entry for email sending
        
        Args:
            log_entry (dict): Log entry data to add
        """
        try:
            logs = self.get_logs()
            
            # Add timestamp if not provided
            if not log_entry.get('timestamp'):
                log_entry['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            logs.append(log_entry)
            
            # Limit to 1000 log entries to prevent file from growing too large
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            with open(self.logs_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
            logger.debug("Log entry added successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to add log entry: {str(e)}")
            return False
    
    def clear_logs(self):
        """
        Clear all email sending logs
        
        Returns:
            bool: True if cleared successfully
        """
        try:
            with open(self.logs_file, 'w') as f:
                json.dump([], f)
                
            logger.info("Logs cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to clear logs: {str(e)}")
            return False
    
    def get_settings(self):
        """
        Get application settings
        
        Returns:
            dict: Dictionary of settings
        """
        try:
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read settings: {str(e)}")
            # Return default settings if file cannot be read
            default_settings = {
                "send_hostname": socket.gethostname(),
                "default_sender": f"smtp@{socket.getfqdn()}",
                "saved_senders": [f"smtp@{socket.getfqdn()}", "test@example.com"],
                "saved_recipients": ["recipient@example.com"],
                "log_level": "INFO",
                "log_retention_days": 30,
                "log_smtp_traffic": True,
                "log_message_content": False,
                "max_attachment_size_mb": 10
            }
            return default_settings
    
    def update_settings(self, settings_data):
        """
        Update application settings
        
        Args:
            settings_data (dict): Settings data to update
            
        Returns:
            bool: True if updated successfully
        """
        try:
            # Get current settings
            current_settings = self.get_settings()
            
            # Update settings with new values
            for key, value in settings_data.items():
                current_settings[key] = value
                
            # Save updated settings
            with open(self.settings_file, 'w') as f:
                json.dump(current_settings, f, indent=2)
                
            logger.info("Settings updated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to update settings: {str(e)}")
            return False
            
    def add_saved_sender(self, email):
        """
        Add a saved sender email address
        
        Args:
            email (str): Email address to save
            
        Returns:
            bool: True if successful
        """
        try:
            # Get current settings
            current_settings = self.get_settings()
            
            # Make sure saved_senders exists
            if 'saved_senders' not in current_settings:
                current_settings['saved_senders'] = []
                
            # Add email if not already in the list
            if email not in current_settings['saved_senders']:
                current_settings['saved_senders'].append(email)
                
            # Write settings to file
            with open(self.settings_file, 'w') as f:
                json.dump(current_settings, f, indent=2)
                
            return True
        except Exception as e:
            logger.error(f"Failed to add saved sender: {str(e)}")
            return False
            
    def remove_saved_sender(self, email):
        """
        Remove a saved sender email address
        
        Args:
            email (str): Email address to remove
            
        Returns:
            bool: True if successful
        """
        try:
            # Get current settings
            current_settings = self.get_settings()
            
            # Make sure saved_senders exists
            if 'saved_senders' not in current_settings:
                logger.warning(f"Cannot remove sender {email}: No saved_senders in settings")
                return False
                
            # Debug log for visibility
            logger.info(f"Attempting to remove sender {email} from list: {current_settings['saved_senders']}")
                
            # Remove email if in list
            if email in current_settings['saved_senders']:
                current_settings['saved_senders'].remove(email)
                logger.info(f"Removed {email} from saved_senders, new list: {current_settings['saved_senders']}")
                
                # Write settings to file
                with open(self.settings_file, 'w') as f:
                    json.dump(current_settings, f, indent=2)
                    
                logger.info(f"Successfully saved updated settings after removing {email}")
                return True
            else:
                logger.warning(f"Cannot remove sender {email}: Not found in saved_senders list")
                return False
        except Exception as e:
            logger.error(f"Failed to remove saved sender {email}: {str(e)}")
            return False
            
    def add_saved_recipient(self, email):
        """
        Add a saved recipient email address
        
        Args:
            email (str): Email address to save
            
        Returns:
            bool: True if successful
        """
        try:
            # Get current settings
            current_settings = self.get_settings()
            
            # Make sure saved_recipients exists
            if 'saved_recipients' not in current_settings:
                current_settings['saved_recipients'] = []
                
            # Add email if not already in the list
            if email not in current_settings['saved_recipients']:
                current_settings['saved_recipients'].append(email)
                
            # Write settings to file
            with open(self.settings_file, 'w') as f:
                json.dump(current_settings, f, indent=2)
                
            return True
        except Exception as e:
            logger.error(f"Failed to add saved recipient: {str(e)}")
            return False
            
    def remove_saved_recipient(self, email):
        """
        Remove a saved recipient email address
        
        Args:
            email (str): Email address to remove
            
        Returns:
            bool: True if successful
        """
        try:
            # Get current settings
            current_settings = self.get_settings()
            
            # Make sure saved_recipients exists
            if 'saved_recipients' not in current_settings:
                logger.warning(f"Cannot remove recipient {email}: No saved_recipients in settings")
                return False
                
            # Debug log for visibility
            logger.info(f"Attempting to remove recipient {email} from list: {current_settings['saved_recipients']}")
                
            # Remove email if in list
            if email in current_settings['saved_recipients']:
                current_settings['saved_recipients'].remove(email)
                logger.info(f"Removed {email} from saved_recipients, new list: {current_settings['saved_recipients']}")
                
                # Write settings to file
                with open(self.settings_file, 'w') as f:
                    json.dump(current_settings, f, indent=2)
                    
                logger.info(f"Successfully saved updated settings after removing {email}")
                return True
            else:
                logger.warning(f"Cannot remove recipient {email}: Not found in saved_recipients list")
                return False
        except Exception as e:
            logger.error(f"Failed to remove saved recipient {email}: {str(e)}")
            return False
            
    def get_detailed_logs(self, limit=None, search_text=None):
        """
        Get logs with filtering and advanced options
        
        Args:
            limit (int, optional): Maximum number of logs to return
            search_text (str, optional): Text to search for in logs
            
        Returns:
            list: Filtered list of log entries
        """
        try:
            logs = self.get_logs()
            
            # Filter by search text if provided
            if search_text:
                filtered_logs = []
                for log in logs:
                    # Search in multiple fields
                    searchable_text = " ".join([
                        str(log.get("profile", "")),
                        str(log.get("sender", "")),
                        " ".join(log.get("recipients", [])),
                        str(log.get("subject", "")),
                        str(log.get("status", "")),
                        str(log.get("error", ""))
                    ]).lower()
                    
                    if search_text.lower() in searchable_text:
                        filtered_logs.append(log)
                logs = filtered_logs
            
            # Sort logs by timestamp (newest first)
            logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Limit the number of logs if requested
            if limit and isinstance(limit, int) and limit > 0:
                logs = logs[:limit]
                
            return logs
        except Exception as e:
            logger.error(f"Failed to get detailed logs: {str(e)}")
            return []
