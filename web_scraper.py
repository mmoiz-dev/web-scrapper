#!/usr/bin/env python3
"""
Ultimate Web Scraper for PDFs and Ebooks
Advanced multi-website scraper with graceful interruption, unlimited depth, and robust error handling
"""

import os
import sys
import time
import signal
import logging
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Set, List, Dict, Optional, Tuple
import json
import hashlib
from datetime import datetime
import threading
from queue import Queue
import validators
from tqdm import tqdm
import pickle
import random

# Third-party imports
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class GracefulInterrupt:
    """Handle graceful interruption of the scraper"""
    def __init__(self):
        self.interrupted = False
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logger.info(f"Received interrupt signal {signum}. Gracefully shutting down...")
        self.interrupted = True

class AdvancedWebScraper:
    """Ultimate web scraper class with advanced features"""
    
    def __init__(self, base_dir: str = "downloads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.pdf_dir = self.base_dir / "pdfs"
        self.ebook_dir = self.base_dir / "ebooks"
        self.metadata_dir = self.base_dir / "metadata"
        self.logs_dir = self.base_dir / "logs"
        
        for dir_path in [self.pdf_dir, self.ebook_dir, self.metadata_dir, self.logs_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # State management
        self.visited_urls: Set[str] = set()
        self.downloaded_files: Set[str] = set()
        self.failed_downloads: Set[str] = set()
        self.retry_queue: Queue = Queue()
        
        # Session management with advanced settings
        self.session = self._create_session()
        
        # Website-specific configurations
        self.website_configs = self._load_website_configs()
        
        # Interruption handling
        self.interrupt_handler = GracefulInterrupt()
        
        # Threading
        self.download_queue = Queue()
        self.max_workers = 5  # Reduced for better stability
        
        # Statistics
        self.stats = {
            'total_downloads': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'total_size_downloaded': 0,
            'start_time': datetime.now()
        }
        
        # Load previous state
        self._load_state()
    
    def _create_session(self) -> requests.Session:
        """Create a robust requests session with advanced settings"""
        session = requests.Session()
        
        # Advanced headers to avoid detection
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Advanced retry strategy with longer timeouts
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _load_website_configs(self) -> Dict[str, Dict]:
        """Load advanced website-specific scraping configurations"""
        return {
            'shamela.ws': {
                'pdf_selectors': [
                    'a[href*=".pdf"]', 'a[href*="download"]', 'a[href*="تحميل"]',
                    'a[href*="PDF"]', 'a[href*="pdf"]', 'a[onclick*="pdf"]'
                ],
                'ebook_selectors': [
                    'a[href*=".epub"]', 'a[href*=".mobi"]', 'a[href*=".txt"]',
                    'a[href*=".doc"]', 'a[href*=".docx"]', 'a[href*=".rtf"]'
                ],
                'max_depth': None,
                'requires_selenium': False,
                'custom_headers': {'Accept-Language': 'ar,en;q=0.9'},
                'delay': 0.5,
                'max_retries': 3,
                'special_handling': 'islamic_arabic'
            },
            'archive.org': {
                'pdf_selectors': [
                    'a[href*=".pdf"]', 'a[href*="download"]', 'a[href*="PDF"]',
                    'a[href*="pdf"]', 'a[data-format="pdf"]', 'a[title*="PDF"]'
                ],
                'ebook_selectors': [
                    'a[href*=".epub"]', 'a[href*=".mobi"]', 'a[href*=".txt"]',
                    'a[href*=".doc"]', 'a[href*=".docx"]', 'a[data-format="epub"]'
                ],
                'max_depth': None,
                'requires_selenium': False,
                'delay': 1,
                'max_retries': 5,
                'special_handling': 'archive_org'
            },
            'dorar.net': {
                'pdf_selectors': [
                    'a[href*=".pdf"]', 'a[href*="download"]', 'a[href*="تحميل"]',
                    'a[href*="PDF"]', 'a[href*="pdf"]', 'a[onclick*="pdf"]'
                ],
                'ebook_selectors': [
                    'a[href*=".epub"]', 'a[href*=".mobi"]', 'a[href*=".txt"]',
                    'a[href*=".doc"]', 'a[href*=".docx"]', 'a[href*=".rtf"]'
                ],
                'max_depth': None,
                'requires_selenium': False,
                'custom_headers': {'Accept-Language': 'ar,en;q=0.9'},
                'delay': 0.5,
                'max_retries': 3,
                'special_handling': 'islamic_arabic'
            },
            'waqfeya.net': {
                'pdf_selectors': [
                    'a[href*=".pdf"]', 'a[href*="download"]', 'a[href*="تحميل"]',
                    'a[href*="PDF"]', 'a[href*="pdf"]', 'a[onclick*="pdf"]'
                ],
                'ebook_selectors': [
                    'a[href*=".epub"]', 'a[href*=".mobi"]', 'a[href*=".txt"]',
                    'a[href*=".doc"]', 'a[href*=".docx"]', 'a[href*=".rtf"]'
                ],
                'max_depth': None,
                'requires_selenium': False,
                'custom_headers': {'Accept-Language': 'ar,en;q=0.9'},
                'delay': 0.5,
                'max_retries': 3,
                'special_handling': 'islamic_arabic'
            },
            'alukah.net': {
                'pdf_selectors': [
                    'a[href*=".pdf"]', 'a[href*="download"]', 'a[href*="تحميل"]',
                    'a[href*="PDF"]', 'a[href*="pdf"]', 'a[onclick*="pdf"]'
                ],
                'ebook_selectors': [
                    'a[href*=".epub"]', 'a[href*=".mobi"]', 'a[href*=".txt"]',
                    'a[href*=".doc"]', 'a[href*=".docx"]', 'a[href*=".rtf"]'
                ],
                'max_depth': None,
                'requires_selenium': False,
                'custom_headers': {'Accept-Language': 'ar,en;q=0.9'},
                'delay': 0.5,
                'max_retries': 3,
                'special_handling': 'islamic_arabic'
            },
            'islamqa.info': {
                'pdf_selectors': [
                    'a[href*=".pdf"]', 'a[href*="download"]', 'a[href*="تحميل"]',
                    'a[href*="PDF"]', 'a[href*="pdf"]', 'a[onclick*="pdf"]'
                ],
                'ebook_selectors': [
                    'a[href*=".epub"]', 'a[href*=".mobi"]', 'a[href*=".txt"]',
                    'a[href*=".doc"]', 'a[href*=".docx"]', 'a[href*=".rtf"]'
                ],
                'max_depth': None,
                'requires_selenium': False,
                'custom_headers': {'Accept-Language': 'ar,en;q=0.9'},
                'delay': 0.5,
                'max_retries': 3,
                'special_handling': 'islamic_arabic'
            },
            'islamweb.net': {
                'pdf_selectors': [
                    'a[href*=".pdf"]', 'a[href*="download"]', 'a[href*="تحميل"]',
                    'a[href*="PDF"]', 'a[href*="pdf"]', 'a[onclick*="pdf"]'
                ],
                'ebook_selectors': [
                    'a[href*=".epub"]', 'a[href*=".mobi"]', 'a[href*=".txt"]',
                    'a[href*=".doc"]', 'a[href*=".docx"]', 'a[href*=".rtf"]'
                ],
                'max_depth': None,
                'requires_selenium': False,
                'custom_headers': {'Accept-Language': 'ar,en;q=0.9'},
                'delay': 0.5,
                'max_retries': 3,
                'special_handling': 'islamic_arabic'
            },
            'islamway.net': {
                'pdf_selectors': [
                    'a[href*=".pdf"]', 'a[href*="download"]', 'a[href*="تحميل"]',
                    'a[href*="PDF"]', 'a[href*="pdf"]', 'a[onclick*="pdf"]'
                ],
                'ebook_selectors': [
                    'a[href*=".epub"]', 'a[href*=".mobi"]', 'a[href*=".txt"]',
                    'a[href*=".doc"]', 'a[href*=".docx"]', 'a[href*=".rtf"]'
                ],
                'max_depth': None,
                'requires_selenium': False,
                'custom_headers': {'Accept-Language': 'ar,en;q=0.9'},
                'delay': 0.5,
                'max_retries': 3,
                'special_handling': 'islamic_arabic'
            },
            'islamonline.net': {
                'pdf_selectors': [
                    'a[href*=".pdf"]', 'a[href*="download"]', 'a[href*="تحميل"]',
                    'a[href*="PDF"]', 'a[href*="pdf"]', 'a[onclick*="pdf"]'
                ],
                'ebook_selectors': [
                    'a[href*=".epub"]', 'a[href*=".mobi"]', 'a[href*=".txt"]',
                    'a[href*=".doc"]', 'a[href*=".docx"]', 'a[href*=".rtf"]'
                ],
                'max_depth': None,
                'requires_selenium': False,
                'custom_headers': {'Accept-Language': 'ar,en;q=0.9'},
                'delay': 0.5,
                'max_retries': 3,
                'special_handling': 'islamic_arabic'
            },
            'ahlalhdeeth.com': {
                'pdf_selectors': [
                    'a[href*=".pdf"]', 'a[href*="download"]', 'a[href*="تحميل"]',
                    'a[href*="PDF"]', 'a[href*="pdf"]', 'a[onclick*="pdf"]'
                ],
                'ebook_selectors': [
                    'a[href*=".epub"]', 'a[href*=".mobi"]', 'a[href*=".txt"]',
                    'a[href*=".doc"]', 'a[href*=".docx"]', 'a[href*=".rtf"]'
                ],
                'max_depth': None,
                'requires_selenium': False,
                'custom_headers': {'Accept-Language': 'ar,en;q=0.9'},
                'delay': 0.5,
                'max_retries': 3,
                'special_handling': 'islamic_arabic'
            },
            'openiti.org': {
                'pdf_selectors': [
                    'a[href*=".pdf"]', 'a[href*="download"]', 'a[href*="تحميل"]',
                    'a[href*="PDF"]', 'a[href*="pdf"]', 'a[onclick*="pdf"]'
                ],
                'ebook_selectors': [
                    'a[href*=".epub"]', 'a[href*=".mobi"]', 'a[href*=".txt"]',
                    'a[href*=".doc"]', 'a[href*=".docx"]', 'a[href*=".rtf"]'
                ],
                'max_depth': None,
                'requires_selenium': False,
                'custom_headers': {'Accept-Language': 'ar,en;q=0.9'},
                'delay': 0.5,
                'max_retries': 3,
                'special_handling': 'islamic_arabic'
            },
            'mandumah.com': {
                'pdf_selectors': [
                    'a[href*=".pdf"]', 'a[href*="download"]', 'a[href*="تحميل"]',
                    'a[href*="PDF"]', 'a[href*="pdf"]', 'a[onclick*="pdf"]'
                ],
                'ebook_selectors': [
                    'a[href*=".epub"]', 'a[href*=".mobi"]', 'a[href*=".txt"]',
                    'a[href*=".doc"]', 'a[href*=".docx"]', 'a[href*=".rtf"]'
                ],
                'max_depth': None,
                'requires_selenium': False,
                'custom_headers': {'Accept-Language': 'ar,en;q=0.9'},
                'delay': 0.5,
                'max_retries': 3,
                'special_handling': 'islamic_arabic'
            },
            'sdl.edu.sa': {
                'pdf_selectors': [
                    'a[href*=".pdf"]', 'a[href*="download"]', 'a[href*="تحميل"]',
                    'a[href*="PDF"]', 'a[href*="pdf"]', 'a[onclick*="pdf"]'
                ],
                'ebook_selectors': [
                    'a[href*=".epub"]', 'a[href*=".mobi"]', 'a[href*=".txt"]',
                    'a[href*=".doc"]', 'a[href*=".docx"]', 'a[href*=".rtf"]'
                ],
                'max_depth': None,
                'requires_selenium': False,
                'custom_headers': {'Accept-Language': 'ar,en;q=0.9'},
                'delay': 0.5,
                'max_retries': 3,
                'special_handling': 'islamic_arabic'
            },
            'alfiqh.net': {
                'pdf_selectors': [
                    'a[href*=".pdf"]', 'a[href*="download"]', 'a[href*="تحميل"]',
                    'a[href*="PDF"]', 'a[href*="pdf"]', 'a[onclick*="pdf"]'
                ],
                'ebook_selectors': [
                    'a[href*=".epub"]', 'a[href*=".mobi"]', 'a[href*=".txt"]',
                    'a[href*=".doc"]', 'a[href*=".docx"]', 'a[href*=".rtf"]'
                ],
                'max_depth': None,
                'requires_selenium': False,
                'custom_headers': {'Accept-Language': 'ar,en;q=0.9'},
                'delay': 0.5,
                'max_retries': 3,
                'special_handling': 'islamic_arabic'
            },
            'tafsir.one': {
                'pdf_selectors': [
                    'a[href*=".pdf"]', 'a[href*="download"]', 'a[href*="تحميل"]',
                    'a[href*="PDF"]', 'a[href*="pdf"]', 'a[onclick*="pdf"]'
                ],
                'ebook_selectors': [
                    'a[href*=".epub"]', 'a[href*=".mobi"]', 'a[href*=".txt"]',
                    'a[href*=".doc"]', 'a[href*=".docx"]', 'a[href*=".rtf"]'
                ],
                'max_depth': None,
                'requires_selenium': False,
                'custom_headers': {'Accept-Language': 'ar,en;q=0.9'},
                'delay': 0.5,
                'max_retries': 3,
                'special_handling': 'islamic_arabic'
            },
            'getchaptrs.com': {
                'pdf_selectors': [
                    'a[href*=".pdf"]', 'a[href*="download"]', 'a[href*="تحميل"]',
                    'a[href*="PDF"]', 'a[href*="pdf"]', 'a[onclick*="pdf"]'
                ],
                'ebook_selectors': [
                    'a[href*=".epub"]', 'a[href*=".mobi"]', 'a[href*=".txt"]',
                    'a[href*=".doc"]', 'a[href*=".docx"]', 'a[href*=".rtf"]'
                ],
                'max_depth': None,
                'requires_selenium': False,
                'custom_headers': {'Accept-Language': 'ar,en;q=0.9'},
                'delay': 0.5,
                'max_retries': 3,
                'special_handling': 'islamic_arabic'
            }
        }
    
    def _load_state(self):
        """Load previous scraping state from files"""
        state_file = self.base_dir / "scraper_state.pkl"
        if state_file.exists():
            try:
                with open(state_file, 'rb') as f:
                    state = pickle.load(f)
                    self.visited_urls = state.get('visited_urls', set())
                    self.downloaded_files = state.get('downloaded_files', set())
                    self.failed_downloads = state.get('failed_downloads', set())
                    self.stats = state.get('stats', self.stats)
                logger.info(f"Loaded state: {len(self.visited_urls)} visited URLs, {len(self.downloaded_files)} downloaded files")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
    
    def _save_state(self):
        """Save current scraping state to files"""
        state_file = self.base_dir / "scraper_state.pkl"
        try:
            state = {
                'visited_urls': self.visited_urls,
                'downloaded_files': self.downloaded_files,
                'failed_downloads': self.failed_downloads,
                'stats': self.stats,
                'timestamp': datetime.now().isoformat()
            }
            with open(state_file, 'wb') as f:
                pickle.dump(state, f)
            logger.info("State saved successfully")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def _get_website_config(self, url: str) -> Dict:
        """Get configuration for a specific website"""
        domain = urlparse(url).netloc.lower()
        for site_domain, config in self.website_configs.items():
            if site_domain in domain:
                return config
        return self.website_configs.get('default', {})
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and belongs to target websites"""
        if not validators.url(url):
            return False
        
        domain = urlparse(url).netloc.lower()
        return any(site_domain in domain for site_domain in self.website_configs.keys())
    
    def _get_file_extension(self, url: str, content_type: str = None) -> str:
        """Extract file extension from URL or content-type"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Common file extensions
        extensions = ['.pdf', '.epub', '.mobi', '.txt', '.doc', '.docx', '.rtf', '.azw3', '.djvu']
        for ext in extensions:
            if ext in path:
                return ext
        
        # Check content-type if no extension in URL
        if content_type:
            if 'pdf' in content_type.lower():
                return '.pdf'
            elif 'epub' in content_type.lower():
                return '.epub'
            elif 'mobi' in content_type.lower():
                return '.mobi'
            elif 'text' in content_type.lower():
                return '.txt'
        
        return '.pdf'  # Default to PDF
    
    def _generate_filename(self, url: str, title: str = None) -> str:
        """Generate a safe filename from URL and title"""
        if title:
            # Clean title for filename - handle Arabic text better
            import unicodedata
            # Normalize unicode characters
            title = unicodedata.normalize('NFKD', title)
            # Keep only alphanumeric, spaces, and some safe characters
            title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            title = title[:50]  # Limit length to avoid issues
        else:
            title = "untitled"
        
        # Add hash to ensure uniqueness
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        ext = self._get_file_extension(url)
        
        return f"{title}_{url_hash}{ext}"
    
    def _download_file_sync(self, url: str, title: str = None) -> bool:
        """Download a file synchronously with retry mechanism"""
        config = self._get_website_config(url)
        max_retries = config.get('max_retries', 3)
        
        for attempt in range(max_retries):
            try:
                # Check if already downloaded
                filename = self._generate_filename(url, title)
                file_path = self.pdf_dir / filename if self._get_file_extension(url) == '.pdf' else self.ebook_dir / filename
                
                if file_path.exists():
                    logger.info(f"File already exists: {filename}")
                    self.downloaded_files.add(url)
                    return True
                
                # Download file with custom headers
                headers = self.session.headers.copy()
                if 'custom_headers' in config:
                    headers.update(config['custom_headers'])
                
                response = self.session.get(url, stream=True, timeout=60, headers=headers)
                response.raise_for_status()
                
                # Get file size
                file_size = int(response.headers.get('content-length', 0))
                content_type = response.headers.get('content-type', '')
                
                # Update extension based on content-type
                ext = self._get_file_extension(url, content_type)
                if ext != self._get_file_extension(url):
                    filename = filename.rsplit('.', 1)[0] + ext
                    file_path = self.pdf_dir / filename if ext == '.pdf' else self.ebook_dir / filename
                
                # Download with progress bar
                downloaded_size = 0
                with open(file_path, 'wb') as f:
                    with tqdm(total=file_size, unit='B', unit_scale=True, desc=filename) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                pbar.update(len(chunk))
                
                # Save metadata
                metadata = {
                    'url': url,
                    'title': title,
                    'filename': filename,
                    'file_size': file_size,
                    'downloaded_size': downloaded_size,
                    'download_time': datetime.now().isoformat(),
                    'content_type': content_type,
                    'headers': dict(response.headers)
                }
                
                metadata_file = self.metadata_dir / f"{filename}.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                self.downloaded_files.add(url)
                self.stats['successful_downloads'] += 1
                self.stats['total_size_downloaded'] += downloaded_size
                logger.info(f"Successfully downloaded: {filename} ({downloaded_size} bytes)")
                return True
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(1, 5))  # Random delay between retries
                else:
                    logger.error(f"Failed to download {url} after {max_retries} attempts")
                    self.failed_downloads.add(url)
                    self.stats['failed_downloads'] += 1
                    return False
        
        return False
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from a page with advanced filtering"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href:
                absolute_url = urljoin(base_url, href)
                if self._is_valid_url(absolute_url):
                    # Filter out common non-content URLs
                    if not any(skip in absolute_url.lower() for skip in [
                        'javascript:', 'mailto:', 'tel:', '#', 'logout', 'login', 'register',
                        'search', 'admin', 'cart', 'checkout', 'account', 'profile'
                    ]):
                        links.append(absolute_url)
        return links
    
    def _extract_download_links(self, soup: BeautifulSoup, base_url: str, config: Dict) -> List[Tuple[str, str]]:
        """Extract download links for PDFs and ebooks with advanced selectors"""
        downloads = []
        
        # Extract PDF links
        for selector in config.get('pdf_selectors', []):
            for link in soup.select(selector):
                href = link.get('href')
                if href:
                    absolute_url = urljoin(base_url, href)
                    title = link.get_text(strip=True) or link.get('title', '') or link.get('alt', '')
                    downloads.append((absolute_url, title))
        
        # Extract ebook links
        for selector in config.get('ebook_selectors', []):
            for link in soup.select(selector):
                href = link.get('href')
                if href:
                    absolute_url = urljoin(base_url, href)
                    title = link.get_text(strip=True) or link.get('title', '') or link.get('alt', '')
                    downloads.append((absolute_url, title))
        
        # Additional extraction for special handling
        special_handling = config.get('special_handling', '')
        if special_handling == 'islamic_arabic':
            # Look for Arabic download links
            for link in soup.find_all('a'):
                text = link.get_text(strip=True).lower()
                if any(keyword in text for keyword in ['تحميل', 'pdf', 'download', 'كتاب', 'كتاب']):
                    href = link.get('href')
                    if href:
                        absolute_url = urljoin(base_url, href)
                        title = link.get_text(strip=True)
                        downloads.append((absolute_url, title))
        
        return downloads
    
    def _scrape_page(self, url: str, depth: int = 0) -> List[str]:
        """Scrape a single page for links and downloads with advanced error handling"""
        if self.interrupt_handler.interrupted:
            return []
        
        if url in self.visited_urls:
            return []
        
        self.visited_urls.add(url)
        config = self._get_website_config(url)
        
        try:
            # Add custom headers if specified
            headers = self.session.headers.copy()
            if 'custom_headers' in config:
                headers.update(config['custom_headers'])
            
            # Add random delay to avoid detection
            delay = config.get('delay', 1)
            if delay > 0:
                time.sleep(random.uniform(delay * 0.5, delay * 1.5))
            
            # Try to get the page with better error handling
            try:
                response = self.session.get(url, headers=headers, timeout=60)
                response.raise_for_status()
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error for {url}: {e}")
                return []
            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout for {url}: {e}")
                return []
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for {url}: {e}")
                return []
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type.lower():
                logger.info(f"Skipping non-HTML content: {url}")
                return []
            
            # Use html5lib parser instead of lxml
            soup = BeautifulSoup(response.content, 'html5lib')
            
            # Extract download links
            downloads = self._extract_download_links(soup, url, config)
            for download_url, title in downloads:
                if download_url not in self.downloaded_files and download_url not in self.failed_downloads:
                    self.download_queue.put((download_url, title))
            
            # Extract navigation links
            links = self._extract_links(soup, url)
            
            return links
            
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return []
    
    def _download_worker(self):
        """Worker thread for downloading files"""
        while True:
            try:
                download_url, title = self.download_queue.get(timeout=5)
                if download_url == "STOP":
                    break
                
                self._download_file_sync(download_url, title)
                
            except Exception as e:
                if "Empty" in str(e):
                    # Queue timeout, continue waiting
                    continue
                elif "STOP" in str(download_url):
                    # Worker should stop
                    break
                else:
                    logger.error(f"Download worker error: {e}")
                    # Don't break, just continue to next item
                    continue
    
    def scrape_website(self, start_url: str, max_depth: int = None):
        """Scrape a website starting from the given URL with unlimited depth"""
        logger.info(f"Starting to scrape: {start_url}")
        
        # Start download workers
        download_threads = []
        for _ in range(self.max_workers):
            thread = threading.Thread(target=self._download_worker, daemon=True)
            thread.start()
            download_threads.append(thread)
        
        try:
            urls_to_visit = [(start_url, 0)]
            
            while urls_to_visit and not self.interrupt_handler.interrupted:
                current_url, depth = urls_to_visit.pop(0)
                
                # Check depth limit (None means unlimited)
                if max_depth is not None and depth > max_depth:
                    continue
                
                logger.info(f"Scraping {current_url} (depth: {depth})")
                
                # Scrape current page
                new_links = self._scrape_page(current_url, depth)
                
                # Add new links to visit
                for link in new_links:
                    if link not in self.visited_urls:
                        urls_to_visit.append((link, depth + 1))
                
                # Save state periodically
                if len(self.visited_urls) % 10 == 0:
                    self._save_state()
                
                # Print statistics
                if len(self.visited_urls) % 50 == 0:
                    self._print_statistics()
        
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            # Stop download workers
            for _ in range(self.max_workers):
                self.download_queue.put(("STOP", ""))
            
            # Wait for threads to finish
            for thread in download_threads:
                thread.join(timeout=5)
            
            self._save_state()
            self._print_statistics()
            logger.info("Scraping completed")
    
    def _print_statistics(self):
        """Print current scraping statistics"""
        runtime = datetime.now() - self.stats['start_time']
        logger.info(f"""
=== SCRAPING STATISTICS ===
Runtime: {runtime}
Visited URLs: {len(self.visited_urls)}
Successful Downloads: {self.stats['successful_downloads']}
Failed Downloads: {self.stats['failed_downloads']}
Total Size Downloaded: {self.stats['total_size_downloaded'] / (1024*1024):.2f} MB
========================
        """)
    
    def scrape_all_websites(self, websites: List[str]):
        """Scrape all provided websites"""
        logger.info(f"Starting to scrape {len(websites)} websites")
        
        for website in websites:
            if self.interrupt_handler.interrupted:
                break
            
            try:
                logger.info(f"Scraping website: {website}")
                self.scrape_website(website)
                
                # Save state after each website
                self._save_state()
                
            except Exception as e:
                logger.error(f"Failed to scrape {website}: {e}")
                continue
        
        logger.info("All websites scraped")
        self._print_statistics()

def main():
    """Main function to run the scraper"""
    # List of websites to scrape
    websites = [
        "https://shamela.ws",
        "https://archive.org",
        "https://dorar.net",
        "https://waqfeya.net",
        "https://alukah.net",
        "https://islamqa.info/ar",
        "https://islamweb.net",
        "https://islamway.net",
        "https://islamonline.net",
        "https://ahlalhdeeth.com",
        "https://openiti.org",
        "https://mandumah.com",
        "https://sdl.edu.sa/SDLPortal/ar/A-ZAll.aspx",
        "https://m.alfiqh.net",
        "https://read.tafsir.one/ibn-aashoor",
        "https://www.getchaptrs.com"
    ]
    
    # Create scraper instance
    scraper = AdvancedWebScraper()
    
    try:
        # Start scraping all websites
        scraper.scrape_all_websites(websites)
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, saving state...")
        scraper._save_state()
        scraper._print_statistics()
        logger.info("State saved. Exiting gracefully.")
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        scraper._save_state()
        raise

if __name__ == "__main__":
    main() 