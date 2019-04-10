import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
import random

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
        cursor = conn.execute("select * from users")
        for row in cursor:
            if row['username'] == username:
                name = row['name']
                if row['home_zip'] == home_zip:
                    return name
                    break
                else:
                    return 'error_combo'
                    break
    return 'error_user'

#
# Functions used for \home
#
def get_history(username):
    with engine.connect() as conn:
        cursor = conn.execute("select * \
                                from recommended")
        history = []
        for row in cursor:
            if row['username'] == username:
                history.append(row[1:])
        return history

#
# Functions used for \recommendation
#
def get_recommendation(zipcode):
    degree = random.randint(-10, 100)
    probability = random.randint(0, 100)
    rec_num = 0
    recommendation = ''
    with engine.connect() as conn:
        cursor = conn.execute("select * \
                                from forms")
        for row in cursor:
            if row['degree'] == degree:
                if row['probability'] == probability:
                    rec_num = row['rec_number']
                    break

        cursor = conn.execute("select * \
                                from recommendation")
        for row in cursor:
            if row['rec_number'] == rec_num:
                recommendation = row['comment']
                break

    return recommendation

        # clothing = conn.execute("select clothing_group \
        #                         from matches_clothing \
        #                         where degree= ?", (degree,)).fetchone()
        # print clothing






