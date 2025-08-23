#!/usr/bin/env python3
"""
🔍 Backend Organization Verification Script
This script verifies that all paths are correctly organized after reorganization.
"""

import os
import sys
import re
from pathlib import Path

def test_imports():
    """Test that all import paths work correctly"""
    print("🔍 Testing import paths...")
    
    # Add backend directory to path
    backend_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(backend_dir / 'src'))
    
    results = []
    
    # Test utils imports
    try:
        from utils.logger import get_logger
        results.append("✅ utils.logger import - OK")
    except ImportError as e:
        results.append(f"❌ utils.logger import - FAILED: {e}")
    
    try:
        from utils.backup_manager import BackupManager
        results.append("✅ utils.backup_manager import - OK")
    except ImportError as e:
        results.append(f"❌ utils.backup_manager import - FAILED: {e}")
    
    try:
        from utils.unicode_helper import safe_print
        results.append("✅ utils.unicode_helper import - OK")
    except ImportError as e:
        results.append(f"❌ utils.unicode_helper import - FAILED: {e}")
    
    # Test scraper import (will fail due to dependencies but should find the module)
    try:
        from scrapers.crawl4ai_scraper import EnhancedCyberSecurityNewsScraper
        results.append("✅ scrapers.crawl4ai_scraper import - OK")
    except ImportError as e:
        if "crawl4ai" in str(e):
            results.append("✅ scrapers.crawl4ai_scraper path - OK (dependency missing is expected)")
        else:
            results.append(f"❌ scrapers.crawl4ai_scraper import - FAILED: {e}")
    
    return results

def check_file_structure():
    """Check that all important files are in their correct locations"""
    print("📁 Checking file structure...")
    
    backend_dir = Path(__file__).parent.parent
    results = []
    
    # Core files
    files_to_check = [
        ('main_launch.py', backend_dir / 'main_launch.py'),
        ('FastAPI app', backend_dir / 'api' / 'cybersecurity_fastapi.py'),
        ('Scraper', backend_dir / 'src' / 'scrapers' / 'crawl4ai_scraper.py'),
        ('AI Summarizer', backend_dir / 'Ai' / 'enhanced_ai_summarizer.py'),
        ('Docker Compose', backend_dir / 'docker' / 'docker-compose.automated.yml'),
        ('Automation Service', backend_dir / 'automation' / 'automation_service.py'),
        ('Test Scripts', backend_dir / 'scripts' / 'debug_extraction.py'),
    ]
    
    for name, file_path in files_to_check:
        if file_path.exists():
            results.append(f"✅ {name}: {file_path.relative_to(backend_dir)}")
        else:
            results.append(f"❌ {name}: MISSING - {file_path.relative_to(backend_dir)}")
    
    return results

def check_organized_structure():
    """Check that the organized folder structure is correct"""
    print("🗂️ Checking organized structure...")
    
    backend_dir = Path(__file__).parent.parent
    results = []
    
    # Expected organized directories
    organized_dirs = [
        ('automation/', backend_dir / 'automation'),
        ('api/', backend_dir / 'api'),
        ('scripts/', backend_dir / 'scripts'),
        ('docker/', backend_dir / 'docker'),
        ('src/scrapers/', backend_dir / 'src' / 'scrapers'),
        ('src/utils/', backend_dir / 'src' / 'utils'),
        ('Ai/', backend_dir / 'Ai'),
        ('data/alerts/', backend_dir / 'data' / 'alerts'),
        ('data/backup/', backend_dir / 'data' / 'backup'),
    ]
    
    for name, dir_path in organized_dirs:
        if dir_path.exists() and dir_path.is_dir():
            if name.startswith('data/'):
                file_count = len(list(dir_path.glob('*')))
                results.append(f"✅ {name}: {file_count} files")
            else:
                file_count = len(list(dir_path.glob('*.py')))
                results.append(f"✅ {name}: {file_count} Python files")
        else:
            results.append(f"❌ {name}: MISSING")
    
    return results

