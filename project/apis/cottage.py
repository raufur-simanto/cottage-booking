from flask import request, jsonify, current_app as app, render_template, make_response, send_from_directory, Response
from flask_restx import Namespace, Resource, fields
from project.apis.utils import load_rdf_graph, search_cottages_by_criteria, get_all_cottages, load_service_description_graph, process_rdf_input, generate_rdf
import os

# Load RDF data graph
g = load_rdf_graph()
service_g = load_service_description_graph()


# Define the namespace for cottages
cottage_namespace = Namespace("Cottages", description="Cottage related operations")

# Define request models
cottage_search_model = cottage_namespace.model('CottageSearch', {
    'bookerName': fields.String(required=True, description="Name of the booker"),
    'requiredPlaces': fields.Integer(required=True, description="Number of places needed"),
    'requiredBedrooms': fields.Integer(required=True, description="Number of bedrooms required"),
    'maxLakeDistance': fields.Integer(required=True, description="Max distance to lake"),
    'preferredCity': fields.String(required=True, description="Preferred city"),
    'maxCityDistance': fields.Integer(required=True, description="Max distance to city center"),
    'numberOfDays': fields.Integer(required=True, description="Number of days to stay"),
    'startDate': fields.String(required=True, description="Start date in dd.mm.yyyy format"),
    'dateShift': fields.Integer(required=True, description="Allowed shift in dates"),
})


class MainPage(Resource):
    def get(self):
        headers = {'Content-Type': 'text/html'}
        return make_response(render_template('index.html'), 200, headers)
    

class Cottage_Service(Resource):
    def get(self):
        data = service_g.serialize(format='xml')
        return Response(data, mimetype='application/rdf+xml')




class SearchCottages(Resource):
    # @cottage_namespace.expect(cottage_search_model)
    def post(self):
        data = request.data.decode('utf-8')
        # app.logger.info(f"--------------------------data----------------------------")
        data = data.encode().decode("unicode_escape")
        cleaned_data = data.strip('"')
        app.logger.info(f"cleaned:   {cleaned_data}")
        with open("project/apis/rdf_data/input.xml", "w", encoding="utf-8") as f:
            f.write(cleaned_data)

        booking_input_data = process_rdf_input()
        app.logger.info(f"formated input: {booking_input_data}")
        try:
            matching_cottages = search_cottages_by_criteria(g, booking_input_data)
            resp_data = generate_rdf(matching_cottages)
            app.logger.info(f"{resp_data}")
            # return {'status': 'success', 'results': resp_data}
            return Response(resp_data, content_type="xml/rdf")
        except Exception as e:
            return {'status': 'error', 'message': str(e)}, 400


class GetAllCottages(Resource):
    def get(self):
        is_available_query = request.args.get('isAvailable', default=None, type=str)
        try:
            cottages = get_all_cottages(g, is_available_query)
            app.logger.info(cottages)

            return {'status': 'success', 'results': cottages}, 200
        except Exception as e:
            return {'status': 'error', 'message': str(e)}, 400

     
class Alive(Resource):
    def get(self):
        return {"msg": "Alive"}, 200
    

class ServeOntology(Resource):
    def get(self, filename):
        try:
            # Get the absolute path to the rdf_data directory
            rdf_data_path = os.path.join(os.path.dirname(__file__), 'rdf_data')
            app.logger.info(f"Attempting to serve ontology file: {filename}")
            app.logger.info(f"Looking in directory: {rdf_data_path}")
            
            # Read the file content
            with open(os.path.join(rdf_data_path, filename), 'r') as f:
                content = f.read()

            # Create response with proper content type
            response = make_response(content)
            
            # Set content type based on file extension
            if filename.endswith('.owl'):
                response.headers['Content-Type'] = 'application/rdf+xml'
            elif filename.endswith('.rdf'):
                response.headers['Content-Type'] = 'application/rdf+xml'
            elif filename.endswith('.ttl'):
                response.headers['Content-Type'] = 'text/turtle'
            else:
                response.headers['Content-Type'] = 'text/plain'

            # Add CORS headers to allow the Falcon extension to read the content
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            
            # Add headers to display in browser
            response.headers['Content-Disposition'] = 'inline'
            
            return response

        except Exception as e:
            app.logger.error(f"Error serving ontology: {str(e)}")
            return {'error': str(e)}, 404



# Update the resource additions
cottage_namespace.add_resource(Cottage_Service, '')
# cottage_namespace.add_resource(MainPage, '')
cottage_namespace.add_resource(SearchCottages, '/search')
cottage_namespace.add_resource(GetAllCottages, '/all')
cottage_namespace.add_resource(Alive, "/alive")
cottage_namespace.add_resource(ServeOntology, '/onto/<path:filename>')
