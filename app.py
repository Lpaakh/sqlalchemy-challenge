# Import necessary libraries
import numpy as np
from datetime import datetime
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify


# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
station = Base.classes.station
measurement = Base.classes.measurement

# Create an app, being sure to pass __name__
app = Flask(__name__)


# Define what to do when a user hits the index route
@app.route("/")
def home():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/{{start}}<br/>"
        f"/api/v1.0/{{start}}/{{end}}<br/>"
    )

# Define what to do when a user hits the various routes
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Convert the query results to a dictionary using date as the key and prcp as the value.
    most_recent_date = session.query(measurement.date).order_by(measurement.date.desc()).first()[0]
    most_recent_date_datetime = datetime.strptime(most_recent_date, "%Y-%m-%d")
    one_year_prior = str(most_recent_date_datetime.replace(year=most_recent_date_datetime.year-1).date())

    ytd_precipitation = session.query(measurement.date, func.max(measurement.prcp).label('prcp')).\
    filter(measurement.date >= one_year_prior).\
    group_by(measurement.date).order_by(measurement.date).all()

    session.close()

    ytd_precipitation_dict = { ytd_precipitation[i][0] : ytd_precipitation[i][1] for i in range(0,len(ytd_precipitation)) }

    # Return the JSON representation of your dictionary.
    return jsonify(ytd_precipitation_dict)


@app.route("/api/v1.0/stations")
def stations():
     # Create our session (link) from Python to the DB
    session = Session(engine)

    # Return a JSON list of stations from the dataset.
    station_list = session.query(station.station).all()
    
    session.close()

    # Return a JSON list of station_list
    station_list = [ station[0] for station in station_list ]

    return jsonify(station_list)

@app.route("/api/v1.0/tobs")
def tobs():
     # Create our session (link) from Python to the DB
    session = Session(engine)

    #Query the dates and temperature observations of the most active station for the last year of data.
    most_recent_date = session.query(measurement.date).order_by(measurement.date.desc()).first()[0]
    most_recent_date_datetime = datetime.strptime(most_recent_date, "%Y-%m-%d")
    one_year_prior = str(most_recent_date_datetime.replace(year=most_recent_date_datetime.year-1).date())
    
    most_temp_activity = session.query(measurement.station, func.count(measurement.tobs).label('count')).\
        filter(measurement.tobs.isnot(None))\
        .group_by(measurement.station).order_by(func.count(measurement.tobs).desc()).first()[0]

    tobs = session.query(func.max(measurement.tobs).label('highest_temp')).\
        filter(measurement.date >= one_year_prior).\
        filter(measurement.station == most_temp_activity).\
        group_by(measurement.date).order_by(measurement.date).all()

    session.close()

    # Return a JSON list of temperature observations (TOBS) for the previous year.
    tobs = [ temp[0] for temp in tobs ]

    return jsonify(tobs)

@app.route("/api/v1.0/<start>")
def start(start):

     # Create our session (link) from Python to the DB
    session = Session(engine)

    #Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range.
    temp_data = session.query(func.min(measurement.tobs).label('lowest temp'),\
        func.max(measurement.tobs).label('highest temp'),\
        func.avg(measurement.tobs).label('average temp'))\
        .filter(measurement.date >= start).first()

    session.close()

    #When given the start only, calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date.
    # Convert list of tuples into normal list
    result = { 'TMIN': temp_data[0],
        'TAVG': temp_data[1],
        'TMAX': temp_data[2]
    }

    return jsonify(result)

@app.route("/api/v1.0/<start>/<end>")
def end(start, end):

    # Create our session (link) from Python to the DB
    session = Session(engine)

     #Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range.
    temp_data = session.query(func.min(measurement.tobs).label('lowest temp'),\
        func.max(measurement.tobs).label('highest temp'),\
        func.avg(measurement.tobs).label('average temp'))\
        .filter( measurement.date >= start, measurement.date <= end ).first()

    session.close()
     #When given the start and the end date, calculate the TMIN, TAVG, and TMAX for dates between the start and end date inclusive.
    # Convert list of tuples into normal list
    result = { 'TMIN': temp_data[0],
        'TAVG': temp_data[1],
        'TMAX': temp_data[2]
    }

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
