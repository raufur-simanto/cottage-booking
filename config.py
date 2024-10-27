import os


class BaseConfig:
    "This class is for base configuration"

    CB = "http://localhost:8080/CottageBooking/ontology#"
    ONT = "http://www.co-ode.org/ontologies/ont.owl#"


class DevelopmentConfig(BaseConfig):
    pass


class ProductionConfig(BaseConfig):
    pass


class TestConfig(BaseConfig):
    pass
    

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestConfig,
}
