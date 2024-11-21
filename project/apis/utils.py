from rdflib import Graph, URIRef, Namespace, Literal
from rdflib.namespace import RDF, XSD
from datetime import datetime, timedelta
import uuid
import html
import os
from flask import current_app as app


CB = Namespace(app.config.get("CB"))



def check_file_exists(file_path):
    """
    Check if a file exists at the specified path.

    Args:
    - file_path (str): The path to the file to check.

    Returns:
    - bool: True if the file exists, False otherwise.
    """
    return os.path.exists(file_path)


def load_rdf_graph():
    """
    Load RDF graph from file.
    """
    g = Graph()
    g.parse("project/apis/rdf_data/CottageBooking.rdf", format="xml")
    return g

def load_service_description_graph():
    """
        Load RDF graph from file
    """
    g = Graph()
    g.parse("project/apis/rdf_data/CottageService.rdf", format="ttl")
    return g


def generate_possible_dates(start_date, date_shift, num_days):
    """
    Generate all possible date ranges based on start date and shift.
    """
    print("---------------------------------")
    try:
        start = start_date
        
        print(start)
        possible_dates = []
        for shift in range(-date_shift, date_shift + 1):
            shifted_start = start + timedelta(days=shift)
            shifted_end = shifted_start + timedelta(days=num_days)
            possible_dates.append({
                'startDate': shifted_start.strftime("%Y-%m-%d"),
                'endDate': shifted_end.strftime("%Y-%m-%d")
            })
        return possible_dates
    except Exception as e:
        app.logger.info(f"error: {e}")


def search_cottages_by_criteria(g, data):
    """
    Search for cottages matching the given criteria.
    """
    app.logger.info(f"--------------data---------")
    app.logger.info(f"{data}")
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

    app.logger.info(f"data in search cottage-----------")
    
    # Generate all possible date ranges
    possible_date_ranges = generate_possible_dates(start_date, date_shift, num_days)

    print(f"possible_date_ranges: {possible_date_ranges}")
    
    # Find matching cottages
    matching_cottages = []
    
    # Query for all cottages
    for cottage in g.subjects(RDF.type, CB.Cottage):
        
        # Get cottage properties
        places = int(g.value(cottage, CB.hasNumberOfPlaces))
        app.logger.info(f"places: {places}")
        bedrooms = int(g.value(cottage, CB.hasNumberOfBedrooms))
        lake_distance = int(g.value(cottage, CB.hasDistanceToLake))
        nearest_city = g.value(cottage, CB.hasNearestCity)
        city_name = str(g.value(nearest_city, CB.hasName))
        city_distance = int(g.value(cottage, CB.hasDistanceToCity))

        app.logger.info(f"-----------------------{str(g.value(cottage, CB.hasName))}------------------------")
        
        # Check if cottage matches criteria
        if (places >= required_places and
            bedrooms >= required_bedrooms and
            lake_distance <= max_lake_distance and
            city_name == preferred_city and
            city_distance <= max_city_distance):
            
            # Check available booking periods
            available_periods = get_available_booking_periods_for_a_cottage(g, cottage)
            # Check if any of the possible date ranges are available
            for date_range in possible_date_ranges:
                if is_any_date_range_available(available_periods, date_range):
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
                        'cottageName': str(g.value(cottage, CB.hasName)),
                        'bookingPeriod': date_range
                    }
                    matching_cottages.append(cottage_info)
    return matching_cottages


def get_available_booking_periods_for_a_cottage(g, cottage):
    """
    Retrieve available booking periods for a given cottage by checking against its unavailable booking periods.
    """
    # Get all booking periods
    all_booking_periods = get_all_booking_periods(g)
    app.logger.info(f"---------get all bookings -----------------------")
    app.logger.info(f"{all_booking_periods}")

    # Get unavailable booking periods for the cottage
    unavailable_periods = get_unavailable_booking_periods(g, cottage)
    app.logger.info(f"---------get unavailable bookings -----------------------")
    app.logger.info(f"{unavailable_periods}")

    available_periods = []

    for period in all_booking_periods:
        period_start = datetime.strptime(period['start_date'], "%Y-%m-%d")
        period_end = datetime.strptime(period['end_date'], "%Y-%m-%d")

        # Check if the current period overlaps with any unavailable periods
        is_available = True
        for unavailable in unavailable_periods:
            unavailable_start = datetime.strptime(unavailable['start_date'], "%Y-%m-%d")
            unavailable_end = datetime.strptime(unavailable['end_date'], "%Y-%m-%d")

            # Check for overlap
            if (period_start <= unavailable_end and period_end >= unavailable_start):
                is_available = False
                break  # No need to check further if we found an overlap

        if is_available:
            available_periods.append(period)

    app.logger.info("------- available booking --------------------")
    app.logger.info(f"total: {len(available_periods)}, {available_periods}")
    return available_periods



