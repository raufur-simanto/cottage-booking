from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import RDF
from datetime import datetime, timedelta
import uuid

from flask import current_app as app


CB = Namespace(app.config.get("CB"))
ONT = Namespace(app.config.get("ONT"))


def load_rdf_graph():
    """
    Load RDF graph from file.
    """
    g = Graph()
    g.parse("project/apis/rdf_data/CottageBookingData.rdf", format="xml")
    return g


def generate_possible_dates(start_date, date_shift, num_days):
    """
    Generate all possible date ranges based on start date and shift.
    """
    start = datetime.strptime(start_date, "%d.%m.%Y")
    possible_dates = []
    for shift in range(-date_shift, date_shift + 1):
        shifted_start = start + timedelta(days=shift)
        shifted_end = shifted_start + timedelta(days=num_days)
        possible_dates.append({
            'startDate': shifted_start.strftime("%Y-%m-%d"),
            'endDate': shifted_end.strftime("%Y-%m-%d")
        })
    return possible_dates


def search_cottages_by_criteria(g, data):
    """
    Search for cottages matching the given criteria.
    """
    # Extract search criteria
    booker_name = data['bookerName']
    required_places = int(data['requiredPlaces'])
    required_bedrooms = int(data['requiredBedrooms'])
    max_lake_distance = int(data['maxLakeDistance'])
    preferred_city = data['preferredCity']
    max_city_distance = int(data['maxCityDistance'])
    num_days = int(data['numberOfDays'])
    start_date = data['startDate']  # Format: dd.mm.yyyy
    date_shift = int(data['dateShift'])
    
    # Generate all possible date ranges
    possible_date_ranges = generate_possible_dates(start_date, date_shift, num_days)

    print(f"possible_date_ranges: {possible_date_ranges}")
    
    # Find matching cottages
    matching_cottages = []
    
    # Query for all cottages
    for cottage in g.subjects(RDF.type, CB.Cottage):
        # Check if cottage is available
        isAvailable = bool(g.value(cottage, ONT.isAvailable, default=False))
        if not isAvailable:
            continue
            
        # Get cottage properties
        places = int(g.value(cottage, CB.hasNumberOfPlaces))
        bedrooms = int(g.value(cottage, CB.hasNumberOfBedrooms))
        lake_distance = int(g.value(cottage, CB.hasDistanceToLake))
        nearest_city = g.value(cottage, CB.hasNearestCity)
        city_name = str(g.value(nearest_city, CB.hasName))
        city_distance = int(g.value(cottage, CB.hasDistanceToCity))
        
        # Check if cottage matches criteria
        if (places >= required_places and
            bedrooms >= required_bedrooms and
            lake_distance <= max_lake_distance and
            city_name == preferred_city and
            city_distance <= max_city_distance):
            
            # Generate a booking suggestion for each possible date range
            for date_range in possible_date_ranges:
                booking_number = str(uuid.uuid4())
                
                cottage_info = {
                    'bookerName': booker_name,
                    'bookingNumber': booking_number,
                    'address': str(g.value(cottage, CB.hasAddress)),
                    'image': str(g.value(cottage, CB.hasImage)),
                    'actualPlaces': places,
                    'actualBedrooms': bedrooms,
                    'distanceToLake': lake_distance,
                    'nearestCity': city_name,
                    'distanceToCity': city_distance,
                    'bookingPeriod': date_range,
                    'cottageName': str(g.value(cottage, CB.hasName))
                }
                matching_cottages.append(cottage_info)
    return matching_cottages



def get_all_cottages(g, is_available_query):
    """
    Retrieve all cottages, optionally filter by availability.
    """

    if is_available_query is not None:
            is_available_query = is_available_query.lower() in ['true', '1', 'yes']
        
    all_cottages = []

    ## query in cottages 
    for cottage in g.subjects(RDF.type, CB.Cottage):
        places = int(g.value(cottage, CB.hasNumberOfPlaces))
        bedrooms = int(g.value(cottage, CB.hasNumberOfBedrooms))
        lake_distance = int(g.value(cottage, CB.hasDistanceToLake))
        nearest_city = g.value(cottage, CB.hasNearestCity)
        city_name = str(g.value(nearest_city, CB.hasName))
        city_distance = int(g.value(cottage, CB.hasDistanceToCity))
        cottage_name = str(g.value(cottage, CB.hasName))
        address = str(g.value(cottage, CB.hasAddress))
        image = str(g.value(cottage, CB.hasImage))
        is_available = bool(g.value(cottage, ONT.isAvailable))

        # If 'isAvailable' is provided, filter by availability
        if is_available_query is not None and is_available != is_available_query:
            continue

        cottage_info = {
            'cottageName': cottage_name,
            'address': address,
            'image': image,
            'actualPlaces': places,
            'actualBedrooms': bedrooms,
            'distanceToLake': lake_distance,
            'nearestCity': city_name,
            'distanceToCity': city_distance,
            'isAvailable': is_available
        }

        all_cottages.append(cottage_info)
    return all_cottages
