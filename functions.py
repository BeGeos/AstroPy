from datetime import datetime, timedelta
from models import User, AuthKeys
import requests
import re
import string
import random
import smtplib
from email.message import EmailMessage

# Email smtp setup for sending emails [environment variables]
EMAIL_ADDRESS = 'YOUR_EMAIL_ADDRESS'
EMAIL_PASSWORD = 'YOUR_APP_PASSWORD'


# Api Token generator
def key_generator(num=24):
    alphanumeric = string.ascii_letters + string.digits
    key = ''
    for _ in range(1, num + 1):
        key += random.choice(alphanumeric)
    return key


# Security code generator
def code_generator(num=6):
    numbers = string.digits
    code = ''
    for _ in range(1, num + 1):
        code += random.choice(numbers)
    return int(code)


# URL extension generator
def ext_generator(num=24):
    alphabet = string.ascii_letters
    extension = ''
    for _ in range(1, num + 1):
        extension += random.choice(alphabet)
    return extension


# Check for user authentication credentials
def is_username_available(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return False
    return True


# Send email with security code
def email_security_code(username, email, security_code):

    msg = EmailMessage()
    msg['Subject'] = '[AstroPy] - Please confirm you email address'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email
    msg.set_content(f"""Hey {username}!\n 
Thank you for signing up. 
To complete the procedure and finally get to use this API, send a post request to the link below, and make sure 
to include in the body your username and the security code\n\n
Link: http://localhost:5000/astropy/api/v1/verification
Security code: {security_code}\n\n
This code will be active for 10 minutes, after that you can request a new one at the following link\n
http://localhost:5000/astropy/api/v1/new-code-request\n
In that case send a post request specifying in the body your username and password, a new email like this 
one will be sent promptly with a new security code.\n\n
If you did not send this request to sign up, your email address might have been used illicitly.\n\n
Thank you very much for your cooperation and support. I am extremely grateful that you decided to use this 
service. I hope you find it useful and it can enhance your astronomical observation experience.\n\n
\n\nThanks,\n@BeGeos - AstroPy""")
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        smtp.send_message(msg)


# Send email for recover password link
def email_recovery_password(username, email, recovery_link):
    msg = EmailMessage()
    msg['Subject'] = '[AstroPy] - Password recovery request'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email
    msg.set_content(f"""Hey {username}!\n  
It seems like somebody made a request to recover/change your password.
If you want to update the password send a post request to the link below. In the body of your request, 
include your username and the new password.\n\n
Link: {recovery_link}\n
This link will be active for 24 hours, after that you can request a new one at the following link
http://localhost:5000/astropy/api/v1/recovery\nand follow the steps for recovering your password.\n
In case you did not send any request but still received this message, your username and email were used illicitly.
\nYou could either skip this message or if you were worried about security issues contact this link\n
http://localhost/astropy/security
\n\nThanks,\n@BeGeos - AstroPy""")
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        smtp.send_message(msg)


def is_email_available(email):
    _email = User.query.filter_by(email=email).first()
    if _email:
        return False
    return True


# Email API check
def does_email_exist(email):
    pass


def sun_time_from_api(lat, lon):
    """ Send API call to OpenWeatherAPI for sunrise and sunset time at location """

    url = 'https://api.openweathermap.org/data/2.5/weather?'
    api_key = ''
    payload = {'lat': lat, 'lon': lon, 'appid': api_key}
    get_request = requests.get(url, params=payload)
    if get_request.status_code != 200:
        print(get_request.status_code)
        return
    api_response = get_request.json()

    timezone = api_response['timezone']
    sunrise = datetime.utcfromtimestamp(api_response['sys']['sunrise']) + timedelta(seconds=timezone)
    # print(sunrise, '-- sunrise')
    sunset = datetime.utcfromtimestamp(api_response['sys']['sunset']) + timedelta(seconds=timezone)

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
        star_rise = sunrise - abs(closest_delay)
        if star_rise < 0:
            star_rise += 24
    elif - 1 <= closest_delay <= 1:
        return 'This star is not observable now'
    if star_rise == 24:
        star_rise -= 24
    star_set = star_rise + 12
    if star_set >= 24:
        star_set -= 24

    # TODO Calculate the available hours of darkness for observation
    day = [d for d in range(sunrise, sunset)]
    star_span = [h for h in range(star_rise, star_set)]

    return {'star rise': star_rise, 'star set': star_set,
            'day': day, 'star span': star_span, 'closest delay': closest_delay}


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


# API call for coordinates from city name -- OpenCage Geocoding
def geocoding_api(city):
    url_geocoding = 'https://api.opencagedata.com/geocode/v1/json?'
    api_key = ''
    payload = {'q': city, 'key': api_key, 'limit': 1}
    request = requests.get(url_geocoding, params=payload)
    file = request.json()

    output = {}

    if file['results']:
        output['lat'] = file['results'][0]['annotations']['DMS']['lat']
        output['lon'] = file['results'][0]['annotations']['DMS']['lng']
    else:
        output = None

    return output


# Formatting of latitude and longitude
def check_if_north(lat):
    check_lat = re.findall('(.[0-9]*)°', lat)
    if 'S' in lat:
        result = '-' + str(*check_lat)
        result = int(result)
    else:
        result = int(*check_lat)
    return result


def check_if_east(lon):
    check_lon = re.findall('(.[0-9]*)°', lon)
    if 'W' in lon:
        result = '-' + str(*check_lon)
        result = int(result)
    else:
        result = int(*check_lon)
    return result
