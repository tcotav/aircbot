import re
import requests
from bs4 import BeautifulSoup
import validators
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class LinkHandler:
    def __init__(self):
        # Regex pattern to find URLs in messages - improved to handle more cases
        self.url_pattern = re.compile(
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            re.IGNORECASE
        )
        
        # Headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def extract_urls(self, message: str) -> list:
        """Extract all URLs from a message"""
        urls = self.url_pattern.findall(message)
        # Clean up and validate URLs
        valid_urls = []
        for url in urls:
            # Remove trailing punctuation that might have been captured
            cleaned_url = url.rstrip('.,!;)?]')
            if validators.url(cleaned_url):
                valid_urls.append(cleaned_url)
        return valid_urls
    
    def get_link_metadata(self, url: str) -> Tuple[str, str]:
        """
        Fetch title and description from a URL
        Returns (title, description)
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Handle both .text and .content attributes
            content = response.text if hasattr(response, 'text') else response.content.decode('utf-8', errors='ignore')
            soup = BeautifulSoup(content, 'html.parser')
            
            # Get title
            title = url  # Default fallback to URL
            if soup.title:
                if soup.title.string:
                    title = soup.title.string.strip()
                elif soup.title.get_text():
                    # Handle cases where title has nested tags
                    title = soup.title.get_text().strip()
            # If no title found, keep the URL as fallback
            
            # Get description from meta tags
            description = ""
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and hasattr(meta_desc, 'get') and meta_desc.get('content'):
                description = meta_desc.get('content', '').strip()
            
            # If no meta description, try Open Graph
            if not description:
                og_desc = soup.find('meta', attrs={'property': 'og:description'})
                if og_desc and hasattr(og_desc, 'get') and og_desc.get('content'):
                    description = og_desc.get('content', '').strip()
            
            # Limit length
            if len(title) > 200:
                title = title[:197] + "..."
            if len(description) > 300:
                description = description[:297] + "..."
            
            return title, description
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch metadata for {url}: {e}")
            return url, "Could not fetch description"
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            return url, "Error processing link"
