# data/mock_apartments.py - Realistic Ottawa apartments for testing/demo

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Apartment


def get_mock_apartments(budget_min: int, budget_max: int, bedrooms: int) -> list:
    """
    Returns realistic mock apartments for Ottawa.
    Filters by budget and bedrooms.
    """
    
    all_apartments = [
        Apartment(
            id="apt_001",
            title="Modern 1BR in the Heart of Centretown",
            address="180 Metcalfe Street, Unit 804",
            neighborhood="Centretown",
            price=1850,
            bedrooms=1,
            bathrooms=1.0,
            sqft=620,
            amenities=["gym", "rooftop_terrace", "concierge"],
            pet_friendly=False,
            parking_included=False,
            laundry_type="in_building",
            image_url="https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800",
            source_url="https://rentals.ca/ottawa/180-metcalfe-street",
            lat=45.4201,
            lng=-75.6941
        ),
        Apartment(
            id="apt_002",
            title="Sunny 1BR with Balcony - The Glebe",
            address="890 Bank Street, Unit 305",
            neighborhood="The Glebe",
            price=1950,
            bedrooms=1,
            bathrooms=1.0,
            sqft=700,
            amenities=["balcony", "dishwasher"],
            pet_friendly=True,
            parking_included=True,
            laundry_type="in_unit",
            image_url="https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800",
            source_url="https://rentals.ca/ottawa/890-bank-street",
            lat=45.3989,
            lng=-75.6897
        ),
        Apartment(
            id="apt_003",
            title="Affordable 1BR near Parliament",
            address="222 Queen Street, Unit 1204",
            neighborhood="Centretown",
            price=1650,
            bedrooms=1,
            bathrooms=1.0,
            sqft=550,
            amenities=["gym"],
            pet_friendly=False,
            parking_included=False,
            laundry_type="in_building",
            image_url="https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800",
            source_url="https://rentals.ca/ottawa/222-queen-street",
            lat=45.4215,
            lng=-75.6972
        ),
        Apartment(
            id="apt_004",
            title="Trendy Loft in Hintonburg",
            address="1080 Wellington Street West, Unit 2",
            neighborhood="Hintonburg",
            price=1750,
            bedrooms=1,
            bathrooms=1.0,
            sqft=680,
            amenities=["exposed_brick", "high_ceilings"],
            pet_friendly=True,
            parking_included=False,
            laundry_type="in_unit",
            image_url="https://images.unsplash.com/photo-1536376072261-38c75010e6c9?w=800",
            source_url="https://rentals.ca/ottawa/1080-wellington-west",
            lat=45.3975,
            lng=-75.7330
        ),
        Apartment(
            id="apt_005",
            title="Cozy 1BR in Sandy Hill",
            address="450 Laurier Avenue East, Unit 6",
            neighborhood="Sandy Hill",
            price=1550,
            bedrooms=1,
            bathrooms=1.0,
            sqft=580,
            amenities=[],
            pet_friendly=False,
            parking_included=True,
            laundry_type="in_building",
            image_url="https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=800",
            source_url="https://rentals.ca/ottawa/450-laurier-east",
            lat=45.4240,
            lng=-75.6780
        ),
        Apartment(
            id="apt_006",
            title="Spacious 1BR in Westboro Village",
            address="388 Richmond Road, Unit 501",
            neighborhood="Westboro",
            price=2100,
            bedrooms=1,
            bathrooms=1.0,
            sqft=750,
            amenities=["gym", "pool", "balcony"],
            pet_friendly=True,
            parking_included=True,
            laundry_type="in_unit",
            image_url="https://images.unsplash.com/photo-1560185893-a55cbc8c57e8?w=800",
            source_url="https://rentals.ca/ottawa/388-richmond-road",
            lat=45.3925,
            lng=-75.7540
        ),
        Apartment(
            id="apt_007",
            title="Budget-Friendly 1BR in Vanier",
            address="255 Montreal Road, Unit 102",
            neighborhood="Vanier",
            price=1400,
            bedrooms=1,
            bathrooms=1.0,
            sqft=600,
            amenities=["parking"],
            pet_friendly=True,
            parking_included=True,
            laundry_type="in_building",
            image_url="https://images.unsplash.com/photo-1484154218962-a197022b5858?w=800",
            source_url="https://rentals.ca/ottawa/255-montreal-road",
            lat=45.4380,
            lng=-75.6650
        ),
        Apartment(
            id="apt_008",
            title="Charming 1BR in Little Italy",
            address="330 Preston Street, Unit 4B",
            neighborhood="Little Italy",
            price=1700,
            bedrooms=1,
            bathrooms=1.0,
            sqft=640,
            amenities=["dishwasher"],
            pet_friendly=False,
            parking_included=False,
            laundry_type="in_unit",
            image_url="https://images.unsplash.com/photo-1502672023488-70e25813eb80?w=800",
            source_url="https://rentals.ca/ottawa/330-preston-street",
            lat=45.4062,
            lng=-75.7145
        ),
        Apartment(
            id="apt_009",
            title="Luxury 1BR in Byward Market",
            address="50 George Street, Unit 1808",
            neighborhood="Byward Market",
            price=2200,
            bedrooms=1,
            bathrooms=1.0,
            sqft=580,
            amenities=["gym", "concierge", "rooftop_terrace"],
            pet_friendly=False,
            parking_included=False,
            laundry_type="in_unit",
            image_url="https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800",
            source_url="https://rentals.ca/ottawa/50-george-street",
            lat=45.4275,
            lng=-75.6920
        ),
        Apartment(
            id="apt_010",
            title="Quiet 1BR in Alta Vista",
            address="1541 Alta Vista Drive, Unit 3",
            neighborhood="Alta Vista",
            price=1600,
            bedrooms=1,
            bathrooms=1.0,
            sqft=720,
            amenities=["balcony", "parking"],
            pet_friendly=True,
            parking_included=True,
            laundry_type="in_unit",
            image_url="https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?w=800",
            source_url="https://rentals.ca/ottawa/1541-alta-vista",
            lat=45.3850,
            lng=-75.6690
        ),
        Apartment(
            id="apt_011",
            title="Renovated 1BR in Old Ottawa South",
            address="1100 Bank Street, Unit 208",
            neighborhood="Old Ottawa South",
            price=1800,
            bedrooms=1,
            bathrooms=1.0,
            sqft=670,
            amenities=["dishwasher", "ac"],
            pet_friendly=True,
            parking_included=False,
            laundry_type="in_building",
            image_url="https://images.unsplash.com/photo-1536376072261-38c75010e6c9?w=800",
            source_url="https://rentals.ca/ottawa/1100-bank-street",
            lat=45.3890,
            lng=-75.6880
        ),
        Apartment(
            id="apt_012",
            title="Bright Corner Unit - New Edinburgh",
            address="420 Mackay Street, Unit 5",
            neighborhood="New Edinburgh",
            price=1900,
            bedrooms=1,
            bathrooms=1.0,
            sqft=700,
            amenities=["balcony"],
            pet_friendly=True,
            parking_included=True,
            laundry_type="in_unit",
            image_url="https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=800",
            source_url="https://rentals.ca/ottawa/420-mackay-street",
            lat=45.4380,
            lng=-75.6780
        ),
        Apartment(
            id="apt_013",
            title="Spacious 2BR Family Apartment - Centretown",
            address="200 Gloucester Street, Unit 605",
            neighborhood="Centretown",
            price=2400,
            bedrooms=2,
            bathrooms=1.0,
            sqft=950,
            amenities=["gym", "parking"],
            pet_friendly=True,
            parking_included=True,
            laundry_type="in_unit",
            image_url="https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800",
            source_url="https://rentals.ca/ottawa/200-gloucester",
            lat=45.4180,
            lng=-75.6950
        ),
        Apartment(
            id="apt_014",
            title="2BR with Den in The Glebe",
            address="780 Bank Street, Unit 402",
            neighborhood="The Glebe",
            price=2600,
            bedrooms=2,
            bathrooms=1.5,
            sqft=1050,
            amenities=["balcony", "dishwasher", "ac"],
            pet_friendly=True,
            parking_included=True,
            laundry_type="in_unit",
            image_url="https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800",
            source_url="https://rentals.ca/ottawa/780-bank-street",
            lat=45.4010,
            lng=-75.6890
        ),
        Apartment(
            id="apt_015",
            title="Affordable 2BR in Vanier",
            address="300 Montreal Road, Unit 8",
            neighborhood="Vanier",
            price=1800,
            bedrooms=2,
            bathrooms=1.0,
            sqft=850,
            amenities=["parking"],
            pet_friendly=True,
            parking_included=True,
            laundry_type="in_building",
            image_url="https://images.unsplash.com/photo-1484154218962-a197022b5858?w=800",
            source_url="https://rentals.ca/ottawa/300-montreal-road",
            lat=45.4395,
            lng=-75.6620
        ),
    ]
    
    filtered = [
        apt for apt in all_apartments
        if budget_min <= apt.price <= budget_max
        and apt.bedrooms == bedrooms
    ]
    
    return filtered


if __name__ == "__main__":
    apartments = get_mock_apartments(1500, 2000, 1)
    print(f"Found {len(apartments)} apartments between $1500-$2000 (1BR):")
    for apt in apartments:
        print(f"  • {apt.title}: ${apt.price}/mo in {apt.neighborhood}")
