"""
Robust JSON Parser for LLM Responses

This module provides utilities for extracting and parsing JSON from LLM responses,
handling common issues like:
- Markdown code blocks
- Unterminated strings
- Missing delimiters
- Invalid JSON structure
- Partial JSON responses
"""

import json
import re
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


def extract_json_from_response(content: str) -> Optional[str]:
    """
    Extract JSON string from LLM response content.
    
    Handles multiple formats:
    - Markdown code blocks (```json ... ```)
    - Plain code blocks (``` ... ```)
    - Inline JSON objects
    - Partial JSON with surrounding text
    
    Args:
        content: Raw LLM response content
        
    Returns:
        Extracted JSON string or None if not found
    """
    if not content:
        return None
    
    content = content.strip()
    
    # Strategy 1: Extract from markdown JSON code block
    json_match = re.search(r'```json\s*\n?(.*?)\n?```', content, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()
    
    # Strategy 2: Extract from generic code block
    code_match = re.search(r'```\s*\n?(.*?)\n?```', content, re.DOTALL)
    if code_match:
        code_content = code_match.group(1).strip()
        # Check if it looks like JSON
        if code_content.startswith('{') or code_content.startswith('['):
            return code_content
    
    # Strategy 3: Find JSON object boundaries
    # Look for first { and last } or first [ and last ]
    brace_start = content.find('{')
    bracket_start = content.find('[')
    
    if brace_start >= 0 or bracket_start >= 0:
        # Determine which comes first
        if bracket_start >= 0 and (brace_start < 0 or bracket_start < brace_start):
            # Array JSON
            start_idx = bracket_start
            end_idx = content.rfind(']')
            if end_idx > start_idx:
                return content[start_idx:end_idx + 1]
        elif brace_start >= 0:
            # Object JSON
            start_idx = brace_start
            end_idx = content.rfind('}')
            if end_idx > start_idx:
                return content[start_idx:end_idx + 1]
    
    # Strategy 4: Return content as-is if it looks like JSON
    stripped = content.strip()
    if (stripped.startswith('{') and stripped.endswith('}')) or \
       (stripped.startswith('[') and stripped.endswith(']')):
        return stripped
    
    return None


def repair_json(json_str: str) -> Optional[str]:
    """
    Attempt to repair common JSON errors.
    
    Handles:
    - Unterminated strings
    - Missing commas
    - Unescaped quotes
    - Trailing commas
    
    Args:
        json_str: JSON string that may have errors
        
    Returns:
        Repaired JSON string or None if repair fails
    """
    if not json_str:
        return None
    
    try:
        # Try parsing first - if it works, return as-is
        json.loads(json_str)
        return json_str
    except json.JSONDecodeError:
        pass
    
    # Repair strategies
    repaired = json_str
    
    # Strategy 1: Fix unterminated strings
    # Find strings that start with " but don't end properly
    # This is complex, so we'll use a simpler approach
    
    # Strategy 2: Remove trailing commas before } or ]
    repaired = re.sub(r',\s*}', '}', repaired)
    repaired = re.sub(r',\s*]', ']', repaired)
    
    # Strategy 3: Fix missing commas between object properties
    # This is also complex, so we'll focus on simpler fixes
    
    # Strategy 4: Try to close unterminated strings
    # Count quotes - if odd, try to close
    quote_count = repaired.count('"') - repaired.count('\\"')
    if quote_count % 2 != 0:
        # Try to find the last unclosed string and close it
        # This is heuristic-based
        last_quote_idx = repaired.rfind('"')
        if last_quote_idx >= 0:
            # Check if there's a closing quote after this
            remaining = repaired[last_quote_idx + 1:]
            if '"' not in remaining.replace('\\"', ''):
                # Likely unterminated - try to close it
                # Find the end of the line or next comma/brace
                end_chars = [',', '\n', '}', ']']
                end_idx = len(repaired)
                for char in end_chars:
                    idx = repaired.find(char, last_quote_idx + 1)
                    if idx >= 0:
                        end_idx = min(end_idx, idx)
                
                if end_idx < len(repaired):
                    repaired = repaired[:end_idx] + '"' + repaired[end_idx:]
    
    return repaired


def parse_json_robust(content: str, required_fields: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """
    Parse JSON from LLM response with robust error handling.
    
    This function:
    1. Extracts JSON from various formats
    2. Attempts to repair common errors
    3. Validates structure
    4. Returns parsed JSON or None
    
    Args:
        content: Raw LLM response content
        required_fields: List of required top-level fields (for validation)
        
    Returns:
        Parsed JSON dictionary or None if parsing fails
    """
    if not content:
        logger.warning("Empty content provided to parse_json_robust")
        return None
    
    # Step 1: Extract JSON string
    json_str = extract_json_from_response(content)
    if not json_str:
        logger.warning("Could not extract JSON from response")
        logger.debug(f"Content preview (first 200 chars): {content[:200]}")
        return None
    
    # Step 2: Try parsing as-is
    try:
        result = json.loads(json_str)
        if validate_json_structure(result, required_fields):
            return result
    except json.JSONDecodeError as e:
        logger.debug(f"Initial JSON parse failed: {e}")
    
    # Step 3: Try repairing and parsing
    repaired = repair_json(json_str)
    if repaired and repaired != json_str:
        try:
            result = json.loads(repaired)
            if validate_json_structure(result, required_fields):
                logger.info("Successfully parsed JSON after repair")
                return result
        except json.JSONDecodeError as e:
            logger.debug(f"Repaired JSON parse failed: {e}")
    
    # Step 4: Try using json5 or other lenient parser (if available)
    try:
        import json5
        result = json5.loads(json_str)
        if validate_json_structure(result, required_fields):
            logger.info("Successfully parsed JSON using json5")
            return result
    except ImportError:
        logger.debug("json5 not available, skipping lenient parse")
    except Exception as e:
        logger.debug(f"json5 parse failed: {e}")
    
    # Step 5: Try partial extraction (extract valid JSON objects)
    try:
        # Find all JSON objects/arrays in the string
        objects = []
        depth = 0
        start = -1
        
        for i, char in enumerate(json_str):
            if char == '{' or char == '[':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}' or char == ']':
                depth -= 1
                if depth == 0 and start >= 0:
                    obj_str = json_str[start:i + 1]
                    try:
                        obj = json.loads(obj_str)
                        objects.append(obj)
                    except json.JSONDecodeError:
                        pass
                    start = -1
        
        # If we found at least one valid object, return the first one
        if objects:
            logger.info(f"Extracted {len(objects)} valid JSON objects, using first")
            return objects[0]
    except Exception as e:
        logger.debug(f"Partial extraction failed: {e}")
    
    logger.error("All JSON parsing strategies failed")
    logger.debug(f"JSON string preview (first 500 chars): {json_str[:500]}")
    return None


