"""
Name Sanitization Utilities
Converts user objectives/descriptions into valid Python identifiers
"""

import re
from typing import Optional


def sanitize_for_filename(text: str, max_length: int = 50) -> str:
    """
    Sanitize text to create valid filename.
    
    Args:
        text: Raw text (e.g., "Support Customers, Invoices, Payments")
        max_length: Maximum filename length
        
    Returns:
        Valid filename (e.g., "support_customers_invoices_payments")
    
    Examples:
        >>> sanitize_for_filename("Support Customers, Invoices, Payments")
        'support_customers_invoices_payments'
        >>> sanitize_for_filename("API Integration - OAuth 2.0")
        'api_integration_oauth_2_0'
    """
    if not text:
        return "unnamed"
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove possessives and common words that add noise
    text = text.replace("'s", "")
    
    # Replace punctuation and special chars with spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Split into words and filter out common filler words
    filler_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'from'}
    words = [w for w in text.split() if w and w not in filler_words]
    
    # Join with underscores
    sanitized = '_'.join(words)
    
    # Ensure it doesn't start with a number
    if sanitized and sanitized[0].isdigit():
        sanitized = 'module_' + sanitized
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('_')
    
    # Ensure not empty
    if not sanitized:
        sanitized = "unnamed"
    
    return sanitized


def sanitize_for_class_name(text: str, max_length: int = 80) -> str:
    """
    Sanitize text to create valid Python class name (PascalCase).
    
    Args:
        text: Raw text (e.g., "Support Customers, Invoices, Payments")
        max_length: Maximum class name length
        
    Returns:
        Valid class name (e.g., "SupportCustomersInvoicesPayments")
    
    Examples:
        >>> sanitize_for_class_name("Support Customers, Invoices, Payments")
        'SupportCustomersInvoicesPayments'
        >>> sanitize_for_class_name("API Integration - OAuth 2.0")
        'ApiIntegrationOauth20'
    """
    if not text:
        return "UnnamedClass"
    
    # Remove possessives
    text = text.replace("'s", "")
    
    # Replace punctuation and special chars with spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Split into words and filter out filler words
    filler_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'from'}
    words = [w for w in text.split() if w and w not in filler_words]
    
    # Capitalize each word (PascalCase)
    class_name = ''.join(word.capitalize() for word in words)
    
    # Ensure it starts with a letter
    if class_name and class_name[0].isdigit():
        class_name = 'Module' + class_name
    
    # Truncate if too long
    if len(class_name) > max_length:
        class_name = class_name[:max_length]
    
    # Ensure not empty
    if not class_name:
        class_name = "UnnamedClass"
    
    return class_name


def sanitize_for_variable_name(text: str, max_length: int = 40) -> str:
    """
    Sanitize text to create valid Python variable name (snake_case).
    
    Args:
        text: Raw text
        max_length: Maximum variable name length
        
    Returns:
        Valid variable name
    
    Examples:
        >>> sanitize_for_variable_name("Customer ID")
        'customer_id'
        >>> sanitize_for_variable_name("Payment Method - Credit Card")
        'payment_method_credit_card'
    """
    # Reuse filename sanitization (same rules)
    return sanitize_for_filename(text, max_length)


def sanitize_for_function_name(text: str, max_length: int = 50) -> str:
    """
    Sanitize text to create valid Python function name (snake_case).
    
    Args:
        text: Raw text
        max_length: Maximum function name length
        
    Returns:
        Valid function name
    
    Examples:
        >>> sanitize_for_function_name("Get Customer Details")
        'get_customer_details'
    """
    # Reuse filename sanitization
    return sanitize_for_filename(text, max_length)


def sanitize_objective(objective: str) -> Dict[str, str]:
    """
    Sanitize objective text for all naming purposes.
    
    Args:
        objective: Raw objective text
        
    Returns:
        Dictionary with sanitized names for different purposes
    
    Example:
        >>> sanitize_objective("Support Customers, Invoices, Payments")
        {
            'filename': 'support_customers_invoices_payments',
            'class_name': 'SupportCustomersInvoicesPayments',
            'variable_name': 'support_customers_invoices_payments',
            'function_name': 'support_customers_invoices_payments',
            'display_name': 'Support Customers Invoices Payments'
        }
    """
    return {
        'filename': sanitize_for_filename(objective),
        'class_name': sanitize_for_class_name(objective),
        'variable_name': sanitize_for_variable_name(objective),
        'function_name': sanitize_for_function_name(objective),
        'display_name': re.sub(r'[^\w\s]', ' ', objective).strip(),
        'original': objective
    }

