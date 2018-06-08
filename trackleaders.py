import time
import re
from datetime import datetime, timedelta
import requests
from lxml.etree import HTML

# URL template for accessing spot records
SPOT_URL_TEMPL = 'http://trackleaders.com/spot/%s/%s.js'
# RE template for parsing spot timestamp
SPOT_TS_RE_TEMPL = '"%s - (?:(?P<days>\d+) days, )?(?:(?P<hours>\d+) hours, )?(?P<minutes>\d+) minutes ago",.* icon:'
# Trackleader URL template
TL_URL_TEMPL = "http://trackleaders.com/%sf.php"
# RE for parsing spot position (latLong pair)
SPOT_POS_RE = re.compile(r'\);point = new google.maps.LatLng\( (?P<latitude>[\-\d.]+), (?P<longitude>[\-\d.]+)\)')
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
MILE_RE = re.compile(r'Route mile (?P<mile>.*) mi')
MIN_STOP_TIME = timedelta(minutes=5)
# if a racer's average speed (MPH) between two points is lower than this, we consider it a break
STOP_SPEED = 2.0

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
    return '_'.join(c for c in components)


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
    minutes, _ = divmod(duration, 60)
    hours, minutes = divmod(minutes, 60)
    readable = []
    if hours != 0:
        readable.append("%d hours"% hours)
    if minutes != 0:
        readable.append("%d minutes"% minutes)
    return " and ".join(readable)


def get_breaks(race, racer_id):
    '''
    given a race id and id of a user, return off-saddle data
    '''
    spot_url = SPOT_URL_TEMPL% (race, racer_id)
    spot_feed = requests.get(spot_url, headers={'User-Agent': USER_AGENT}).text
    as_date = make_datetime_converter()
    timestamps = parse_timestamps(racer_id, spot_feed)
    positions = list(SPOT_POS_RE.finditer(spot_feed, re.MULTILINE))
    miles = [float(matched.group('mile'))
                for matched in  MILE_RE.finditer(spot_feed, re.MULTILINE)
                if matched]
    breaks = []
    tot_duration = 0
    for i, ts in enumerate(timestamps):
        if i >= len(positions) or i >= len(timestamps)-1:
            break
        ts2 = timestamps[i+1]
        matched_pos = positions[i] 
        break_start, break_end = as_date(ts), as_date(ts2)
        mile1, mile2 = miles[i], miles[i+1]

        delta = break_end - break_start
        if delta < MIN_STOP_TIME:
            continue

        duration = delta.total_seconds()
        duration_hr = float(duration) / 3600
        avg_mph = (mile2-mile1) / duration_hr
        if avg_mph > STOP_SPEED:
            continue

        tot_duration += duration
        lat = float(matched_pos.group('latitude'))
        lng = float(matched_pos.group('longitude'))
        breaks.append({
            'start': break_start.isoformat(),
            'end': break_end.isoformat(),
            'duration': duration,
            'lat': lat,
            'lng': lng
        })

    if breaks:
        # coalesce contiguous breaks
        coalesced_breaks = [breaks[0]]
        prev = breaks[0]
        i = 1
        while i < len(breaks):
            cur = breaks[i]
            if cur['start'] == prev['end']:
                prev['end'] = cur['end']
                prev['duration'] += cur['duration']
            else:
                coalesced_breaks.append(cur)
                prev = cur
            i += 1

        breaks = coalesced_breaks

    # calculate percentage
    for brk in breaks:
        dur = brk['duration']
        brk['duration'] = '%s (%.2f%% of %s)'% (
                to_readable_duration(dur), 
                dur/tot_duration*100,
                to_readable_duration(tot_duration))
    return breaks, tot_duration


def get_racers(race_id):
    page = HTML(requests.get(TL_URL_TEMPL% race_id, headers={'User-Agent': USER_AGENT}).text)
    racers = set(el.text for el in page.xpath('.//a[@onmouseout]'))
    return list(racers)


def get_race_name(race_id):
    page = HTML(requests.get(TL_URL_TEMPL% race_id, headers={'User-Agent': USER_AGENT}).text)
    return page.findtext('.//title').split('live')[0].strip()
