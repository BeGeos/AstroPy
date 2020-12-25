from datetime import datetime, timedelta
import requests


def sun_time_from_api(lat, lon):
    """ Send API call to OpenWeatherAPI for sunrise and sunset time at location"""

    url = 'https://api.openweathermap.org/data/2.5/weather?'
    api_key = 'b7adec848b0680cb9a2518e37b256861'
    payload = {'lat': lat, 'lon': lon, 'appid': api_key}
    get_request = requests.get(url, params=payload)
    if get_request.status_code != 200:
        print(get_request.status_code)
        return
    api_response = get_request.json()

    timezone = api_response['timezone']
    sunrise = datetime.fromtimestamp(api_response['sys']['sunrise']) + timedelta(seconds=timezone)
    sunset = datetime.fromtimestamp(api_response['sys']['sunset']) + timedelta(seconds=timezone)

    sunrise = float(sunrise.strftime('%H.%M'))
    sunset = float(sunset.strftime('%H.%M'))

    return {'sunrise': sunrise, 'sunset': sunset,
            'utc': timezone}


def star_rising_time(ra, sun_times: dict):
    vernal_equinox = datetime(2020, 3, 21)

    # From API call
    sunrise = int(sun_times['sunrise'])
    sunset = int(sun_times['sunset'])

    # Theory of right ascension
    time_of_year = {
        vernal_equinox: ra,
        datetime(2020, 4, 21): ra - 2,
        datetime(2020, 5, 21): ra - 4,
        datetime(2020, 6, 21): ra - 6,
        datetime(2020, 7, 21): ra - 8,
        datetime(2020, 8, 21): ra - 10,
        datetime(2020, 9, 21): ra - 12,
        datetime(2020, 10, 21): ra - 14,
        datetime(2020, 11, 21): ra - 16,
        datetime(2020, 12, 21): ra - 18,
        datetime(2020, 1, 21): ra - 20,
        datetime(2020, 2, 21): ra - 22,

    }

    # Find the closest date to today in the dictionary time_of_year
    today = datetime.today()
    base = timedelta(days=366)
    for k, v in time_of_year.items():
        delta = k - today
        if abs(delta) < base:
            closest_delay = time_of_year[k]
            base = abs(delta)

    # Find the rise time of the star if it's lower than 1 it means the star rises and sets
    # along whit the Sun, therefore there is no time when it becomes observable
    if closest_delay > 1:
        star_rise = sunrise + closest_delay
    elif closest_delay < - 1:
        star_rise = sunrise - closest_delay
        if star_rise < 0:
            star_rise += 24
    elif - 1 <= closest_delay <= 1:
        return 'This star is not observable now'
    star_set = star_rise + 12
    if star_set >= 0:
        star_set -= 24

    # TODO Calculate the available hours of darkness for observation
    day = [d for d in range(sunrise, sunset)]
    star_span = [h for h in range(star_rise, star_set)]

    return {'star rise': star_rise, 'star set': star_set,
            'day': day, 'star span': star_span}


# TODO improve calculate position
def calculate_position(rise_time: int, utc: int):
    # Circle divided 24h
    step = 360 / 24

    # Comparison between now and the time the star has risen
    now = datetime.utcnow() + timedelta(seconds=utc)
    rise_dt = datetime(2020, 3, 21, rise_time, 0, 0)

    delta_t = now - rise_dt
    hours_passed = int(delta_t.seconds / 3600)
    travelled_degrees = hours_passed * step

    if 180 <= travelled_degrees < 360:
        return 'It has already set'
    if travelled_degrees == 360 or travelled_degrees == 0:
        return "It's rising now"

    return f'It is {travelled_degrees}° from the east'


