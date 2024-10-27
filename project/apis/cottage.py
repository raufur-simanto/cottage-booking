from flask import request, jsonify, current_app as app, render_template, make_response
from flask_restx import Namespace, Resource, fields
from project.apis.utils import load_rdf_graph, search_cottages_by_criteria, get_all_cottages

# Load RDF data graph
g = load_rdf_graph()


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


class SearchCottages(Resource):
    @cottage_namespace.expect(cottage_search_model)
    def post(self):
        data = request.json
        try:
            matching_cottages = search_cottages_by_criteria(g, data)
            return {'status': 'success', 'results': matching_cottages}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}, 400

# Route to get all cottages with an optional 'isAvailable' query param


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



# Update the resource additions
cottage_namespace.add_resource(MainPage, '')
cottage_namespace.add_resource(SearchCottages, '/search')
cottage_namespace.add_resource(GetAllCottages, '/all')
cottage_namespace.add_resource(Alive, "/alive")
