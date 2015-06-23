import time
import re
from datetime import datetime, timedelta
import requests
from lxml.etree import HTML

# URL template for accessing spot records
SPOT_URL_TEMPL = 'http://trackleaders.com/spot/%s/%s.js'
# RE template for parsing spot timestamp
SPOT_TS_RE_TEMPL = 'title: "%s - (?:(?P<days>\d+) days, )?(?:(?P<hours>\d+) hours, )?(?P<minutes>\d+) minutes ago",[^\n\r]* icon: (?P<icon>\w+)}'
# Trackleader URL template
TL_URL_TEMPL = "http://trackleaders.com/%sf.php"
# RE for parsing spot position (latLong pair)
SPOT_POS_RE = re.compile(r'\);point = new google.maps.LatLng\( (?P<latitude>[\-\d.]+), (?P<longitude>[\-\d.]+)\)')
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
# icons trackleaders used for moving dots
REGULAR_ICONS = ('iconDot', 'iconDotGray')


def process_timestamp(ts_match):
    ts = ts_match.groupdict()
    for k, v in ts.iteritems():
        if v is None:
            ts[k] = 0
        elif k != 'icon':
            ts[k] = int(v)
    return ts


def parse_timestamps(racer_id, spot_feed):
    '''
    parse timestamps from spot feed (actually a JS source file)
    '''
    matched_timestamps = re.finditer(SPOT_TS_RE_TEMPL% racer_id,
                                    spot_feed,
                                    re.MULTILINE) 
    return map(process_timestamp, matched_timestamps)


def get_racer_id(racer_name):
    components = re.split('\W', racer_name)
    return '_'.join(c.capitalize() for c in components)


def make_datetime_converter():
    '''
    convert timestamp to a datetime
    '''
    now = datetime.now()
    def converter(ts):
        delta = timedelta(days=ts['days'],
                hours=ts['hours'],
                minutes=ts['minutes'])
        return now - delta

    return converter 


def to_readable_duration(duration):
    '''
    convert a timedelta into a human-friendly string (hh:mm:ss)
    '''
    compact_time = time.strftime('%H:%M:%S', time.gmtime(duration.total_seconds())) 
    hours, minutes, seconds = compact_time.split(':')
    return "%s hours, %s minutes, and %s seconds"% (hours, minutes, seconds) 


def get_breaks(race, racer_id):
    '''
    given a race id and id of a user, return off-saddle data
    '''
    spot_url = SPOT_URL_TEMPL% (race, racer_id)
    spot_feed = requests.get(spot_url, headers={'User-Agent': USER_AGENT}).text
    as_date = make_datetime_converter()
    timestamps = parse_timestamps(racer_id, spot_feed)
    positions = list(SPOT_POS_RE.finditer(spot_feed, re.MULTILINE))
    breaks = []
    for i, ts in enumerate(timestamps):
        if ts['icon'] in REGULAR_ICONS or i == len(timestamps) - 1:
            continue
        matched_pos = positions[i] 
        break_start, break_end = as_date(ts), as_date(timestamps[i+1])
        duration = to_readable_duration(break_end-break_start)
        lat = float(matched_pos.group('latitude'))
        lng = float(matched_pos.group('longitude'))
        breaks.append({
            'start': break_start.isoformat(),
            'end': break_end.isoformat(),
            'duration': duration,
            'lat': lat,
            'lng': lng
        })
    return breaks 


def get_racers(race_id):
    page = HTML(requests.get(TL_URL_TEMPL% race_id, headers={'User-Agent': USER_AGENT}).text)
    racers = set(el.text for el in page.xpath('.//a[@title="Click for individual history"]'))
    return list(racers)


def get_race_name(race_id):
    page = HTML(requests.get(TL_URL_TEMPL% race_id, headers={'User-Agent': USER_AGENT}).text)
    return page.findtext('.//title').split('live')[0].strip()
