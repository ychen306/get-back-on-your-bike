from flask import Flask, request, jsonify, Response, render_template
import subprocess
from trackleaders import get_breaks, get_racer_id, get_racers, get_race_name

app = Flask(__name__)

BAD_REQUEST = Response(status='405')


def get_commit_hash():
    '''
    get git commit hash
    '''
    return subprocess.Popen(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE).\
            stdout.\
            readline().\
            strip()


@app.route('/<race_id>')
def home(race_id):
    return render_template('index.html',
            race_id=race_id,
            race_name=get_race_name(race_id),
            git_hash=get_commit_hash())


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


if __name__ == '__main__':
    app.run(debug=True)
