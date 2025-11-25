"""
Name Generator Utilities
Generates concise, descriptive names from objectives/descriptions.

This module provides intelligent name generation that creates short,
descriptive names rather than using the entire objective text.
"""

import re
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


def generate_concise_name(objective: str, agent_type: Optional[str] = None, max_length: int = 60) -> str:
    """
    Generate a concise, descriptive name from an objective.
    
    This function extracts key concepts from the objective and creates
    a short, descriptive name suitable for task titles, filenames, etc.
    
    Args:
        objective: The full objective/description text
        agent_type: Optional agent type (e.g., "CODER", "RESEARCHER") for context
        max_length: Maximum length of the generated name
        
    Returns:
        Concise name (e.g., "QuickBooks API Integration" instead of full sentence)
    
    Examples:
        >>> generate_concise_name("Do an initial check to the QuickBooks API using the keys provided")
        'QuickBooks API Check'
        >>> generate_concise_name("Create a NextJs interface to Perform these tasks")
        'NextJS Interface'
        >>> generate_concise_name("Connect the Backend and UI using an SQLite Database")
        'Backend-UI SQLite Connection'
    """
    if not objective:
        return "Unnamed Task"
    
    # Remove common prefixes/suffixes that add noise
    objective = objective.strip()
    
    # Remove common action prefixes
    prefixes_to_remove = [
        r'^(do|create|build|implement|develop|make|add|setup|configure|perform|execute|run)\s+',
        r'^(create a|build a|implement a|develop a|make a|add a|setup a|configure a)\s+',
        r'^(create an|build an|implement an|develop an|make an|add an|setup an|configure an)\s+',
    ]
    for pattern in prefixes_to_remove:
        objective = re.sub(pattern, '', objective, flags=re.IGNORECASE)
    
    # Extract key concepts (nouns, proper nouns, important verbs)
    # Strategy 1: Extract proper nouns (capitalized words) and key technologies
    words = objective.split()
    key_terms = []
    
    # Common technology/API names to preserve
    tech_keywords = {
        'quickbooks', 'qbo', 'odoo', 'stripe', 'oauth', 'api', 'rest', 'graphql',
        'nextjs', 'next.js', 'react', 'sqlite', 'postgresql', 'mysql', 'mongodb',
        'fastapi', 'django', 'flask', 'express', 'nodejs', 'python', 'typescript',
        'javascript', 'terraform', 'kubernetes', 'k8s', 'docker', 'azure', 'aws',
        'webhook', 'websocket', 'redis', 'celery', 'temporal'
    }
    
    # Extract important terms
    for word in words:
        word_lower = word.lower().rstrip('.,;:!?')
        
        # Preserve technology keywords
        if word_lower in tech_keywords:
            key_terms.append(word_lower.title() if word_lower.islower() else word)
        # Preserve proper nouns (capitalized words)
        elif word and word[0].isupper() and len(word) > 2:
            key_terms.append(word.rstrip('.,;:!?'))
        # Preserve important action verbs
        elif word_lower in ['connect', 'integrate', 'migrate', 'sync', 'validate', 'authenticate', 'authorize']:
            key_terms.append(word_lower.title())
    
    # Strategy 2: If we didn't find enough key terms, use first few meaningful words
    if len(key_terms) < 2:
        # Remove filler words and take first 3-4 meaningful words
        filler_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'from', 'using', 'by', 'via'}
        meaningful_words = [w.rstrip('.,;:!?') for w in words if w.lower() not in filler_words][:4]
        key_terms.extend(meaningful_words)
    
    # Strategy 3: Extract noun phrases (patterns like "API integration", "database connection")
    noun_phrases = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', objective)
    if noun_phrases:
        # Use the longest noun phrase as it's likely the main concept
        longest_phrase = max(noun_phrases, key=len)
        if len(longest_phrase.split()) <= 3:  # Only if reasonable length
            key_terms.insert(0, longest_phrase)
    
    # Build the concise name
    if key_terms:
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in key_terms:
            term_lower = term.lower()
            if term_lower not in seen:
                seen.add(term_lower)
                unique_terms.append(term)
        
        # Join terms
        concise_name = ' '.join(unique_terms[:5])  # Max 5 terms
        
        # Truncate if too long (at word boundary)
        if len(concise_name) > max_length:
            words = concise_name.split()
            truncated = []
            current_length = 0
            for word in words:
                if current_length + len(word) + 1 <= max_length:
                    truncated.append(word)
                    current_length += len(word) + 1
                else:
                    break
            concise_name = ' '.join(truncated) if truncated else concise_name[:max_length]
    else:
        # Fallback: use first few words of objective
        words = objective.split()[:4]
        concise_name = ' '.join(words)
        if len(concise_name) > max_length:
            concise_name = concise_name[:max_length].rsplit(' ', 1)[0]  # Truncate at word boundary
    
    # Clean up: remove trailing punctuation
    concise_name = concise_name.rstrip('.,;:!?')
    
    # Ensure not empty
    if not concise_name:
        concise_name = "Unnamed Task"
    
    return concise_name


