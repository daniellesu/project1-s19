import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
import random, requests, datetime

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
        history = conn.execute("""select r.zipcode, r.date_time, recommendation.comment \
                                from recommended as r, recommendation \
                                where r.username = '{}' \
                                and r.rec_number = recommendation.rec_number
                                order by date_time DESC \
                                """.format(username)).fetchall()
        # for row in cursor:
        #     history.append(row)

        return history
print get_history('user1')


def insert_rec_history(username, zipcode, deg, prob, rec_num):
    with engine.connect() as conn:
        time = conn.execute("select current_timestamp::timestamp(0)").fetchone()['current_timestamp']
        cmd1 = "insert into user_input_location \
                (username, zipcode, date_time) \
                values (%s, %s, %s);"
        conn.execute(cmd1, (username, zipcode, time))

        cmd2 = "insert into retrieve_temp_precip \
                (degree, probability, username, zipcode, date_time) \
                values (%s, %s, %s, %s, %s);"
        conn.execute(cmd2, (deg, prob, username, zipcode, time))

        cmd3 = "insert into recommended\
                (username, zipcode, date_time, rec_number) \
                values (%s, %s, %s, %s);"
        conn.execute(cmd3, (username, zipcode, time, rec_num))
#
#Functions used for \register
#
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

def insert_user(username, home_zip, name):
    with engine.connect() as conn:
        if name == None or name == '':
            cmd = "insert into users \
                (username, home_zip) \
                values ('{}', '{}')".format(username, home_zip)
        else:
            cmd = "insert into users \
                    (username, home_zip, name) \
                    values ('{}', '{}', '{}')".format(username, home_zip, name)

        conn.execute(text(cmd))

        # # check to see if it was inserted
        # table = conn.execute("""select * \
        #                         from users \
        #                         where username = '{}' \
        #                         """.format(username)).fetchall()
        # return table

#
#Functions used for \change_account
#
def update_homezip(username, home_zip):
    with engine.connect() as conn:
        cmd = """update users \
                set home_zip = '{}' \
                where username = '{}' """.format(home_zip, username)
        conn.execute(text(cmd))

        # # check to see if it was inserted
        # table = conn.execute("""select * \
        #                         from users \
        #                         where username = '{}' \
        #                         """.format(username)).fetchall()
        # return table

def update_name(username, name):
    with engine.connect() as conn:
        cmd = """update users \
                set name = '{}' \
                where username = '{}' """.format(name, username)
        conn.execute(text(cmd))

        # # check to see if it was inserted
        # table = conn.execute("""select * \
        #                         from users \
        #                         where username = '{}' \
        #                         """.format(username)).fetchall()
        # return table

#
#Functions used for \recommendation
#
def get_recommendation(degree, probability):
    with engine.connect() as conn:
        rec_number = conn.execute("""select rec_number \
                                from forms \
                                where degree = {} \
                                and probability = {}""".format(degree, probability)).fetchone()['rec_number']

        recommendation = conn.execute("""select comment \
                                from recommendation \
                                where rec_number = {}""".format(rec_number)).fetchone()['comment']

        if rec_number == None or recommendation == None:
            return "uh oh someting's gone wrong"

        return recommendation, rec_number


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



