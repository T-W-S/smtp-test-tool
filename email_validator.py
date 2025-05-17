import re
import socket

def validate_email(email):
    """
    Validate an email address format
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if valid
        
    Raises:
        ValueError: If email is invalid with detailed reason
    """
    # Strip whitespace
    email = email.strip()
    
    # Check for empty string
    if not email:
        raise ValueError("Email address cannot be empty")
    
    # Check maximum length
    if len(email) > 254:
        raise ValueError("Email address is too long")
    
    # Basic pattern matching
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError("Email address format is invalid")
    
    # Split into local and domain parts
    try:
        local_part, domain = email.rsplit('@', 1)
    except ValueError:
        raise ValueError("Email address must contain exactly one @ symbol")
    
    # Check local part length
    if len(local_part) > 64:
        raise ValueError("Local part of email address is too long")
    
    # Check for consecutive dots
    if '..' in local_part or '..' in domain:
        raise ValueError("Email address cannot contain consecutive dots")
    
    # Check if domain has at least one dot
    if '.' not in domain:
        raise ValueError("Domain must contain at least one dot")
    
    # Optional: Check if domain exists (DNS check)
    # This is commented out to avoid network requests during validation
    # try:
    #     socket.gethostbyname(domain)
    # except socket.gaierror:
    #     raise ValueError(f"Domain {domain} does not exist")
    
    return True
