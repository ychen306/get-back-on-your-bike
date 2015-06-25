from flask import Flask, request, jsonify, Response, render_template
from hashlib import md5
from trackleaders import get_breaks, get_racer_id, get_racers, get_race_name
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from config import REDIS_HOST, REDIS_PORT
import redis

app = Flask(__name__)
sr = redis.StrictRedis(host='localhost', port=6379, db=0)

BAD_REQUEST = Response(status='405')


def digest(fname):
    '''
    get mp5 digest of a file
    '''
    with open(fname) as target:
        return md5(target.read()).hexdigest()


@app.route('/<race_id>')
def home(race_id):
    return render_template('index.html',
            race_id=race_id,
            race_name=get_race_name(race_id),
            main_digest=digest('static/main.js'))


@app.route('/breaks/<race_id>')
def show_breaks(race_id):
    if 'name' not in request.args:
        return BAD_REQUEST
    racer_name = request.args['name']
    racer_id = get_racer_id(racer_name)
    breaks, tot_duration = get_breaks(race_id, racer_id)
    feed = {
        'raceId': race_id,
        'racerId': racer_id,
        'racerName': racer_name, 
        'breaks': breaks,
        'totalDuration': int(tot_duration)
    }
    return jsonify(feed)


@app.route('/racers/<race_id>')
def show_racers(race_id):
    feed = {
        'raceId': race_id,
        'racers': get_racers(race_id)
    }
    return jsonify(feed)


@app.route('/geocode/<lat>,<lng>')
def geocode(lat, lng):
    endp = "%s,%s" % (lat, lng)
    if sr.exists(endp):
        return format_geocode_response(sr.get(endp))

    geolocator = get_geocoder()
    try:
        location = locate(endp, geolocator)
    except GeocoderTimedOut:
        location = locate(endp, get_geocoder())

    addr = location.address
    sr.set(endp, addr)
    return format_geocode_response(addr)

def locate(latlng, geolocator):
    return geolocator.reverse(latlng, exactly_one=True)

def format_geocode_response(addr):
    return jsonify({
        'results' : [{
            'formatted_address' : addr
        }]
    })

def get_geocoder():
    return Nominatim()


if __name__ == '__main__':
    app.run(debug=True)
