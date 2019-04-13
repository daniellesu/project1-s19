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

        #insert_1 = conn.execute(""" INSERT INTO user_input_location (username, zipcode, date_time) VALUES(%s, %s, %s) """, (username, zipcode, time))
        
        #insertion = conn.execute(""" INSERT INTO retrieve_temp_precip (date_time, degree, real_feel, probability, username, zipcode) VALUES (%s,%s,%s,%s,%s,%s)""", (date_time, degree, real_feel, probability, username, zipcode))


        history = []
        for row in cursor:
            history.append(row)
        return history

def insert1(username, zipcode, date_time):
    with engine.connect() as conn:
        insert_1 = conn.execute(""" INSERT INTO user_input_location (username, zipcode, date_time) VALUES(%s, %s, %s) """, (username, zipcode, time))
        
        return home

def insert2(date_time, degree, probability, username, zipcode):
    with engine.connect() as conn:
        #did we put in real_feel???
        insert_2 = conn.execute(""" INSERT INTO retrieve_temp_precip (date_time, degree, probability, username, zipcode) VALUES (%s,%s,%s,%s,%s)""", (date_time, degree, probability, username, zipcode))

        return home

def insert3(username, zipcode, date_time, rec_number):
    with engine.connect() as conn:
        insert_3 = conn.execute(""" INSERT INTO recommended (username, zipcode, date_time, rec_number) VALUES (%s, %s, %s, %s)""", (username, zipcode, date_time, rec_number))

        return home

#Functions used for \recommendation
#
def get_recommendation(degree, probability):
    degree = int(degree)
    rec_num = 0
    recommendation = ''
    with engine.connect() as conn:
        rec_number = conn.execute("""select rec_number \
                                from forms \
                                where degree = {degree} \
                                and probability = {probability}""".format(degree=degree, probability=probability)).fetchone()
        recommendation = conn.execute("""select comment\
                                from recommendation \
                                where rec_number = {rec_number}""".format(rec_number=rec_number['rec_number'])).fetchone()
        if rec_number == None or recommendation == None:
            return "uh oh someting's gone wrong"

        return recommendation['comment']


def get_weather(zipcode):
    link = 'http://api.openweathermap.org/data/2.5/weather?zip='+zipcode+',us'
    apikey = '&appid=94a9f2ccdfedac6327e3e82974f4a5b5'
    result = requests.get(link+apikey)
    json_object = result.json()
    temp_kelvin = float(json_object['main']['temp'])
    temp_fr = (temp_kelvin - 273.15) * 1.8 + 32
    #real_feel = temp_fr
    main_id = json_object['weather'][0]['id']
    weather_description = json_object['weather'][0]['description']

    return temp_fr, main_id, weather_description #, real_feel


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

def get_image(main_id):
    
    if main_id >= 200 and main_id <300:
        image_id = '11d'
        icon = 'http://openweathermap.org/img/w/11d.png'
    
    if main_id >=300 and main_id<400:
        image_id = '09d'
        icon = 'http://openweathermap.org/img/w/09d.png'

    if main_id >= 500 and main_id<600:
        image_id = '10d'
        icon = 'http://openweathermap.org/img/w/10d.png'

    if main_id >= 600 and main_id <700:
        image_id = '13d'
        icon = 'http://openweathermap.org/img/w/13d.png'

    if main_id >= 700 and main_id <800:
        image_id = '50d'
        icon = 'http://openweathermap.org/img/w/50d.png'

    if main_id== 800:
        image_id = '01d'
        icon = 'http://openweathermap.org/img/w/01d.png'

    if main_id >800:
        image_id = '02d'
        icon = 'http://openweathermap.org/img/w/02d.png'

    return icon

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



