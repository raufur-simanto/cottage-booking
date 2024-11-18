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
    g.parse("project/apis/rdf_data/CottageBooking.rdf", format="xml")
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
