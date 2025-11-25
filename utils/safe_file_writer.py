"""
Safe File Writer - Hard Guarantee System

Prevents project-generated code from corrupting the platform's own code space.
All file writes by agents MUST go through this module.

CRITICAL RULES:
1. All project files MUST be written to Tenant_Projects/{project_id}/
2. NO files can be written outside the project workspace
3. Path traversal attacks are blocked
4. System folders are protected
"""

import os
import logging
from pathlib import Path
from typing import Optional, Union
from pathlib import PurePath

logger = logging.getLogger(__name__)

# System folders that MUST NEVER be written to by project code
PROTECTED_SYSTEM_FOLDERS = {
    'addon_portal',
    'agents',
    'api',  # Root-level api folder (system code)
    'config',  # Root-level config (system config)
    'docs',
    'demos',
    'infra',
    'k8s',
    'logs',
    'mobile',  # System mobile folder
    'research',  # Root-level research (system research)
    'shared',
    'src',  # Root-level src (system code)
    'templates',
    'tests',  # Root-level tests (system tests)
    'test_workspace',
    'tools',
    'utils',
    'web',
    'zbin',
    '.github',
    '.git',
    '__pycache__',
    'node_modules',
    'venv',
    '.venv',
}

# System files that MUST NEVER be overwritten
PROTECTED_SYSTEM_FILES = {
    'main.py',
    'README.md',
    'requirements.txt',
    'config_example.json',
    'config.json',
    'test_config.json',
    'test_agent_system.py',
    'test_agents.py',
    'test_database_connection.py',
    'test_duckduckgo_search.py',
    'test_python313_full_compatibility.py',
    'test_research_agent_llm.py',
    'test_researcher.json',
    'test_small.json',
    'test_task_tracking.py',
    'quick_test.py',
    'check_database_schema.py',
    'check_databases.py',
    'check_tenant_sessions_schema.py',
    'create_database.py',
    'fix_db_dsn.py',
    'update_db_dsn_to_q2o.py',
    'update_password_in_env.py',
    'env.example',
    'env.llm.example.txt',
    '.env',
    '.gitignore',
    'learned_templates.db',
    'q2o_licensing.db',
    '.llm_cost_state.json',
}


class WorkspaceSecurityError(Exception):
    """Raised when a file write violates workspace security rules."""
    pass


def validate_workspace_path(workspace_path: Union[str, Path], project_id: Optional[str] = None) -> Path:
    """
    Validate that workspace_path is within Tenant_Projects/{project_id}/.
    
    Args:
        workspace_path: The workspace path to validate
        project_id: Optional project ID for additional validation
        
    Returns:
        Resolved Path object
        
    Raises:
        WorkspaceSecurityError: If workspace_path is invalid or outside Tenant_Projects
    """
    workspace_path = Path(workspace_path).resolve()
    project_root = Path(__file__).resolve().parents[1]  # Q2O_Combined root
    
    # CRITICAL: Workspace MUST be within Tenant_Projects
    tenant_projects_root = project_root / "Tenant_Projects"
    
    try:
        # Check if workspace_path is within Tenant_Projects
        workspace_path.relative_to(tenant_projects_root)
    except ValueError:
        # workspace_path is NOT within Tenant_Projects
        raise WorkspaceSecurityError(
            f"CRITICAL SECURITY VIOLATION: workspace_path '{workspace_path}' is outside Tenant_Projects!\n"
            f"All project files MUST be written to Tenant_Projects/{{project_id}}/\n"
            f"Project root: {project_root}\n"
            f"Tenant_Projects root: {tenant_projects_root}"
        )
    
    # Additional validation: If project_id provided, verify workspace matches
    if project_id:
        expected_workspace = tenant_projects_root / project_id
        if workspace_path != expected_workspace:
            logger.warning(
                f"Workspace path '{workspace_path}' does not match expected project path '{expected_workspace}'. "
                f"Using provided workspace_path."
            )
    
    return workspace_path


