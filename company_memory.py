#!/usr/bin/env python3
"""
Company Memory Management System
Industry-standard persistent storage for company name equivalences across all users and sessions.

Uses SQLite for reliable data persistence with proper indexing and ACID compliance.
"""

import sqlite3
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from contextlib import contextmanager

class CompanyMemoryManager:
    """
    Manages persistent company name equivalences using SQLite.
    Thread-safe with connection pooling for concurrent access.
    """
    
    def __init__(self, db_path: str = "company_memory.db"):
        """Initialize the memory manager with SQLite database."""
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with proper schema and indexes."""
        with self._get_connection() as conn:
            conn.executescript("""
                -- Main company equivalences table
                CREATE TABLE IF NOT EXISTS company_equivalences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    extracted_company TEXT NOT NULL,
                    dnm_company TEXT NOT NULL,
                    similarity_percentage REAL NOT NULL,
                    user_decision BOOLEAN NOT NULL, -- True = same company, False = different
                    confidence_score REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT,
                    statement_id TEXT,
                    page_info TEXT,
                    destination TEXT,
                    UNIQUE(extracted_company, dnm_company) -- Prevent duplicates
                );
                
                -- Index for fast lookups
                CREATE INDEX IF NOT EXISTS idx_extracted_company ON company_equivalences(extracted_company);
                CREATE INDEX IF NOT EXISTS idx_dnm_company ON company_equivalences(dnm_company);
                CREATE INDEX IF NOT EXISTS idx_user_decision ON company_equivalences(user_decision);
                CREATE INDEX IF NOT EXISTS idx_created_at ON company_equivalences(created_at);
                
                -- Company statistics view for analytics
                CREATE VIEW IF NOT EXISTS company_stats AS
                SELECT 
                    extracted_company,
                    COUNT(*) as total_questions,
                    COUNT(CASE WHEN user_decision = 1 THEN 1 END) as confirmed_matches,
                    COUNT(CASE WHEN user_decision = 0 THEN 1 END) as rejected_matches,
                    AVG(similarity_percentage) as avg_similarity,
                    MAX(updated_at) as last_updated,
                    GROUP_CONCAT(DISTINCT destination) as destinations
                FROM company_equivalences
                GROUP BY extracted_company;
                
                -- Global statistics table
                CREATE TABLE IF NOT EXISTS system_stats (
                    stat_name TEXT PRIMARY KEY,
                    stat_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Insert initial stats
                INSERT OR IGNORE INTO system_stats (stat_name, stat_value) VALUES
                ('total_companies', '0'),
                ('total_questions', '0'),
                ('total_matches', '0'),
                ('system_initialized', datetime('now'));
            """)
            
            # Update stats
            self._update_system_stats(conn)
    
    @contextmanager
    def _get_connection(self):
        """Get a thread-safe database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path, 
                timeout=10.0,
                isolation_level=None  # Auto-commit mode
            )
            conn.row_factory = sqlite3.Row  # Enable column access by name
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")  # Better concurrency
            yield conn
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def check_previous_answer(self, extracted_company: str, dnm_company: str) -> Optional[Dict[str, Any]]:
        """
        Check if this company pair has been answered before.
        
        Args:
            extracted_company: Company name extracted from PDF
            dnm_company: Company name from DNM list
            
        Returns:
            Dict with decision info or None if not previously answered
        """
        with self._get_connection() as conn:
            result = conn.execute("""
                SELECT user_decision, similarity_percentage, created_at, updated_at, confidence_score
                FROM company_equivalences
                WHERE extracted_company = ? AND dnm_company = ?
                ORDER BY updated_at DESC
                LIMIT 1
            """, (extracted_company, dnm_company)).fetchone()
            
            if result:
                return {
                    'previously_answered': True,
                    'decision': bool(result['user_decision']),
                    'similarity_percentage': result['similarity_percentage'],
                    'created_at': result['created_at'],
                    'updated_at': result['updated_at'],
                    'confidence_score': result['confidence_score']
                }
            return {'previously_answered': False}
    
    def store_answer(self, extracted_company: str, dnm_company: str, 
                    similarity_percentage: float, user_decision: bool,
                    session_id: str = None, statement_id: str = None,
                    page_info: str = None, destination: str = None) -> bool:
        """
        Store or update a user's decision about company equivalence.
        
        Args:
            extracted_company: Company name extracted from PDF
            dnm_company: Company name from DNM list
            similarity_percentage: Similarity score as percentage
            user_decision: True if same company, False if different
            session_id: Optional session identifier
            statement_id: Optional statement identifier
            page_info: Optional page information
            destination: Optional destination classification
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            with self._get_connection() as conn:
                # Use INSERT OR REPLACE for upsert behavior
                conn.execute("""
                    INSERT OR REPLACE INTO company_equivalences (
                        extracted_company, dnm_company, similarity_percentage,
                        user_decision, session_id, statement_id, page_info,
                        destination, updated_at, confidence_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                """, (
                    extracted_company, dnm_company, similarity_percentage,
                    user_decision, session_id, statement_id, page_info,
                    destination, similarity_percentage / 100.0
                ))
                
                # Update system stats
                self._update_system_stats(conn)
                
                self.logger.info(f"Stored answer: {extracted_company} vs {dnm_company} = {user_decision}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error storing answer: {e}")
            return False
    
    def get_all_companies(self) -> List[Dict[str, Any]]:
        """
        Get all companies with their equivalence data for management interface.
        
        Returns:
            List of company data with equivalences
        """
        with self._get_connection() as conn:
            # Get all unique extracted companies with their stats
            companies = conn.execute("""
                SELECT * FROM company_stats
                ORDER BY last_updated DESC
            """).fetchall()
            
            result = []
            for company in companies:
                # Get all equivalences for this company
                equivalences = conn.execute("""
                    SELECT dnm_company, similarity_percentage, user_decision,
                           created_at, updated_at, page_info, destination
                    FROM company_equivalences
                    WHERE extracted_company = ?
                    ORDER BY similarity_percentage DESC
                """, (company['extracted_company'],)).fetchall()
                
                result.append({
                    'extracted_company': company['extracted_company'],
                    'total_questions': company['total_questions'],
                    'confirmed_matches': company['confirmed_matches'],
                    'rejected_matches': company['rejected_matches'],
                    'avg_similarity': round(company['avg_similarity'], 1),
                    'last_updated': company['last_updated'],
                    'destinations': company['destinations'].split(',') if company['destinations'] else [],
                    'equivalences': [
                        {
                            'dnm_company': eq['dnm_company'],
                            'similarity_percentage': eq['similarity_percentage'],
                            'user_decision': bool(eq['user_decision']),
                            'created_at': eq['created_at'],
                            'updated_at': eq['updated_at'],
                            'page_info': eq['page_info'],
                            'destination': eq['destination']
                        } for eq in equivalences
                    ]
                })
            
            return result
    
    def update_company_equivalences(self, extracted_company: str, 
                                   equivalences: List[Dict[str, Any]]) -> bool:
        """
        Update all equivalences for a specific company.
        
        Args:
            extracted_company: The company to update
            equivalences: List of equivalence dictionaries
            
        Returns:
            True if updated successfully
        """
        try:
            with self._get_connection() as conn:
                for eq in equivalences:
                    conn.execute("""
                        UPDATE company_equivalences 
                        SET user_decision = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE extracted_company = ? AND dnm_company = ?
                    """, (
                        eq['user_decision'], 
                        extracted_company, 
                        eq['dnm_company']
                    ))
                
                self._update_system_stats(conn)
                self.logger.info(f"Updated {len(equivalences)} equivalences for {extracted_company}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating equivalences: {e}")
            return False
    
    def delete_company(self, extracted_company: str) -> bool:
        """
        Delete all equivalences for a specific company.
        
        Args:
            extracted_company: Company to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            with self._get_connection() as conn:
                result = conn.execute("""
                    DELETE FROM company_equivalences 
                    WHERE extracted_company = ?
                """, (extracted_company,))
                
                deleted_count = result.rowcount
                self._update_system_stats(conn)
                
                self.logger.info(f"Deleted {deleted_count} equivalences for {extracted_company}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error deleting company: {e}")
            return False
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics."""
        with self._get_connection() as conn:
            stats = {}
            for row in conn.execute("SELECT stat_name, stat_value FROM system_stats"):
                stats[row['stat_name']] = row['stat_value']
            
            # Add real-time stats
            realtime_stats = conn.execute("""
                SELECT 
                    COUNT(DISTINCT extracted_company) as unique_companies,
                    COUNT(*) as total_equivalences,
                    COUNT(CASE WHEN user_decision = 1 THEN 1 END) as total_matches,
                    AVG(similarity_percentage) as avg_similarity
                FROM company_equivalences
            """).fetchone()
            
            stats.update({
                'unique_companies': realtime_stats['unique_companies'],
                'total_equivalences': realtime_stats['total_equivalences'],
                'total_matches': realtime_stats['total_matches'],
                'avg_similarity': round(realtime_stats['avg_similarity'] or 0, 1)
            })
            
            return stats
    
    def _update_system_stats(self, conn):
        """Update system statistics."""
        stats = conn.execute("""
            SELECT 
                COUNT(DISTINCT extracted_company) as companies,
                COUNT(*) as questions,
                COUNT(CASE WHEN user_decision = 1 THEN 1 END) as matches
            FROM company_equivalences
        """).fetchone()
        
        conn.execute("""
            INSERT OR REPLACE INTO system_stats (stat_name, stat_value, updated_at) VALUES
            ('total_companies', ?, CURRENT_TIMESTAMP),
            ('total_questions', ?, CURRENT_TIMESTAMP),
            ('total_matches', ?, CURRENT_TIMESTAMP)
        """, (str(stats['companies']), str(stats['questions']), str(stats['matches'])))
    
    def export_data(self) -> Dict[str, Any]:
        """Export all data for backup purposes."""
        with self._get_connection() as conn:
            equivalences = conn.execute("""
                SELECT * FROM company_equivalences ORDER BY created_at
            """).fetchall()
            
            return {
                'export_timestamp': datetime.now().isoformat(),
                'total_records': len(equivalences),
                'equivalences': [dict(row) for row in equivalences],
                'system_stats': self.get_system_stats()
            }
    
    def import_data(self, data: Dict[str, Any]) -> bool:
        """Import data from backup."""
        try:
            with self._get_connection() as conn:
                for eq in data.get('equivalences', []):
                    conn.execute("""
                        INSERT OR REPLACE INTO company_equivalences (
                            extracted_company, dnm_company, similarity_percentage,
                            user_decision, session_id, statement_id, page_info,
                            destination, created_at, updated_at, confidence_score
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        eq['extracted_company'], eq['dnm_company'], eq['similarity_percentage'],
                        eq['user_decision'], eq.get('session_id'), eq.get('statement_id'),
                        eq.get('page_info'), eq.get('destination'), eq.get('created_at'),
                        eq.get('updated_at'), eq.get('confidence_score', 0.0)
                    ))
                
                self._update_system_stats(conn)
                self.logger.info(f"Imported {len(data.get('equivalences', []))} records")
                return True
                
        except Exception as e:
            self.logger.error(f"Error importing data: {e}")
            return False


# Global instance for the application
memory_manager = CompanyMemoryManager()