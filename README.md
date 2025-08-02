# Ultimate Web Scraper for PDFs and Ebooks

A powerful, feature-rich Python web scraper designed to download PDFs and ebooks from multiple Islamic and educational websites. This scraper is optimized for VPS deployment with unlimited depth crawling, graceful interruption handling, and robust error recovery.

## 🌟 Features

### Core Capabilities
- **Unlimited Depth Crawling**: No limits on how deep the scraper can go into websites
- **No File Size Limits**: Downloads files of any size without restrictions
- **Multi-Website Support**: Handles 16 different websites with custom configurations
- **Graceful Interruption**: Saves all progress when interrupted (Ctrl+C)
- **State Persistence**: Resumes from where it left off after restart
- **Concurrent Downloads**: Multiple download threads for maximum efficiency

### Advanced Features
- **Smart File Detection**: Identifies PDFs and ebooks using multiple selectors
- **Arabic Content Support**: Special handling for Islamic websites with Arabic content
- **Retry Mechanism**: Automatic retry with exponential backoff for failed downloads
- **Progress Tracking**: Real-time progress bars and detailed statistics
- **Metadata Storage**: Saves detailed metadata for each downloaded file
- **Anti-Detection**: Random delays and realistic headers to avoid blocking
- **Unicode Support**: Proper handling of Arabic text and filenames

### Supported File Types
- **PDFs**: All PDF documents
- **Ebooks**: EPUB, MOBI, AZW3, DJVU formats
- **Documents**: DOC, DOCX, RTF, TXT files

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Sufficient disk space for downloads
- Stable internet connection

### Setup Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv web_scraper_env

# Activate virtual environment
# Windows:
web_scraper_env\Scripts\activate
# Linux/Mac:
source web_scraper_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## 📋 Supported Websites

The scraper is configured for these websites:

1. **shamela.ws** - Islamic library and books
2. **archive.org** - Internet Archive
3. **dorar.net** - Islamic knowledge portal
4. **waqfeya.net** - Islamic books and resources
5. **alukah.net** - Islamic articles and books
6. **islamqa.info/ar** - Islamic Q&A in Arabic
7. **islamweb.net** - Islamic web portal
8. **islamway.net** - Islamic way portal
9. **islamonline.net** - Islamic online resources
10. **ahlalhdeeth.com** - Islamic hadith resources
11. **openiti.org** - Open Islamic Texts Initiative
12. **mandumah.com** - Islamic research portal
13. **sdl.edu.sa** - Saudi Digital Library
14. **m.alfiqh.net** - Islamic jurisprudence
15. **read.tafsir.one** - Quranic interpretation
16. **getchaptrs.com** - Chapter-based reading

## 🎯 Usage

### Basic Usage
```bash
# Activate virtual environment (if using one)
web_scraper_env\Scripts\activate

# Run the scraper
python web_scraper.py
```

The scraper will automatically:
1. Create necessary directories (`downloads/`, `pdfs/`, `ebooks/`, `metadata/`)
2. Start scraping all configured websites
3. Download PDFs and ebooks to appropriate folders
4. Save progress every 10 pages visited
5. Display real-time statistics

### Directory Structure
```
downloads/
├── pdfs/           # Downloaded PDF files
├── ebooks/         # Downloaded ebook files
├── metadata/       # JSON metadata for each file
├── logs/           # Log files
└── scraper_state.pkl  # Progress state file
```

### Interruption and Resume
- Press `Ctrl+C` to gracefully stop the scraper
- All progress is automatically saved
- Restart the script to resume from where it left off

## ⚙️ Configuration

### Website-Specific Settings
Each website has custom configurations:
- **Selectors**: CSS selectors for finding download links
- **Delays**: Random delays to avoid detection
- **Retries**: Number of retry attempts for failed downloads
- **Headers**: Custom HTTP headers for each site

### Performance Tuning
- **Max Workers**: 5 concurrent download threads (optimized for stability)
- **Connection Limits**: 10-20 concurrent connections
- **Timeout**: 60 seconds for downloads
- **Retry Strategy**: 3 attempts with exponential backoff

## 📊 Statistics and Monitoring

The scraper provides detailed statistics:
- Total URLs visited
- Successful downloads
- Failed downloads
- Total data downloaded
- Runtime information

### Example Output
```
=== SCRAPING STATISTICS ===
Runtime: 0:16:45.747547
Visited URLs: 30
Successful Downloads: 2
Failed Downloads: 0
Total Size Downloaded: 0.95 MB
========================
```

## 🔧 Advanced Features

### State Management
- Automatic state saving every 10 pages
- Resume capability after interruption
- Detailed metadata for each file

### Error Handling
- Retry mechanism with exponential backoff
- Graceful handling of network errors
- Detailed error logging
- Connection reset handling

### Anti-Detection
- Random delays between requests
- Realistic browser headers
- Connection pooling
- SSL certificate handling

### Unicode Support
- Proper handling of Arabic text
- Safe filename generation
- UTF-8 encoding for logs and metadata

## 🛠️ Customization

### Adding New Websites
Edit the `_load_website_configs()` method to add new websites:

```python
'newwebsite.com': {
    'pdf_selectors': ['a[href*=".pdf"]', 'a[href*="download"]'],
    'ebook_selectors': ['a[href*=".epub"]', 'a[href*=".mobi"]'],
    'max_depth': None,
    'requires_selenium': False,
    'custom_headers': {'Accept-Language': 'en-US,en;q=0.9'},
    'delay': 1,
    'max_retries': 3,
    'special_handling': 'default'
}
```

### Modifying Download Behavior
- Adjust `max_workers` for concurrent downloads
- Modify `delay` values for different speeds
- Change retry settings in website configs

## 📝 Logging

The scraper creates detailed logs:
- `scraper.log`: Main application log (UTF-8 encoded)
- Console output: Real-time progress
- Metadata files: JSON files for each download

## ⚠️ Important Notes

### Legal and Ethical Considerations
- Respect website terms of service
- Use reasonable delays to avoid overwhelming servers
- Only download content you have permission to access
- Consider the impact on website resources

### System Requirements
- **RAM**: Minimum 2GB, recommended 4GB+
- **Storage**: Depends on content size (can be several GB)
- **Network**: Stable broadband connection
- **CPU**: Multi-core recommended for better performance

### Best Practices
1. Run during off-peak hours
2. Monitor system resources
3. Keep backups of downloaded content
4. Respect rate limits and delays
5. Use virtual environment for isolation

## 🐛 Troubleshooting

### Common Issues
1. **Connection Errors**: Check internet connection and firewall settings
2. **Permission Errors**: Ensure write permissions for download directory
3. **Memory Issues**: Reduce `max_workers` if system runs out of memory
4. **Disk Space**: Monitor available storage space
5. **Unicode Errors**: Ensure UTF-8 encoding support

### Virtual Environment Management
```bash
# Activate environment
web_scraper_env\Scripts\activate

# Deactivate environment
deactivate

# Recreate environment (if needed)
rmdir /s web_scraper_env
python -m venv web_scraper_env
```

### Debug Mode
Enable detailed logging by modifying the logging level in the script.

## 📄 License

This project is for educational purposes. Please ensure compliance with website terms of service and applicable laws.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

---

**Note**: This scraper is designed for educational and research purposes. Always respect website terms of service and use responsibly.