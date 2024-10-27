from flask_restx import Api

api = Api( 
    title="Cottage Booking Service",
    version="1.0",
    description="A simple Cottage Booking Api"
    )

from project.apis.cottage import cottage_namespace

api.add_namespace(cottage_namespace, path='/cottages')