def check_data_folder_structure():
    """Check that the data folder is properly organized"""
    print("📊 Checking data folder organization...")
    
    backend_dir = Path(__file__).parent.parent
    data_dir = backend_dir / 'data'
    results = []
    
    # Expected core files in data directory
    core_files = [
        'summarized_news_hf.json',
        'News_today_20250818.json',  # Dynamic date
        'url_final_summarized.txt',
        'url_scraped.txt'
    ]
    
    # Check core files (allowing dynamic date in News file)
    for file_pattern in core_files:
        if 'News_today_' in file_pattern:
            # Check for any News_today_*.json file
            news_files = list(data_dir.glob('News_today_*.json'))
            if news_files:
                results.append(f"✅ News file: {news_files[0].name}")
            else:
                results.append("❌ News_today_*.json: MISSING")
        else:
            file_path = data_dir / file_pattern
            if file_path.exists():
                results.append(f"✅ Core file: {file_pattern}")
            else:
                results.append(f"❌ Core file: {file_pattern} MISSING")
    
    # Check alerts folder
    alerts_dir = data_dir / 'alerts'
    if alerts_dir.exists():
        alert_files = list(alerts_dir.glob('*'))
        results.append(f"✅ Alerts folder: {len(alert_files)} files")
    else:
        results.append("❌ Alerts folder: MISSING")
    
    # Check backup folder
    backup_dir = data_dir / 'backup'
    if backup_dir.exists():
        backup_files = list(backup_dir.glob('*'))
        results.append(f"✅ Backup folder: {len(backup_files)} files")
    else:
        results.append("❌ Backup folder: MISSING")
    
    # Check that only expected items are in data root
    data_items = list(data_dir.glob('*'))
    expected_items = {'alerts', 'backup', 'cybersecurity_news_live.json', 'summarized_news_hf.json', 'url_final_summarized.txt', 'url_scraped.txt'}
    # Add dynamic news file
    for item in data_items:
        if item.is_file() and item.name.startswith('News_today_') and item.name.endswith('.json'):
            expected_items.add(item.name)
            break
    
    actual_items = {item.name for item in data_items}
    unexpected_items = actual_items - expected_items
    
    if not unexpected_items:
        results.append("✅ Data folder: Clean (only expected files)")
    else:
        results.append(f"⚠️ Data folder: Contains unexpected items: {', '.join(unexpected_items)}")
    
    # Check backup folder for proper structure (no excessive timestamped files)
    backup_files = list(backup_dir.glob('*cybersecurity_news_live*.json'))
    # Properly identify timestamped files: should have YYYYMMDD_HHMMSS pattern
    timestamped_files = [f for f in backup_files if re.search(r'_\d{8}_\d{6}\.json$', f.name)]
    
    if not timestamped_files:
        results.append("✅ Backup folder: No excessive timestamped files")
    else:
        results.append(f"⚠️ Backup folder: Found {len(timestamped_files)} excessive timestamped files")
    
    return results

def main():
    print("""
🛡️ ═══════════════════════════════════════════════════════════════
    CYBERSECURITY BACKEND ORGANIZATION VERIFICATION
🛡️ ═══════════════════════════════════════════════════════════════
""")
    
    # Test imports
    import_results = test_imports()
    print("\n".join(import_results))
    
    print("\n" + "="*60)
    
    # Check file structure
    structure_results = check_file_structure()
    print("\n".join(structure_results))
    
    print("\n" + "="*60)
    
    # Check organized structure
    organization_results = check_organized_structure()
    print("\n".join(organization_results))
    
    print("\n" + "="*60)
    
    # Check data folder organization
    data_results = check_data_folder_structure()
    print("\n".join(data_results))
    
    print("\n" + "="*60)
    
    # Summary
    all_results = import_results + structure_results + organization_results + data_results
    success_count = len([r for r in all_results if r.startswith("✅")])
    total_count = len(all_results)
    
    print(f"\n📊 SUMMARY: {success_count}/{total_count} checks passed")
    
    if success_count == total_count:
        print("🎉 ALL CHECKS PASSED! Backend is properly organized.")
        return True
    else:
        print("⚠️ Some issues found. Check the results above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
