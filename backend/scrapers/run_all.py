#!/usr/bin/env python3
"""Run all scrapers"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from zumper_scraper import scrape as scrape_zumper
from kijiji_scraper import scrape as scrape_kijiji
from zillow_scraper import scrape as scrape_zillow

def main():
    print("="*60)
    print("RUNNING ALL SCRAPERS")
    print("="*60)
    
    results = {}
    
    print("\n--- ZUMPER ---")
    results['zumper'] = scrape_zumper()
    
    print("\n--- KIJIJI ---")
    results['kijiji'] = scrape_kijiji()
    
    print("\n--- ZILLOW ---")
    results['zillow'] = scrape_zillow()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    total = 0
    for source, listings in results.items():
        count = len(listings) if listings else 0
        total += count
        status = "OK" if count > 0 else "FAILED"
        print(f"  {source}: {count} listings [{status}]")
    
    print(f"\nTotal: {total} listings")
    print("="*60)

if __name__ == "__main__":
    main()
