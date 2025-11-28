"""
Git Manager - Handles Git operations for automatic commits and PR creation.
"""

import subprocess
import logging
import os
import threading
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class GitManager:
    """Manages Git operations for the project."""
    
    def __init__(self, workspace_path: str = ".", auto_commit: bool = True):
        self.workspace_path = Path(workspace_path)
        # QA_Engineer: Respect GIT_AUTO_COMMIT_ENABLED environment variable (default: False for production safety)
        # If auto_commit is explicitly passed, use it; otherwise check environment variable
        if auto_commit is True:
            # Check environment variable if auto_commit was not explicitly set to False
            git_auto_commit_env = os.getenv("GIT_AUTO_COMMIT_ENABLED", "false").lower() == "true"
            self.auto_commit = git_auto_commit_env
        else:
            # Explicitly set to False - respect that
            self.auto_commit = False
        
        self.git_available = self._check_git_available()
        
        if self.auto_commit:
            logger.info(f"Git auto-commit enabled for workspace: {workspace_path}")
        else:
            logger.debug(f"Git auto-commit disabled for workspace: {workspace_path}")
        
        # QA_Engineer: Solution 2 - Batch Commits - Queue for batch commit operations
        self._batch_commit_queue: Dict[str, List[Dict[str, Any]]] = defaultdict(list)  # workspace_path -> [commit_info]
        self._batch_commit_lock = threading.Lock()
        self._batch_commit_max_size = 10  # Maximum files per batch commit
        self._batch_commit_timeout = 30.0  # Seconds before auto-flush
        
        if not self.git_available:
            logger.warning("Git is not available. VCS features will be disabled.")
    
    def _check_git_available(self) -> bool:
        """Check if Git is available in the system."""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=self.workspace_path
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def is_git_repo(self) -> bool:
        """Check if workspace is a Git repository."""
        if not self.git_available:
            return False
        
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=self.workspace_path
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
    
    def initialize_repo(self, initial_commit: bool = False) -> bool:
        """Initialize a Git repository if it doesn't exist."""
        if not self.git_available:
            return False
        
        if self.is_git_repo():
            logger.info("Git repository already exists")
            return True
        
        try:
            subprocess.run(
                ["git", "init"],
                check=True,
                capture_output=True,
                timeout=10,
                cwd=self.workspace_path
            )
            logger.info("Initialized Git repository")
            
            if initial_commit:
                # Create initial commit with .gitignore if exists
                if (self.workspace_path / ".gitignore").exists():
                    subprocess.run(
                        ["git", "add", ".gitignore"],
                        check=True,
                        capture_output=True,
                        timeout=10,
                        cwd=self.workspace_path
                    )
                    subprocess.run(
                        ["git", "commit", "-m", "Initial commit: Add .gitignore"],
                        check=True,
                        capture_output=True,
                        timeout=10,
                        cwd=self.workspace_path
                    )
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to initialize Git repository: {e}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Git init timed out")
            return False
    
    def get_current_branch(self) -> Optional[str]:
        """Get the current Git branch."""
        if not self.is_git_repo():
            return None
        
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
                cwd=self.workspace_path
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None
    
    def create_branch(self, branch_name: str, base_branch: str = "main") -> bool:
        """Create a new branch from base branch."""
        if not self.is_git_repo():
            if not self.initialize_repo():
                return False
        
        try:
            # Checkout base branch first
            subprocess.run(
                ["git", "checkout", base_branch],
                capture_output=True,
                timeout=10,
                cwd=self.workspace_path
            )
            
            # Create and checkout new branch
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.workspace_path
            )
            logger.info(f"Created and checked out branch: {branch_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"Branch {branch_name} may already exist: {e}")
            # Try to checkout existing branch
            try:
                subprocess.run(
                    ["git", "checkout", branch_name],
                    check=True,
                    capture_output=True,
                    timeout=10,
                    cwd=self.workspace_path
                )
                return True
            except subprocess.CalledProcessError:
                return False
        except subprocess.TimeoutExpired:
            logger.error("Git branch creation timed out")
            return False
    
    def get_modified_files(self) -> List[str]:
        """Get list of modified/untracked files."""
        if not self.is_git_repo():
            return []
        
        try:
            # Get modified files
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
                cwd=self.workspace_path
            )
            
            files = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    # Parse git status output (XY filename)
                    status = line[:2]
                    filename = line[3:].strip()
                    if status[1] != ' ' or status[0] in ['M', 'A', '?']:  # Modified, Added, or Untracked
                        files.append(filename)
            
            return files
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return []
    
    def stage_files(self, files: Optional[List[str]] = None, ignore_patterns: Optional[List[str]] = None) -> bool:
        """
        Stage files for commit.
        
        Args:
            files: List of specific files to stage (None = all modified)
            ignore_patterns: Patterns to ignore (e.g., ['*.pyc', '__pycache__/'])
        """
        if not self.is_git_repo():
            return False
        
        try:
            if files:
                # Stage specific files
                for file in files:
                    file_path = self.workspace_path / file
                    if file_path.exists():
                        # Check against ignore patterns
                        if ignore_patterns:
                            should_ignore = False
                            for pattern in ignore_patterns:
                                if pattern in str(file_path):
                                    should_ignore = True
                                    break
                            if should_ignore:
                                continue
                        
                        subprocess.run(
                            ["git", "add", file],
                            check=True,
                            capture_output=True,
                            timeout=10,
                            cwd=self.workspace_path
                        )
            else:
                # Stage all modified files
                subprocess.run(
                    ["git", "add", "-A"],
                    check=True,
                    capture_output=True,
                    timeout=10,
                    cwd=self.workspace_path
                )
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stage files: {e}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Git add timed out")
            return False
    
    def commit(self, message: str, author: Optional[str] = None) -> bool:
        """
        Create a Git commit.
        
        Args:
            message: Commit message
            author: Optional author (format: "Name <email>")
        """
        if not self.is_git_repo():
            return False
        
        try:
            cmd = ["git", "commit", "-m", message]
            if author:
                cmd.extend(["--author", author])
            
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.workspace_path
            )
            
            logger.info(f"Created commit: {message[:50]}...")
            return True
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in e.stderr.lower():
                logger.debug("No changes to commit")
                return False
            logger.error(f"Failed to create commit: {e}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Git commit timed out")
            return False
    
    def auto_commit_task_completion(self, task_id: str, task_title: str, files_created: List[str]) -> bool:
        """
        Automatically commit files created by a completed task.
        
        QA_Engineer: Solution 2 - Batch Commits - Queue commits for batch processing
        instead of committing immediately to reduce Git operation frequency.
        
        Args:
            task_id: Task ID
            task_title: Task title/description
            files_created: List of files created by the task
        """
        if not self.auto_commit:
            return False
        
        if not self.is_git_repo():
            logger.debug("Not a Git repository, skipping auto-commit")
            return False
        
        if not files_created:
            return False
        
        # QA_Engineer: Solution 2 - Batch Commits - Queue commit instead of committing immediately
        workspace_key = str(self.workspace_path)
        
        with self._batch_commit_lock:
            # Add to batch queue
            self._batch_commit_queue[workspace_key].append({
                "task_id": task_id,
                "task_title": task_title,
                "files_created": files_created,
                "timestamp": datetime.now()
            })
            
            queue_size = len(self._batch_commit_queue[workspace_key])
            
            # Auto-flush if queue reaches max size
            if queue_size >= self._batch_commit_max_size:
                logger.debug(f"Batch commit queue full ({queue_size} items), flushing...")
                return self._flush_batch_commits(workspace_key)
            else:
                logger.debug(f"Queued commit for task {task_id} ({queue_size}/{self._batch_commit_max_size} in queue)")
                return True
    
    def _flush_batch_commits(self, workspace_key: Optional[str] = None) -> bool:
        """
        Flush batch commit queue and create commits.
        
        QA_Engineer: Solution 2 - Batch Commits - Group file changes and commit together.
        
        Args:
            workspace_key: Specific workspace to flush (None = flush all)
        
        Returns:
            True if commits were successful
        """
        with self._batch_commit_lock:
            workspaces_to_flush = [workspace_key] if workspace_key else list(self._batch_commit_queue.keys())
            
            for ws_key in workspaces_to_flush:
                if ws_key not in self._batch_commit_queue or not self._batch_commit_queue[ws_key]:
                    continue
                
                commit_items = self._batch_commit_queue[ws_key]
                if not commit_items:
                    continue
                
                # Group files by task type/agent for better commit messages
                all_files = []
                task_summaries = []
                
                for item in commit_items:
                    all_files.extend(item["files_created"])
                    task_summaries.append({
                        "task_id": item["task_id"],
                        "task_title": item["task_title"],
                        "file_count": len(item["files_created"])
                    })
                
                # Remove duplicates while preserving order
                seen = set()
                unique_files = []
                for file in all_files:
                    if file not in seen:
                        seen.add(file)
                        unique_files.append(file)
                
                if not unique_files:
                    self._batch_commit_queue[ws_key] = []
                    continue
                
                # Stage all files
                if not self.stage_files(unique_files):
                    logger.warning(f"Failed to stage files for batch commit, skipping")
                    self._batch_commit_queue[ws_key] = []
                    continue
                
                # Generate batch commit message
                commit_message = self._generate_batch_commit_message(task_summaries, unique_files)
                
                # Create batch commit
                success = self.commit(commit_message)
                
                if success:
                    logger.info(f"Batch commit successful: {len(unique_files)} files from {len(task_summaries)} tasks")
                    self._batch_commit_queue[ws_key] = []
                else:
                    logger.warning(f"Batch commit failed, keeping {len(commit_items)} items in queue")
                    # Keep failed items in queue for retry
        
        return True
    
    def _generate_batch_commit_message(self, task_summaries: List[Dict[str, Any]], files: List[str]) -> str:
        """Generate commit message for batch commit."""
        files_summary = ", ".join(files[:5])
        if len(files) > 5:
            files_summary += f" and {len(files) - 5} more"
        
        message = f"feat: Batch commit - {len(task_summaries)} tasks\n\n"
        message += f"Tasks completed:\n"
        for summary in task_summaries[:10]:  # Limit to first 10 tasks
            message += f"- {summary['task_title']} ({summary['file_count']} files)\n"
        
        if len(task_summaries) > 10:
            message += f"- ... and {len(task_summaries) - 10} more tasks\n"
        
        message += f"\nFiles created: {files_summary}\n"
        message += f"Total files: {len(files)}\n"
        message += f"Generated by Multi-Agent System"
        
        return message
    
    def flush_pending_commits(self) -> bool:
        """
        Flush all pending batch commits.
        
        Call this method when project completes or at regular intervals.
        """
        return self._flush_batch_commits()
    
    def _generate_commit_message(self, task_id: str, task_title: str, files_created: List[str]) -> str:
        """Generate a commit message from task information."""
        files_summary = ", ".join(files_created[:3])
        if len(files_created) > 3:
            files_summary += f" and {len(files_created) - 3} more"
        
        message = f"feat: {task_title}\n\n"
        message += f"Task: {task_id}\n"
        message += f"Files created: {files_summary}\n"
        message += f"Generated by Multi-Agent System"
        
        return message
    
    def push_branch(self, branch_name: Optional[str] = None, remote: str = "origin") -> bool:
        """Push branch to remote repository."""
        if not self.is_git_repo():
            return False
        
        branch = branch_name or self.get_current_branch()
        if not branch:
            return False
        
        try:
            result = subprocess.run(
                ["git", "push", "-u", remote, branch],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.workspace_path
            )
            
            if result.returncode == 0:
                logger.info(f"Pushed branch {branch} to {remote}")
                return True
            else:
                logger.warning(f"Push failed or branch already exists: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error("Git push timed out")
            return False


# Singleton instance
_git_manager: Optional[GitManager] = None


def get_git_manager(workspace_path: str = ".", auto_commit: bool = True) -> GitManager:
    """Get the singleton GitManager instance."""
    global _git_manager
    if _git_manager is None:
        _git_manager = GitManager(workspace_path, auto_commit)
    return _git_manager