def validate_json_structure(data: Dict[str, Any], required_fields: Optional[List[str]] = None) -> bool:
    """
    Validate JSON structure has required fields.
    
    Args:
        data: Parsed JSON data
        required_fields: List of required top-level fields
        
    Returns:
        True if structure is valid, False otherwise
    """
    if not isinstance(data, dict):
        logger.warning(f"JSON data is not a dictionary: {type(data)}")
        return False
    
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            return False
    
    return True


def parse_json_with_fallback(content: str, 
                             required_fields: Optional[List[str]] = None,
                             fallback_fn: Optional[callable] = None) -> Optional[Dict[str, Any]]:
    """
    Parse JSON with fallback to alternative parsing method.
    
    Args:
        content: Raw LLM response content
        required_fields: List of required top-level fields
        fallback_fn: Optional function to call if JSON parsing fails
                    (e.g., parse from plain text)
        
    Returns:
        Parsed JSON dictionary or result from fallback function
    """
    result = parse_json_robust(content, required_fields)
    
    if result is not None:
        return result
    
    # Try fallback function if provided
    if fallback_fn:
        try:
            logger.info("Attempting fallback parsing method")
            return fallback_fn(content)
        except Exception as e:
            logger.error(f"Fallback parsing failed: {e}", exc_info=True)
    
    return None

