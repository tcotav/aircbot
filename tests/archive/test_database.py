#!/usr/bin/env python3
"""
Database Test Suite for AircBot
Tests database operations, link management, and data integrity
"""

import unittest
import os
import tempfile
import sqlite3
from unittest.mock import patch, Mock
import time

from database import Database

class TestDatabase(unittest.TestCase):
    """Test database functionality"""
    
    def setUp(self):
        """Set up test database"""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        self.db = Database(self.db_path)
    
    def tearDown(self):
        """Clean up test database"""
        try:
            os.unlink(self.db_path)
        except OSError:
            pass
    
    def test_database_initialization(self):
        """Test that database is properly initialized"""
        self.assertTrue(os.path.exists(self.db_path))
        
        # Check that tables exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        self.assertIn('links', tables)
        conn.close()
    
    def test_save_link_basic(self):
        """Test basic link saving functionality"""
        url = "https://example.com"
        title = "Example Site"
        description = "A test website"
        user = "testuser"
        channel = "#test"
        
        result = self.db.save_link(url, title, description, user, channel)
        self.assertTrue(result)
        
        # Verify link was saved
        links = self.db.get_recent_links(channel, limit=1)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]['url'], url)
        self.assertEqual(links[0]['title'], title)
        self.assertEqual(links[0]['user'], user)
    
    def test_duplicate_link_handling(self):
        """Test that duplicate links are handled correctly"""
        url = "https://example.com"
        title = "Example Site"
        description = "A test website"
        user1 = "user1"
        user2 = "user2"
        channel = "#test"
        
        # Save same URL twice with different users
        result1 = self.db.save_link(url, title, description, user1, channel)
        result2 = self.db.save_link(url, title, description, user2, channel)
        
        self.assertTrue(result1)
        self.assertFalse(result2)  # Should reject duplicate
        
        # Should only have one link
        links = self.db.get_recent_links(channel)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]['user'], user1)  # First user should be preserved
    
    def test_get_recent_links(self):
        """Test retrieving recent links"""
        channel = "#test"
        
        # Add multiple links
        links_data = [
            ("https://example1.com", "Site 1", "Description 1", "user1"),
            ("https://example2.com", "Site 2", "Description 2", "user2"),
            ("https://example3.com", "Site 3", "Description 3", "user3"),
        ]
        
        for url, title, desc, user in links_data:
            self.db.save_link(url, title, desc, user, channel)
            time.sleep(0.01)  # Ensure different timestamps
        
        # Test limit functionality
        recent_links = self.db.get_recent_links(channel, limit=2)
        self.assertEqual(len(recent_links), 2)
        
        # Should be in reverse chronological order (newest first)
        self.assertEqual(recent_links[0]['url'], "https://example3.com")
        self.assertEqual(recent_links[1]['url'], "https://example2.com")
    
    def test_search_links(self):
        """Test link search functionality"""
        channel = "#test"
        
        # Add test links
        test_links = [
            ("https://github.com/python/cpython", "Python Source", "Python repository", "dev1"),
            ("https://docs.python.org", "Python Docs", "Python documentation", "dev2"),
            ("https://stackoverflow.com/questions/tagged/javascript", "JS Questions", "JavaScript Q&A", "dev3"),
        ]
        
        for url, title, desc, user in test_links:
            self.db.save_link(url, title, desc, user, channel)
        
        # Test search by title
        python_links = self.db.search_links(channel, "python")
        self.assertEqual(len(python_links), 2)
        
        # Test search by URL
        github_links = self.db.search_links(channel, "github")
        self.assertEqual(len(github_links), 1)
        self.assertEqual(github_links[0]['title'], "Python Source")
        
        # Test case insensitive search
        js_links = self.db.search_links(channel, "JAVASCRIPT")
        self.assertEqual(len(js_links), 1)
    
    def test_get_links_by_user(self):
        """Test retrieving links by specific user"""
        channel = "#test"
        user1 = "alice"
        user2 = "bob"
        
        # Add links from different users
        self.db.save_link("https://alice1.com", "Alice Link 1", "Desc 1", user1, channel)
        self.db.save_link("https://bob1.com", "Bob Link 1", "Desc 2", user2, channel)
        self.db.save_link("https://alice2.com", "Alice Link 2", "Desc 3", user1, channel)
        
        # Test getting links by user
        alice_links = self.db.get_links_by_user(channel, user1)
        bob_links = self.db.get_links_by_user(channel, user2)
        
        self.assertEqual(len(alice_links), 2)
        self.assertEqual(len(bob_links), 1)
        
        # Verify correct attribution
        for link in alice_links:
            self.assertEqual(link['user'], user1)
        for link in bob_links:
            self.assertEqual(link['user'], user2)
    
    def test_get_stats(self):
        """Test statistics retrieval"""
        channel = "#test"
        
        # Add test data
        self.db.save_link("https://example1.com", "Title 1", "Desc 1", "user1", channel)
        self.db.save_link("https://example2.com", "Title 2", "Desc 2", "user1", channel)
        self.db.save_link("https://example3.com", "Title 3", "Desc 3", "user2", channel)
        
        stats = self.db.get_stats(channel)
        
        self.assertEqual(stats['total_links'], 3)
        self.assertEqual(stats['unique_users'], 2)
        self.assertIn('user1', stats['top_contributors'])
        self.assertIn('user2', stats['top_contributors'])
    
    def test_channel_isolation(self):
        """Test that channels are properly isolated"""
        channel1 = "#test1"
        channel2 = "#test2"
        
        # Add links to different channels
        self.db.save_link("https://channel1.com", "Channel 1 Link", "Desc", "user1", channel1)
        self.db.save_link("https://channel2.com", "Channel 2 Link", "Desc", "user2", channel2)
        
        # Each channel should only see its own links
        channel1_links = self.db.get_recent_links(channel1)
        channel2_links = self.db.get_recent_links(channel2)
        
        self.assertEqual(len(channel1_links), 1)
        self.assertEqual(len(channel2_links), 1)
        self.assertEqual(channel1_links[0]['url'], "https://channel1.com")
        self.assertEqual(channel2_links[0]['url'], "https://channel2.com")
    
    def test_malformed_data_handling(self):
        """Test handling of malformed or edge case data"""
        channel = "#test"
        
        # Test empty strings
        result1 = self.db.save_link("", "Title", "Desc", "user", channel)
        self.assertFalse(result1)
        
        # Test None values
        result2 = self.db.save_link("https://example.com", None, None, "user", channel)
        self.assertTrue(result2)  # Should handle None gracefully
        
        # Test very long strings
        long_title = "x" * 1000
        long_desc = "y" * 5000
        result3 = self.db.save_link("https://example-long.com", long_title, long_desc, "user", channel)
        self.assertTrue(result3)
    
    def test_database_error_handling(self):
        """Test graceful handling of database errors"""
        # Test with invalid database path - should raise exception during init
        with self.assertRaises((OSError, PermissionError)):
            invalid_db = Database("/invalid/path/database.db")
    
    def test_concurrent_access(self):
        """Test handling of concurrent database access"""
        import threading
        import time
        
        channel = "#test"
        results = []
        
        def save_links(start_num):
            for i in range(start_num, start_num + 5):
                url = f"https://example{i}.com"
                result = self.db.save_link(url, f"Title {i}", f"Desc {i}", f"user{i}", channel)
                results.append(result)
                time.sleep(0.001)  # Small delay
        
        # Start multiple threads
        threads = []
        for i in range(0, 20, 5):
            thread = threading.Thread(target=save_links, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All saves should succeed
        self.assertTrue(all(results))
        
        # Should have all links
        links = self.db.get_recent_links(channel, limit=25)
        self.assertEqual(len(links), 20)


class TestDatabaseSchema(unittest.TestCase):
    """Test database schema and migrations"""
    
    def test_schema_validation(self):
        """Test that database schema is correctly created"""
        temp_db = tempfile.NamedTemporaryFile(delete=False)
        temp_db.close()
        
        try:
            db = Database(temp_db.name)
            
            # Connect and check schema
            conn = sqlite3.connect(temp_db.name)
            cursor = conn.cursor()
            
            # Check links table structure
            cursor.execute("PRAGMA table_info(links)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            expected_columns = {
                'id': 'INTEGER',
                'url': 'TEXT',
                'title': 'TEXT',
                'description': 'TEXT',
                'user': 'TEXT',
                'channel': 'TEXT',
                'timestamp': 'REAL'
            }
            
            for col_name, col_type in expected_columns.items():
                self.assertIn(col_name, columns)
            
            conn.close()
            
        finally:
            os.unlink(temp_db.name)


if __name__ == "__main__":
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTest(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTest(loader.loadTestsFromTestCase(TestDatabaseSchema))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Database Tests Complete!")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print(f"\n❌ Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    if result.wasSuccessful():
        print(f"\n✅ All database tests passed!")
    else:
        print(f"\n⚠️  Some database tests failed!")
