## This is a Cottage Booking System

# Project Name

Brief description of what your project does.

## Prerequisites

- Python 3.9+
- Docker (optional)

## Installation

### Local Setup

1. Clone the repository:

   ```bash
   git clone git@github.com:raufur-simanto/cottage-booking.git
   ```

2. Create a virtual environment and activate it:

   ```bash
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory and add your environment variables:

   ```bash
   FLASK_APP=app.py
   ```

### Docker Setup

1. Build the Docker image:

   ```bash
   docker build -t <image-name> .
   ```

2. Run the container:

   ```bash
   docker run -p 5000:5000 <image-name>
   ```

## Usage

The application will be available at `http://localhost:5000/cottages`

## Ontology file path
`http://localhost:5000/cottages/onto/CottageBookingData.rdf`

## API Documentation

The API documentation is automatically generated using Flask-RESTX and can be accessed at:
`http://localhost:5000/docs`