def generate_task_title(objective: str, agent_type: str, max_length: int = 70) -> str:
    """
    Generate a concise task title from an objective and agent type.
    
    Args:
        objective: The full objective/description text
        agent_type: Agent type (e.g., "CODER", "RESEARCHER")
        max_length: Maximum length of the title
        
    Returns:
        Concise task title (e.g., "Backend: QuickBooks API Integration")
    
    Examples:
        >>> generate_task_title("Do an initial check to the QuickBooks API", "CODER")
        'Backend: QuickBooks API Check'
        >>> generate_task_title("Research Stripe payment integration", "RESEARCHER")
        'Research: Stripe Payment Integration'
    """
    # Generate concise name from objective
    concise_name = generate_concise_name(objective, agent_type, max_length=max_length - 15)  # Reserve space for prefix
    
    # Map agent types to display names
    agent_display_names = {
        'CODER': 'Backend',
        'RESEARCHER': 'Research',
        'FRONTEND': 'Frontend',
        'INTEGRATION': 'Integration',
        'INFRASTRUCTURE': 'Infrastructure',
        'WORKFLOW': 'Workflow',
        'TESTING': 'Test',
        'QA': 'QA Review',
        'SECURITY': 'Security Review'
    }
    
    prefix = agent_display_names.get(agent_type.upper(), agent_type.title())
    
    # Build title
    title = f"{prefix}: {concise_name}"
    
    # Ensure it doesn't exceed max_length
    if len(title) > max_length:
        # Truncate the concise name part
        prefix_len = len(prefix) + 2  # ": "
        max_concise = max_length - prefix_len
        concise_name = generate_concise_name(objective, agent_type, max_length=max_concise)
        title = f"{prefix}: {concise_name}"
    
    return title


def generate_component_name(objective: str, component_type: str = "component", max_length: int = 50) -> str:
    """
    Generate a concise name for code components (files, classes, etc.).
    
    Args:
        objective: The full objective/description text
        component_type: Type of component ("file", "class", "function", etc.)
        max_length: Maximum length of the name
        
    Returns:
        Concise component name suitable for filenames/identifiers
    
    Examples:
        >>> generate_component_name("Do an initial check to the QuickBooks API")
        'quickbooks_api_check'
        >>> generate_component_name("Connect the Backend and UI using SQLite")
        'backend_ui_sqlite'
    """
    # Generate concise name
    concise_name = generate_concise_name(objective, max_length=max_length)
    
    # Convert to appropriate format based on component type
    if component_type == "file" or component_type == "filename":
        # Convert to snake_case for filenames
        name = concise_name.lower()
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', '_', name)
        # Truncate if needed
        if len(name) > max_length:
            name = name[:max_length].rsplit('_', 1)[0]
        return name
    
    elif component_type == "class":
        # Convert to PascalCase for class names
        words = concise_name.split()
        name = ''.join(word.capitalize() for word in words)
        # Truncate if needed
        if len(name) > max_length:
            # Try to truncate at word boundary
            truncated = ''
            for word in words:
                if len(truncated) + len(word.capitalize()) <= max_length:
                    truncated += word.capitalize()
                else:
                    break
            name = truncated if truncated else name[:max_length]
        return name
    
    elif component_type == "function":
        # Convert to snake_case for function names
        name = concise_name.lower()
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', '_', name)
        if len(name) > max_length:
            name = name[:max_length].rsplit('_', 1)[0]
        return name
    
    else:
        # Default: return as-is
        return concise_name[:max_length]

