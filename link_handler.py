import re
import requests
from bs4 import BeautifulSoup
import validators
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class LinkHandler:
    def __init__(self):
        # Regex pattern to find URLs in messages
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        # Headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def extract_urls(self, message: str) -> list:
        """Extract all URLs from a message"""
        urls = self.url_pattern.findall(message)
        # Validate URLs
        valid_urls = []
        for url in urls:
            if validators.url(url):
                valid_urls.append(url)
        return valid_urls
    
    def get_link_metadata(self, url: str) -> Tuple[str, str]:
        """
        Fetch title and description from a URL
        Returns (title, description)
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get title
            title = "No title"
            if soup.title:
                title = soup.title.string.strip()
            
            # Get description from meta tags
            description = ""
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '').strip()
            
            # If no meta description, try Open Graph
            if not description:
                og_desc = soup.find('meta', attrs={'property': 'og:description'})
                if og_desc:
                    description = og_desc.get('content', '').strip()
            
            # Limit length
            if len(title) > 200:
                title = title[:197] + "..."
            if len(description) > 300:
                description = description[:297] + "..."
            
            return title, description
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch metadata for {url}: {e}")
            return "Link", "Could not fetch description"
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            return "Link", "Error processing link"
