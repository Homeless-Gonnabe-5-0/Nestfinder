from services.rental_scraper import RentalScraperService
from models import Apartment

class ScraperAgent:
    def __init__(self):
        self.name = "ScraperAgent"
        self.scraper = RentalScraperService()
    
    async def scrape_listings(self, max_pages=5) -> list[Apartment]:
        """Scrape fresh listings"""
        raw_listings = self.scraper.scrape_listings(max_pages=max_pages)
        return [self._to_apartment(listing) for listing in raw_listings]
    
    async def get_cached_listings(self) -> list[Apartment]:
        """Get cached listings"""
        raw_listings = self.scraper.get_cached_listings()
        return [self._to_apartment(listing) for listing in raw_listings]
    
    def _to_apartment(self, raw_data) -> Apartment:
        """Convert raw scraped data to Apartment model"""
        return Apartment(
            id=raw_data.get('id'),
            title=raw_data.get('title'),
            address=raw_data.get('address'),
            neighborhood=raw_data.get('neighborhood'),
            price=raw_data.get('price'),
            bedrooms=raw_data.get('bedrooms'),
            bathrooms=raw_data.get('bathrooms'),
            url=raw_data.get('url'),
            description=raw_data.get('description'),
        )