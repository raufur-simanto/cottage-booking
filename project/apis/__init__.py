from flask_restx import Api

api = Api( 
    title="Cottage Booking Service",
    version="1.0",
    description="A simple Cottage Booking Api",
    doc="/docs"
    )

from project.apis.cottage import cottage_namespace

api.add_namespace(cottage_namespace, path='/cottages')
