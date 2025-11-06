"""
Global Research Database
Persistent storage and querying of research results across all projects
"""

import os
import json
import sqlite3
import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ResearchDatabase:
    """
    SQLite-based database for storing and querying research results.
    
    Features:
    - Persistent storage across projects
    - Full-text search on queries and findings
    - Deduplication based on query hash
    - Automatic indexing
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize research database.
        
        Args:
            db_path: Path to SQLite database file (default: ~/.quickodoo/research.db)
        """
        if db_path is None:
            db_dir = os.path.expanduser("~/.quickodoo")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "research.db")
        
        self.db_path = db_path
        self._init_database()
        logger.info(f"Research database initialized at {self.db_path}")
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main research table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                query_hash TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                depth TEXT,
                confidence_score REAL,
                cached INTEGER DEFAULT 0,
                project_name TEXT,
                data_json TEXT NOT NULL,
                UNIQUE(query_hash)
            )
        ''')
        
        # Documentation URLs table (for easier querying)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documentation_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                research_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                FOREIGN KEY (research_id) REFERENCES research(id)
            )
        ''')
        
        # Key findings table (for full-text search)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS key_findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                research_id INTEGER NOT NULL,
                finding TEXT NOT NULL,
                FOREIGN KEY (research_id) REFERENCES research(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_query ON research(query)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_query_hash ON research(query_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON research(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_confidence ON research(confidence_score)')
        
        conn.commit()
        conn.close()
    
    def _hash_query(self, query: str) -> str:
        """Generate hash for query deduplication."""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def store_research(self, research_results: Dict, project_name: Optional[str] = None) -> int:
        """
        Store research results in database.
        
        Args:
            research_results: Research results dictionary
            project_name: Optional project name for tracking
            
        Returns:
            Research ID (database row ID)
        """
        query = research_results.get('query', '')
        query_hash = self._hash_query(query)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Insert main research record
            cursor.execute('''
                INSERT OR REPLACE INTO research 
                (query, query_hash, timestamp, depth, confidence_score, cached, project_name, data_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                query,
                query_hash,
                research_results.get('timestamp', datetime.now().isoformat()),
                research_results.get('depth', 'adaptive'),
                research_results.get('confidence_score', 0),
                1 if research_results.get('cached') else 0,
                project_name,
                json.dumps(research_results)
            ))
            
            research_id = cursor.lastrowid
            
            # Store documentation URLs
            for url in research_results.get('documentation_urls', []):
                cursor.execute('''
                    INSERT INTO documentation_urls (research_id, url)
                    VALUES (?, ?)
                ''', (research_id, url))
            
            # Store key findings
            for finding in research_results.get('key_findings', []):
                cursor.execute('''
                    INSERT INTO key_findings (research_id, finding)
                    VALUES (?, ?)
                ''', (research_id, finding))
            
            conn.commit()
            logger.info(f"Stored research for query '{query}' with ID {research_id}")
            return research_id
            
        except sqlite3.IntegrityError:
            # Research already exists (same query_hash)
            cursor.execute('SELECT id FROM research WHERE query_hash = ?', (query_hash,))
            row = cursor.fetchone()
            if row:
                logger.info(f"Research for query '{query}' already exists with ID {row[0]}")
                return row[0]
            raise
        finally:
            conn.close()
    
    def query_research(self, search_query: str, limit: int = 10) -> List[Dict]:
        """
        Query research database for matching results.
        
        Args:
            search_query: Search string (matches query, findings, URLs)
            limit: Maximum number of results
            
        Returns:
            List of research results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Search in queries and findings
        search_pattern = f"%{search_query}%"
        
        cursor.execute('''
            SELECT DISTINCT r.id, r.data_json, r.confidence_score, r.timestamp
            FROM research r
            LEFT JOIN key_findings kf ON r.id = kf.research_id
            WHERE r.query LIKE ? OR kf.finding LIKE ?
            ORDER BY r.confidence_score DESC, r.timestamp DESC
            LIMIT ?
        ''', (search_pattern, search_pattern, limit))
        
        results = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row[1])
                results.append(data)
            except json.JSONDecodeError as e:
                logger.warning(f"Could not decode research data for ID {row[0]}: {e}")
        
        conn.close()
        logger.info(f"Query '{search_query}' returned {len(results)} results")
        return results
    
    def get_recent_research(self, limit: int = 20) -> List[Dict]:
        """
        Get most recent research results.
        
        Args:
            limit: Number of results to return
            
        Returns:
            List of recent research results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT data_json FROM research
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        results = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row[0])
                results.append(data)
            except json.JSONDecodeError as e:
                logger.warning(f"Could not decode research data: {e}")
        
        conn.close()
        return results
    
    def get_research_by_platform(self, platform: str, limit: int = 10) -> List[Dict]:
        """
        Get research results related to a specific platform.
        
        Args:
            platform: Platform name (e.g., "QuickBooks", "SAGE", "Stripe")
            limit: Maximum number of results
            
        Returns:
            List of research results
        """
        return self.query_research(platform, limit=limit)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total research records
        cursor.execute('SELECT COUNT(*) FROM research')
        stats['total_research_records'] = cursor.fetchone()[0]
        
        # Total documentation URLs
        cursor.execute('SELECT COUNT(*) FROM documentation_urls')
        stats['total_documentation_urls'] = cursor.fetchone()[0]
        
        # Total key findings
        cursor.execute('SELECT COUNT(*) FROM key_findings')
        stats['total_key_findings'] = cursor.fetchone()[0]
        
        # Average confidence score
        cursor.execute('SELECT AVG(confidence_score) FROM research')
        stats['average_confidence_score'] = round(cursor.fetchone()[0] or 0, 2)
        
        # Most recent research
        cursor.execute('SELECT query, timestamp FROM research ORDER BY timestamp DESC LIMIT 1')
        row = cursor.fetchone()
        if row:
            stats['most_recent_query'] = row[0]
            stats['most_recent_timestamp'] = row[1]
        
        # Top platforms (by query frequency)
        cursor.execute('''
            SELECT query, COUNT(*) as count 
            FROM research 
            GROUP BY query 
            ORDER BY count DESC 
            LIMIT 5
        ''')
        stats['top_queries'] = [{"query": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        conn.close()
        return stats
    
    def export_research(self, output_path: str):
        """
        Export all research to JSON file for backup.
        
        Args:
            output_path: Path to output JSON file
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT data_json FROM research ORDER BY timestamp DESC')
        
        all_research = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row[0])
                all_research.append(data)
            except json.JSONDecodeError:
                continue
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_research, f, indent=2)
        
        conn.close()
        logger.info(f"Exported {len(all_research)} research records to {output_path}")
    
    def import_research(self, input_path: str, project_name: Optional[str] = None):
        """
        Import research from JSON file.
        
        Args:
            input_path: Path to input JSON file
            project_name: Optional project name for imported research
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            research_list = json.load(f)
        
        imported = 0
        for research in research_list:
            try:
                self.store_research(research, project_name=project_name)
                imported += 1
            except Exception as e:
                logger.warning(f"Could not import research: {e}")
        
        logger.info(f"Imported {imported}/{len(research_list)} research records")


# Global database instance
_global_db = None


def get_research_database() -> ResearchDatabase:
    """Get or create global research database instance."""
    global _global_db
    if _global_db is None:
        _global_db = ResearchDatabase()
    return _global_db


# Convenience functions
def store_research(research_results: Dict, project_name: Optional[str] = None) -> int:
    """Store research results in global database."""
    db = get_research_database()
    return db.store_research(research_results, project_name)


def query_research(search_query: str, limit: int = 10) -> List[Dict]:
    """Query global research database."""
    db = get_research_database()
    return db.query_research(search_query, limit)


def get_research_by_platform(platform: str, limit: int = 10) -> List[Dict]:
    """Get research for specific platform."""
    db = get_research_database()
    return db.get_research_by_platform(platform, limit)


def get_research_statistics() -> Dict:
    """Get research database statistics."""
    db = get_research_database()
    return db.get_statistics()

