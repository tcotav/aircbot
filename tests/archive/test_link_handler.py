#!/usr/bin/env python3
"""
Link Handler Test Suite for AircBot
Tests URL extraction, metadata fetching, and link processing
"""

import unittest
from unittest.mock import patch, Mock, MagicMock
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

from link_handler import LinkHandler

class TestLinkHandler(unittest.TestCase):
    """Test link handler functionality"""
    
    def setUp(self):
        """Set up test link handler"""
        self.handler = LinkHandler()
    
    def test_extract_urls_basic(self):
        """Test basic URL extraction from messages"""
        test_cases = [
            # Basic URLs
            ("Check out https://example.com", ["https://example.com"]),
            ("Visit http://test.org for more info", ["http://test.org"]),
            
            # Multiple URLs
            ("See https://site1.com and https://site2.com", 
             ["https://site1.com", "https://site2.com"]),
            
            # URLs with paths
            ("Read https://example.com/path/to/article", 
             ["https://example.com/path/to/article"]),
            
            # URLs with query parameters
            ("Search https://example.com/search?q=test&page=1", 
             ["https://example.com/search?q=test&page=1"]),
            
            # URLs with fragments
            ("Check https://example.com/page#section", 
             ["https://example.com/page#section"]),
        ]
        
        for message, expected_urls in test_cases:
            with self.subTest(message=message):
                extracted = self.handler.extract_urls(message)
                self.assertEqual(extracted, expected_urls)
    
    def test_extract_urls_edge_cases(self):
        """Test URL extraction edge cases"""
        test_cases = [
            # No URLs
            ("Just a regular message", []),
            ("Email addresses like user@example.com are not URLs", []),
            
            # URLs in different contexts
            ("(https://example.com)", ["https://example.com"]),
            ("[https://example.com]", ["https://example.com"]),
            ("Check out: https://example.com!", ["https://example.com"]),
            
            # Malformed URLs (should not be extracted)
            ("Not a URL: htp://broken.com", []),
            ("Also not: https://", []),
            
            # Very long URLs
            (f"Long URL: https://example.com/{'a' * 1000}", 
             [f"https://example.com/{'a' * 1000}"]),
        ]
        
        for message, expected_urls in test_cases:
            with self.subTest(message=message):
                extracted = self.handler.extract_urls(message)
                self.assertEqual(extracted, expected_urls)
    
    def test_extract_urls_case_insensitive(self):
        """Test that URL extraction handles case variations"""
        test_cases = [
            "Check out HTTPS://EXAMPLE.COM",
            "Visit HTTP://TEST.ORG",
            "See Https://Mixed-Case.Com",
        ]
        
        for message in test_cases:
            extracted = self.handler.extract_urls(message)
            self.assertEqual(len(extracted), 1)
            self.assertTrue(extracted[0].lower().startswith(('http://', 'https://')))
    
    @patch('requests.get')
    def test_get_link_metadata_success(self, mock_get):
        """Test successful metadata extraction"""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '''
        <html>
            <head>
                <title>Test Page Title</title>
                <meta name="description" content="This is a test page description">
            </head>
            <body>
                <h1>Test Content</h1>
            </body>
        </html>
        '''
        mock_get.return_value = mock_response
        
        title, description = self.handler.get_link_metadata("https://example.com")
        
        self.assertEqual(title, "Test Page Title")
        self.assertEqual(description, "This is a test page description")
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_get_link_metadata_no_title(self, mock_get):
        """Test metadata extraction when no title is present"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '<html><head></head><body>Content</body></html>'
        mock_get.return_value = mock_response
        
        title, description = self.handler.get_link_metadata("https://example.com")
        
        self.assertEqual(title, "https://example.com")  # Should fall back to URL
        self.assertEqual(description, "")
    
    @patch('requests.get')
    def test_get_link_metadata_no_description(self, mock_get):
        """Test metadata extraction when no description is present"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '<html><head><title>Test Title</title></head><body>Content</body></html>'
        mock_get.return_value = mock_response
        
        title, description = self.handler.get_link_metadata("https://example.com")
        
        self.assertEqual(title, "Test Title")
        self.assertEqual(description, "")
    
    @patch('requests.get')
    def test_get_link_metadata_malformed_html(self, mock_get):
        """Test metadata extraction with malformed HTML"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '<html><title>Broken HTML</title><head><body>No closing tags'
        mock_get.return_value = mock_response
        
        title, description = self.handler.get_link_metadata("https://example.com")
        
        self.assertEqual(title, "Broken HTML")  # BeautifulSoup should handle this
        self.assertEqual(description, "")
    
    @patch('requests.get')
    def test_get_link_metadata_timeout(self, mock_get):
        """Test metadata extraction with request timeout"""
        mock_get.side_effect = Timeout("Request timed out")
        
        title, description = self.handler.get_link_metadata("https://example.com")
        
        self.assertEqual(title, "https://example.com")  # Should fall back to URL
        self.assertEqual(description, "Could not fetch description")
    
    @patch('requests.get')
    def test_get_link_metadata_connection_error(self, mock_get):
        """Test metadata extraction with connection error"""
        mock_get.side_effect = ConnectionError("Connection failed")
        
        title, description = self.handler.get_link_metadata("https://example.com")
        
        self.assertEqual(title, "https://example.com")
        self.assertEqual(description, "Could not fetch description")
    
    @patch('requests.get')
    def test_get_link_metadata_http_error(self, mock_get):
        """Test metadata extraction with HTTP error (404, 500, etc.)"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        title, description = self.handler.get_link_metadata("https://example.com")
        
        self.assertEqual(title, "https://example.com")
        self.assertEqual(description, "Could not fetch description")
    
    @patch('requests.get')
    def test_get_link_metadata_encoding_issues(self, mock_get):
        """Test metadata extraction with encoding issues"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        # Simulate content with special characters
        mock_response.text = '''
        <html>
            <head>
                <title>Tëst Pågé with Ünïcödé</title>
                <meta name="description" content="Déscríptíön wïth spëcíål chåråctërs">
            </head>
        </html>
        '''
        mock_get.return_value = mock_response
        
        title, description = self.handler.get_link_metadata("https://example.com")
        
        self.assertEqual(title, "Tëst Pågé with Ünïcödé")
        self.assertEqual(description, "Déscríptíön wïth spëcíål chåråctërs")
    
    @patch('requests.get')
    def test_get_link_metadata_very_long_content(self, mock_get):
        """Test metadata extraction with very long title/description"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        long_title = "Very " * 100 + "Long Title"
        long_desc = "Very " * 200 + "Long Description"
        mock_response.text = f'''
        <html>
            <head>
                <title>{long_title}</title>
                <meta name="description" content="{long_desc}">
            </head>
        </html>
        '''
        mock_get.return_value = mock_response
        
        title, description = self.handler.get_link_metadata("https://example.com")
        
        # Should handle long content without crashing
        self.assertIsInstance(title, str)
        self.assertIsInstance(description, str)
        self.assertGreater(len(title), 0)
        self.assertGreater(len(description), 0)
    
    @patch('requests.get')
    def test_get_link_metadata_request_headers(self, mock_get):
        """Test that proper headers are sent with requests"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '<html><head><title>Test</title></head></html>'
        mock_get.return_value = mock_response
        
        self.handler.get_link_metadata("https://example.com")
        
        # Check that request was made with proper headers
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        
        # Should have timeout
        self.assertIn('timeout', call_args.kwargs)
        
        # Should have user agent header
        self.assertIn('headers', call_args.kwargs)
        headers = call_args.kwargs['headers']
        self.assertIn('User-Agent', headers)
    
    def test_url_validation(self):
        """Test URL validation logic"""
        valid_urls = [
            "https://example.com",
            "http://test.org",
            "https://subdomain.example.com",
            "https://example.com/path",
            "https://example.com:8080",
            "https://example.com/path?query=value",
            "https://example.com/path#fragment",
        ]
        
        invalid_urls = [
            "",
            "not-a-url",
            "ftp://example.com",  # Only HTTP/HTTPS should be supported
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                # Should not raise exception and should extract URL
                extracted = self.handler.extract_urls(f"Check out {url}")
                self.assertIn(url, extracted)
        
        for url in invalid_urls:
            with self.subTest(url=url):
                # Should not extract invalid URLs
                extracted = self.handler.extract_urls(f"Check out {url}")
                if url.startswith(('http://', 'https://')):
                    # Only HTTP/HTTPS URLs should be extracted
                    continue
                self.assertEqual(len(extracted), 0)
    
    @patch('requests.get')
    def test_concurrent_metadata_requests(self, mock_get):
        """Test handling of concurrent metadata requests"""
        import threading
        import time
        
        # Mock response that takes some time
        def slow_response(*args, **kwargs):
            time.sleep(0.1)  # Simulate slow network
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.text = '<html><head><title>Test</title></head></html>'
            return mock_response
        
        mock_get.side_effect = slow_response
        
        results = []
        
        def fetch_metadata(url):
            title, desc = self.handler.get_link_metadata(url)
            results.append((title, desc))
        
        # Start multiple concurrent requests
        threads = []
        urls = [f"https://example{i}.com" for i in range(5)]
        
        for url in urls:
            thread = threading.Thread(target=fetch_metadata, args=(url,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should complete successfully
        self.assertEqual(len(results), 5)
        for title, desc in results:
            self.assertEqual(title, "Test")


class TestLinkHandlerIntegration(unittest.TestCase):
    """Test link handler integration scenarios"""
    
    def setUp(self):
        """Set up test link handler"""
        self.handler = LinkHandler()
    
    def test_complete_link_processing_workflow(self):
        """Test complete workflow from message to metadata"""
        message = "Check out this great article: https://example.com/article"
        
        # Step 1: Extract URLs
        urls = self.handler.extract_urls(message)
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], "https://example.com/article")
        
        # Step 2: Get metadata (mocked)
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.text = '''
            <html>
                <head>
                    <title>Great Article Title</title>
                    <meta name="description" content="An informative article">
                </head>
            </html>
            '''
            mock_get.return_value = mock_response
            
            title, description = self.handler.get_link_metadata(urls[0])
            
            self.assertEqual(title, "Great Article Title")
            self.assertEqual(description, "An informative article")
    
    def test_multiple_links_in_message(self):
        """Test processing multiple links in a single message"""
        message = """
        Check these resources:
        - Documentation: https://docs.example.com
        - Source code: https://github.com/example/repo
        - Demo: https://demo.example.com/app
        """
        
        urls = self.handler.extract_urls(message)
        
        self.assertEqual(len(urls), 3)
        self.assertIn("https://docs.example.com", urls)
        self.assertIn("https://github.com/example/repo", urls)
        self.assertIn("https://demo.example.com/app", urls)
    
    @patch('requests.get')
    def test_social_media_links(self, mock_get):
        """Test handling of social media and special site links"""
        test_links = [
            ("https://twitter.com/user/status/123", "Twitter Post"),
            ("https://github.com/user/repo", "GitHub Repository"),
            ("https://stackoverflow.com/questions/123", "Stack Overflow Question"),
            ("https://youtube.com/watch?v=abc123", "YouTube Video"),
        ]
        
        for url, expected_title in test_links:
            with self.subTest(url=url):
                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_response.text = f'<html><head><title>{expected_title}</title></head></html>'
                mock_get.return_value = mock_response
                
                title, description = self.handler.get_link_metadata(url)
                self.assertEqual(title, expected_title)


if __name__ == "__main__":
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTest(loader.loadTestsFromTestCase(TestLinkHandler))
    suite.addTest(loader.loadTestsFromTestCase(TestLinkHandlerIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Link Handler Tests Complete!")
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
        print(f"\n✅ All link handler tests passed!")
    else:
        print(f"\n⚠️  Some link handler tests failed!")
