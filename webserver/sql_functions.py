import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
import random, requests

# Use the DB credentials you received by e-mail
DB_USER = "ds3731"
DB_PASSWORD = "wnw0NiHKMr"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"

#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)

#
# Functions used for \login
#
def check_login(username, home_zip):
    with engine.connect() as conn:
        cursor = conn.execute("""select * \
                                from users \
                                where username = %s""", username).fetchone()
        if cursor == None:
            return 'error_user'

        else:
            if cursor['home_zip'] == home_zip:
                return cursor['name']

            else:
                return 'error-combo'

#
# Functions used for \home
#
def get_history(username):
    with engine.connect() as conn:
        cursor = conn.execute("""select zipcode, date_time, rec_number \
                                from recommended \
                                where username = %s\
                                """, username)
        history = []
        for row in cursor:
            history.append(row)
        return history

#
# Functions used for \recommendation
    degree = int(degree)
#
def get_recommendation(degree, probability):
    rec_num = 0
    recommendation = ''
    with engine.connect() as conn:
        rec_number = conn.execute("""select rec_number \
                                from forms \
                                where degree = {degree} \
                                and probability = {probability}""".format(degree=degree, probability=probability)).fetchone()
        recommendation = conn.execute("""select comment\
                                from recommendation \
                                where rec_number = {rec_number}""".format(rec_number=rec_number[0])).fetchone()


        return recommendation['comment']


def get_weather(zipcode):
    link = 'http://api.openweathermap.org/data/2.5/weather?zip='+zipcode+',us'
    apikey = '&appid=94a9f2ccdfedac6327e3e82974f4a5b5'
    result = requests.get(link+apikey)
    json_object = result.json()
    temp_kelvin = float(json_object['main']['temp'])
    temp_fr = (temp_kelvin - 273.15) * 1.8 + 32
    main_id = json_object['weather'][0]['id']
    weather_description = json_object['weather'][0]['description']

    return temp_fr, main_id, weather_description


def approx_probability(main_id):
    probability = 0
    if main_id >= 200 and main_id < 300:
        probability = 100
    if main_id >= 300 and main_id < 400:
        if main_id in [312, 313, 314, 321]:
            probability = random.randint(75, 90)
        else:
            probability = random.randint(30, 50)
    if main_id >= 500 and main_id < 600:
        if main_id in [500, 501]:
            probability = random.randint(45, 55)
        if main_id == 531:
            probability = random.randint(30, 100)
        else:
            probability = random.randint(65, 90)
    if main_id >= 600 and main_id < 700:
        probability = random.randint(75, 100)
    return probability

def get_city(zipcode):
    with engine.connect() as conn:
        row = conn.execute("""select city, state_abbrev \
                                from location \
                                where zipcode = '{}' """.format(zipcode)).fetchone()
        city = row['city']
        state = row['state_abbrev']
        return city, state

def check_username(username):
    with engine.connect() as conn:
        cursor = conn.execute("""select username \
                                from users \
                                where username = '{}' """.format(username)).fetchone()
        if cursor == None:
            return 'username valid'

        else:
            return 'username invalid'

def check_zipcode(zipcode):
    with engine.connect() as conn:
        cursor = conn.execute("""select * \
                                from location \
                                where zipcode = '{}' """.format(zipcode)).fetchone()
        if cursor == None:
            return 'zipcode invalid', None, None

        else:
            city = cursor['city']
            state = cursor['state']
            return 'zipcode valid', city, state

# def insert_new_user(username, zipcode, name):
#     cmd = 'INSERT INTO usernames VALUES (:name1), (:name2)';
#     with engine.connect() as conn:

# Example of adding new data to the database
# @app.route('/add', methods=['POST'])
# def add():
#   name = request.form['name']
#   print name
#   cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
#   g.conn.execute(text(cmd), name1 = name, name2 = name);
#   return redirect('/')