def validate_file_path(file_path: Union[str, Path], workspace_path: Union[str, Path]) -> Path:
    """
    Validate that a file path is safe to write to.
    
    Args:
        file_path: The file path to validate (can be relative or absolute)
        workspace_path: The validated workspace path
        
    Returns:
        Resolved absolute Path object
        
    Raises:
        WorkspaceSecurityError: If file_path is invalid or outside workspace
    """
    workspace_path = Path(workspace_path).resolve()
    file_path = Path(file_path)
    
    # If file_path is absolute, it MUST be within workspace_path
    if file_path.is_absolute():
        try:
            file_path.relative_to(workspace_path)
        except ValueError:
            raise WorkspaceSecurityError(
                f"CRITICAL SECURITY VIOLATION: File path '{file_path}' is outside workspace '{workspace_path}'!\n"
                f"All project files MUST be written within the project workspace."
            )
        resolved_path = file_path
    else:
        # Relative path - resolve against workspace
        resolved_path = (workspace_path / file_path).resolve()
    
    # CRITICAL: Ensure resolved path is still within workspace (prevent path traversal)
    try:
        resolved_path.relative_to(workspace_path)
    except ValueError:
        raise WorkspaceSecurityError(
            f"CRITICAL SECURITY VIOLATION: Path traversal detected!\n"
            f"File path resolves to '{resolved_path}' which is outside workspace '{workspace_path}'.\n"
            f"Original path: {file_path}"
        )
    
    # Check if path tries to access protected system folders
    # Get relative path from project root
    project_root = Path(__file__).resolve().parents[1]
    try:
        rel_to_root = resolved_path.relative_to(project_root)
    except ValueError:
        # File is outside project root - this is OK if it's within workspace
        # But we should still check for protected names in the path
        pass
    else:
        # Check each component of the path
        path_parts = PurePath(rel_to_root).parts
        
        # Check if any part matches a protected folder name
        for part in path_parts:
            if part in PROTECTED_SYSTEM_FOLDERS:
                # Check if this is actually within the workspace (allowed) or root-level (blocked)
                if len(path_parts) > 1 and path_parts[0] == "Tenant_Projects":
                    # This is within Tenant_Projects, so it's OK (e.g., Tenant_Projects/proj/src/...)
                    continue
                else:
                    raise WorkspaceSecurityError(
                        f"CRITICAL SECURITY VIOLATION: Attempted to write to protected system folder '{part}'!\n"
                        f"File path: {resolved_path}\n"
                        f"Protected folders: {PROTECTED_SYSTEM_FOLDERS}"
                    )
        
        # Check if filename matches a protected system file (only at root level)
        if len(path_parts) == 1 and path_parts[0] in PROTECTED_SYSTEM_FILES:
            raise WorkspaceSecurityError(
                f"CRITICAL SECURITY VIOLATION: Attempted to overwrite protected system file '{path_parts[0]}'!\n"
                f"File path: {resolved_path}"
            )
    
    return resolved_path


def safe_write_file(
    file_path: Union[str, Path],
    content: str,
    workspace_path: Union[str, Path],
    project_id: Optional[str] = None,
    encoding: str = 'utf-8',
    create_dirs: bool = True
) -> Path:
    """
    Safely write a file with hard guarantees that it won't corrupt platform code.
    
    This is the ONLY function agents should use to write files.
    
    Args:
        file_path: Relative or absolute path to the file
        content: Content to write
        workspace_path: Validated workspace path (must be within Tenant_Projects)
        project_id: Optional project ID for validation
        encoding: File encoding (default: utf-8)
        create_dirs: Whether to create parent directories (default: True)
        
    Returns:
        Resolved absolute Path to the written file
        
    Raises:
        WorkspaceSecurityError: If any security rule is violated
        OSError: If file cannot be written (permissions, disk full, etc.)
    """
    # Step 1: Validate workspace_path
    validated_workspace = validate_workspace_path(workspace_path, project_id)
    
    # Step 2: Validate file_path
    validated_file_path = validate_file_path(file_path, validated_workspace)
    
    # Step 3: Create parent directories if needed
    if create_dirs:
        validated_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Step 4: Write file
    try:
        with open(validated_file_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        logger.debug(f"[SAFE_WRITE] Wrote file: {validated_file_path.relative_to(Path(__file__).resolve().parents[1])}")
        return validated_file_path
    except OSError as e:
        logger.error(f"Failed to write file '{validated_file_path}': {e}")
        raise


def safe_write_file_binary(
    file_path: Union[str, Path],
    content: bytes,
    workspace_path: Union[str, Path],
    project_id: Optional[str] = None,
    create_dirs: bool = True
) -> Path:
    """
    Safely write a binary file with hard guarantees.
    
    Args:
        file_path: Relative or absolute path to the file
        content: Binary content to write
        workspace_path: Validated workspace path
        project_id: Optional project ID for validation
        create_dirs: Whether to create parent directories
        
    Returns:
        Resolved absolute Path to the written file
        
    Raises:
        WorkspaceSecurityError: If any security rule is violated
        OSError: If file cannot be written
    """
    validated_workspace = validate_workspace_path(workspace_path, project_id)
    validated_file_path = validate_file_path(file_path, validated_workspace)
    
    if create_dirs:
        validated_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(validated_file_path, 'wb') as f:
            f.write(content)
        
        logger.debug(f"[SAFE_WRITE] Wrote binary file: {validated_file_path.relative_to(Path(__file__).resolve().parents[1])}")
        return validated_file_path
    except OSError as e:
        logger.error(f"Failed to write binary file '{validated_file_path}': {e}")
        raise