def get_unavailable_booking_periods(g, cottage):
    """
    Retrieve unavailable booking periods for a given cottage.
    """
    unavailable_periods = []
    # Fetch the unavailable booking period linked to the cottage
    for period in g.objects(cottage, CB.isUnavailable):
        start_date = g.value(period, CB.bookingStartDate)
        end_date = g.value(period, CB.bookingEndDate)
        unavailable_periods.append({
            'start_date': start_date,
            'end_date': end_date
        })
    return unavailable_periods


def get_all_booking_periods(g):
    """
    Retrieve all booking periods from the RDF graph.
    """
    booking_periods = []

    # Query for all booking period individuals
    for period in g.subjects(RDF.type, CB.BookingPeriod):
        start_date = g.value(period, CB.bookingStartDate)
        end_date = g.value(period, CB.bookingEndDate)

        # Append the booking period to the list
        booking_periods.append({
            'start_date': start_date,
            'end_date': end_date,
            'period_id': str(period)  # Optionally include the period ID
        })

    return booking_periods



def is_any_date_range_available(available_periods, possible_date_range):
    """
    Check if any of the possible date ranges are available (not in unavailable periods).
    """
    if is_date_range_available(available_periods, possible_date_range):
        return True  # Found an available date range
    return False


def is_date_range_available(available_periods, date_range):
    """
    Check if the given date range is unavailable within the unavailable booking periods.
    """
    start_date = datetime.strptime(date_range['startDate'], "%Y-%m-%d")
    end_date = datetime.strptime(date_range['endDate'], "%Y-%m-%d")

    for period in available_periods:
        period_start = datetime.strptime(period['start_date'], "%Y-%m-%d")
        period_end = datetime.strptime(period['end_date'], "%Y-%m-%d")

        if start_date >= period_start and end_date <= period_end:
            return True
    return False


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



def process_rdf_input():
    g = Graph()
    g.parse("project/apis/rdf_data/input.xml", format='xml')
    # Define the namespace
    ns1 = Namespace("http://localhost:8080/CottageBookingService/ontology#")
    print("booker")
    print(g.value(URIRef("http://example.org/request"), ns1.bookerName))

    # Extract the booking parameters
    raw_booking_data = {
        'bookerName': g.value(URIRef("http://example.org/request"), ns1.bookerName),
        'requiredPlaces': g.value(URIRef("http://example.org/request"), ns1.requiredPlaces),
        'requiredBedrooms': g.value(URIRef("http://example.org/request"), ns1.requiredBedrooms),
        'maxLakeDistance': g.value(URIRef("http://example.org/request"), ns1.maxDistanceToLake),
        'preferredCity': g.value(URIRef("http://example.org/request"), ns1.nearestCity),
        'maxCityDistance': g.value(URIRef("http://example.org/request"), ns1.maxDistanceToCity),
        'numberOfDays': g.value(URIRef("http://example.org/request"), ns1.requiredDays),
        'startDate': g.value(URIRef("http://example.org/request"), ns1.startDate),
        'dateShift': g.value(URIRef("http://example.org/request"), ns1.maxShiftDays)
    }

    app.logger.info(f"---------------------- raw booking data ------------------")
    app.logger.info(f"{raw_booking_data}")

    # Convert `rdflib.term.Literal` to plain Python types where applicable
    booking_data = {
        key: (value.value if isinstance(value, Literal) else value)
        for key, value in raw_booking_data.items()
    }

#     # Cast numeric fields explicitly to the desired types
#     # booking_data['requiredPlaces'] = int(booking_data['requiredPlaces'])
#     # booking_data['requiredBedrooms'] = int(booking_data['requiredBedrooms'])
#     # booking_data['maxLakeDistance'] = int(booking_data['maxLakeDistance'])
#     # booking_data['maxCityDistance'] = int(booking_data['maxCityDistance'])
#     # booking_data['numberOfDays'] = int(booking_data['numberOfDays'])
#     # booking_data['dateShift'] = int(booking_data['dateShift'])

    app.logger.info(f"Formatted input: {booking_data}")
    return booking_data





