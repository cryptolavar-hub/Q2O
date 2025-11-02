"""
Language Detection Utility - Detects programming languages and package managers.
Supports multi-language projects and auto-detection.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Detects programming languages and package managers in a project."""
    
    # File extensions mapping
    LANGUAGE_EXTENSIONS = {
        "python": [".py", ".pyi", ".pyw"],
        "javascript": [".js", ".mjs", ".cjs"],
        "typescript": [".ts", ".tsx"],
        "nodejs": [".js", ".mjs", ".cjs", ".ts", ".tsx", ".json"],  # Node.js includes JS/TS
        "go": [".go"],
        "java": [".java"],
        "csharp": [".cs"],
        "ruby": [".rb"],
        "php": [".php"],
        "rust": [".rs"],
        "terraform": [".tf", ".tfvars"],
        "yaml": [".yaml", ".yml"],
        "json": [".json"],
    }
    
    # Package manager indicators
    PACKAGE_MANAGERS = {
        "npm": ["package.json"],
        "pnpm": ["pnpm-lock.yaml", "pnpm-workspace.yaml"],
        "yarn": ["yarn.lock", "yarn.json"],
        "pip": ["requirements.txt", "setup.py", "pyproject.toml"],
        "poetry": ["poetry.lock", "pyproject.toml"],
        "pipenv": ["Pipfile", "Pipfile.lock"],
        "go": ["go.mod", "go.sum"],
        "maven": ["pom.xml"],
        "gradle": ["build.gradle", "build.gradle.kts"],
        "cargo": ["Cargo.toml", "Cargo.lock"],
        "composer": ["composer.json", "composer.lock"],
        "gem": ["Gemfile", "Gemfile.lock"],
    }
    
    # Framework indicators
    FRAMEWORK_INDICATORS = {
        "nextjs": ["next.config.js", "next.config.ts", "pages/", "app/"],
        "react": ["react", "react-dom"],  # In package.json
        "express": ["express"],  # In package.json
        "nestjs": ["@nestjs/core"],  # In package.json
        "fastapi": ["fastapi"],  # In requirements.txt or imports
        "django": ["django"],  # In requirements.txt or imports
        "flask": ["flask"],  # In requirements.txt or imports
        "spring": ["spring-boot"],  # In pom.xml or build.gradle
        "rails": ["rails"],  # In Gemfile
        "laravel": ["laravel/framework"],  # In composer.json
    }
    
    def __init__(self, workspace_path: str = "."):
        self.workspace_path = Path(workspace_path)
    
    def detect_languages(self, limit: int = 100) -> Dict[str, Any]:
        """
        Detect all languages in the project.
        
        Args:
            limit: Maximum number of files to scan
            
        Returns:
            Dictionary with detected languages, frameworks, and package managers
        """
        detected_languages: Set[str] = set()
        detected_package_managers: Set[str] = set()
        detected_frameworks: Set[str] = set()
        file_counts: Dict[str, int] = defaultdict(int)
        
        scanned = 0
        
        # Scan files
        for root, dirs, files in os.walk(self.workspace_path):
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build'}]
            
            for file in files:
                if scanned >= limit:
                    break
                
                file_path = Path(root) / file
                ext = file_path.suffix.lower()
                
                # Detect by extension
                for lang, exts in self.LANGUAGE_EXTENSIONS.items():
                    if ext in exts:
                        detected_languages.add(lang)
                        file_counts[lang] += 1
                        scanned += 1
                        break
                
                # Detect package managers
                for pm, indicators in self.PACKAGE_MANAGERS.items():
                    if file in indicators:
                        detected_package_managers.add(pm)
            
            if scanned >= limit:
                break
        
        # Detect frameworks from package files
        package_files = self._find_package_files()
        for pkg_file in package_files:
            frameworks = self._detect_frameworks_from_package(pkg_file)
            detected_frameworks.update(frameworks)
        
        # Special handling: Node.js includes JavaScript/TypeScript
        if "nodejs" in detected_languages:
            detected_languages.add("javascript")
            if any(f.endswith(".ts") or f.endswith(".tsx") for f in file_counts.keys()):
                detected_languages.add("typescript")
        
        return {
            "languages": sorted(list(detected_languages)),
            "package_managers": sorted(list(detected_package_managers)),
            "frameworks": sorted(list(detected_frameworks)),
            "file_counts": file_counts,
            "primary_language": self._determine_primary_language(detected_languages, file_counts)
        }
    
    def _find_package_files(self) -> List[Path]:
        """Find package manager files in workspace."""
        package_files = []
        common_names = [
            "package.json", "pyproject.toml", "requirements.txt", "go.mod",
            "pom.xml", "build.gradle", "Cargo.toml", "composer.json", "Gemfile"
        ]
        
        for root, dirs, files in os.walk(self.workspace_path):
            for file in files:
                if file in common_names:
                    package_files.append(Path(root) / file)
        
        return package_files
    
    def _detect_frameworks_from_package(self, package_file: Path) -> List[str]:
        """Detect frameworks from package manager files."""
        frameworks = []
        
        try:
            if package_file.name == "package.json":
                with open(package_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    
                    if "next" in deps:
                        frameworks.append("nextjs")
                    if "react" in deps:
                        frameworks.append("react")
                    if "express" in deps:
                        frameworks.append("express")
                    if "@nestjs/core" in deps:
                        frameworks.append("nestjs")
            
            elif package_file.name in ["requirements.txt", "pyproject.toml"]:
                # Check for Python frameworks
                content = package_file.read_text(encoding='utf-8')
                if "fastapi" in content.lower():
                    frameworks.append("fastapi")
                if "django" in content.lower():
                    frameworks.append("django")
                if "flask" in content.lower():
                    frameworks.append("flask")
        except Exception as e:
            logger.debug(f"Error reading package file {package_file}: {e}")
        
        return frameworks
    
    def _determine_primary_language(self, languages: Set[str], file_counts: Dict[str, int]) -> Optional[str]:
        """Determine the primary language based on file counts."""
        if not languages:
            return None
        
        # Remove meta languages
        candidates = {lang: count for lang, count in file_counts.items() if lang in languages}
        
        if not candidates:
            return sorted(languages)[0]
        
        return max(candidates.items(), key=lambda x: x[1])[0]
    
    def detect_nodejs_version(self) -> Optional[str]:
        """
        Detect Node.js version requirement from package.json or .nvmrc.
        
        Returns:
            Node.js version string (e.g., ">=20.0.0") or None
        """
        # Check .nvmrc
        nvmrc = self.workspace_path / ".nvmrc"
        if nvmrc.exists():
            return nvmrc.read_text(encoding='utf-8').strip()
        
        # Check package.json engines
        package_json = self.workspace_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    engines = data.get("engines", {})
                    node_version = engines.get("node")
                    if node_version:
                        return node_version
            except Exception:
                pass
        
        return None


def get_language_detector(workspace_path: str = ".") -> LanguageDetector:
    """Get a LanguageDetector instance."""
    return LanguageDetector(workspace_path)