# Define function to generate RDF for multiple bookings
def generate_rdf(bookings_data):
    # Create a new RDF graph
    g = Graph()

    # Define namespaces
    ns = {
        'sswap': URIRef('http://localhost:8080/CottageBookingService/ontology#'),
        'cottage': URIRef('http://localhost:8080/CottageBookingService/cottage#'),
        'xsd': XSD
    }

    # Add the CottageBookingService resource
    service_uri = URIRef('http://localhost:8080/CottageBookingService')
    g.add((service_uri, RDF.type, ns['sswap'] + 'Resource'))
    g.add((service_uri, ns['sswap'] + 'name', Literal("Cottage Booking Service", datatype=XSD.string)))
    g.add((service_uri, ns['sswap'] + 'oneLineDescription', Literal("A service that accepts booking parameters and returns cottages that meet these requirements", datatype=XSD.string)))

    # Iterate through each booking and generate RDF for each
    for booking in bookings_data:
        # Generate a unique booking number (if needed, or use the provided bookingNumber)
        booking_number = booking['bookingNumber']

        # Create booking resource URI
        booking_uri = URIRef(f'http://localhost:8080/CottageBookingService/Booking/{booking_number}')
        # Add booking period details (nested object: bookingPeriod)
        start_date = booking['bookingPeriod']['startDate']
        end_date = booking['bookingPeriod']['endDate']
        g.add((booking_uri, ns['cottage'] + 'bookingStartDate', Literal(start_date, datatype=XSD.date)))
        g.add((booking_uri, ns['cottage'] + 'bookingEndDate', Literal(end_date, datatype=XSD.date)))

        # For each booking, add suggested cottages (mapped data)
        cottage_suggestion_uri = URIRef(f'http://localhost:8080/CottageBookingService/CottageSuggestion/{booking_number}')

        g.add((cottage_suggestion_uri, RDF.type, ns['sswap'] + 'CottageSuggestion'))
        g.add((cottage_suggestion_uri, ns['cottage'] + 'bookingNumber', Literal(booking['bookingNumber'], datatype=XSD.string)))
        g.add((cottage_suggestion_uri, ns['cottage'] + 'bookerName', Literal(booking['bookerName'], datatype=XSD.string)))
        g.add((cottage_suggestion_uri, ns['cottage'] + 'cottageName', Literal(booking['cottageName'], datatype=XSD.string)))
        g.add((cottage_suggestion_uri, ns['cottage'] + 'cottageAddress', Literal(booking['address'], datatype=XSD.string)))
        g.add((cottage_suggestion_uri, ns['cottage'] + 'cottageImage', Literal(booking['image'], datatype=XSD.anyURI)))
        g.add((cottage_suggestion_uri, ns['cottage'] + 'actualPlaces', Literal(booking['actualPlaces'], datatype=XSD.integer)))
        g.add((cottage_suggestion_uri, ns['cottage'] + 'actualBedrooms', Literal(booking['actualBedrooms'], datatype=XSD.integer)))
        g.add((cottage_suggestion_uri, ns['cottage'] + 'actualDistanceToLake', Literal(booking['distanceToLake'], datatype=XSD.integer)))
        g.add((cottage_suggestion_uri, ns['cottage'] + 'nearestCity', Literal(booking['nearestCity'], datatype=XSD.string)))
        g.add((cottage_suggestion_uri, ns['cottage'] + 'distanceToCity', Literal(booking['distanceToCity'], datatype=XSD.integer)))
        g.add((cottage_suggestion_uri, ns['cottage'] + 'bookingStartDate', Literal(start_date, datatype=XSD.date)))
        g.add((cottage_suggestion_uri, ns['cottage'] + 'bookingEndDate', Literal(end_date, datatype=XSD.date)))

        # Map the CottageBookingService to the CottageSuggestion
        g.add((booking_uri, ns['sswap'] + 'mapsTo', cottage_suggestion_uri))

    # Return the RDF graph in a readable format
    return g.serialize(format="xml")

# Example booking data (you can pass your actual data here)
# bookings_data = [
#     {
#         "bookerName": "John Doe",
#         "bookingNumber": "321ac1ad-044d-4643-82eb-edf02382091f",
#         "address": "321 Ocean Drive, Helsinki",
#         "image": "https://s3.brilliant.com.bd/images/seasidevilla.jpg",
#         "actualPlaces": 10,
#         "actualBedrooms": 5,
#         "distanceToLake": 0,
#         "nearestCity": "Helsinki",
#         "distanceToCity": 10,
#         "cottageName": "Seaside Villa",
#         "bookingPeriod": {
#             "startDate": "2024-12-01",
#             "endDate": "2024-12-06"
#         }
#     },
#     {
#         "bookerName": "Jane Doe",
#         "bookingNumber": "abc12345-6789-0123-4567-89abcdef0123",
#         "address": "123 Lake View, Espoo",
#         "image": "https://s3.brilliant.com.bd/images/lakeviewvilla.jpg",
#         "actualPlaces": 8,
#         "actualBedrooms": 4,
#         "distanceToLake": 2,
#         "nearestCity": "Espoo",
#         "distanceToCity": 5,
#         "cottageName": "Lake View Villa",
#         "bookingPeriod": {
#             "startDate": "2024-12-10",
#             "endDate": "2024-12-15"
#         }
#     }
# ]




