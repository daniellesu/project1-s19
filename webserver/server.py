#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import (
                  Flask, flash, request, render_template, g,
                  redirect, Response, session, abort, url_for
                  )
from sql_functions import (
                          check_login, get_history, get_recommendation,
                          get_weather, approx_probability, get_city,
                          check_username, check_zipcode, get_image,
                          insert_user, update_homezip, update_name,
                          insert_rec_history
                          )

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


# XXX: The Database URI should be in the format of:
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "ds3731"
DB_PASSWORD = "wnw0NiHKMr"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/

  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """
  # DEBUG: this is debugging code to see what request looks like
  # print request.args

@app.route('/')
def index():
  if session.get('username') == None:
    return render_template('index.html')

  else:
    return redirect(url_for('home'))


@app.route('/home')
def home():
  if session.get('username') == None:
    return redirect(url_for('index'))

  username = session.get('username')
  history = get_history(username)

  if session.get('name') != None:
    name = session.get('name')
  else:
    name = username

  context = dict(data=history, name=name)

  return render_template("home.html", **context)


@app.route('/login', methods=['POST'])
def login():
  error = None

  check = check_login(request.form['username'], request.form['home_zip'])

  if check == 'error-combo':
    error = 'Invalid username/home zipcode combination'
    session.pop('username', None)
    session.pop('home_zip', None)
    session.pop('name', None)
    return render_template('login.html', error=error)

  elif check == 'error_user':
    error = 'Username not found'
    session.pop('username', None)
    session.pop('home_zip', None)
    session.pop('name', None)
    return render_template('login.html', error=error)

  else:
    flash('You were successfully logged in!')
    session['username'] = request.form['username']
    session['home_zip'] = request.form['home_zip']

    if check != None:
      session['name'] = check

    return redirect(url_for('home'))

#
# Create new account page
#
@app.route('/register')
def register():
  return render_template('register.html')


@app.route('/register/account', methods=['POST'])
def register_account():
  error = None
  username = request.form['username']
  home_zip = request.form['home_zip']
  name = request.form['firstname']

  username_valid = check_username(request.form['username'])
  zipcode_valid, city, state = check_zipcode(request.form['home_zip'])

  if username_valid == 'username invalid':
    error = "That username is taken, please try another username."
    return render_template('register.html', error=error)

  if zipcode_valid == 'zipcode invalid':
    error = "That zipcode is invalid. Please enter a zipcode in the United States."
    return render_template('register.html', error=error)

  else:
    insert_user(username, home_zip, name)
    return redirect(url_for('register_success'))


@app.route('/register/success')
def register_success():
  return render_template('register_success.html')


@app.route('/logout')
def logout():
   # remove the username from the session if it is there
   session.pop('username', None)
   session.pop('home_zip', None)
   session.pop('name', None)
   return redirect(url_for('index'))

@app.route('/change_account')
def change_account():
  username = session.get('username')
  home_zip = session.get('home_zip')
  name = session.get('name')
  data = {'username': username,
          'home_zip': home_zip,
          'name': name}
  return render_template('change_account.html', data=data)


@app.route('/change_homezip', methods=['POST'])
def change_homezip():
  username = session.get('username')
  new_home_zip = request.form['home_zip']

  # Function to update home_zip
  update_homezip(username, new_home_zip)

  session.clear()
  # session.pop('username', None)
  # session.pop('home_zip', None)
  # session.pop('name', None)

  return render_template('change_homezip.html')

@app.route('/change_name', methods=['POST'])
def change_name():
  username = session.get('username')
  new_name = request.form['firstname']

  # Function to update name
  update_name(username, new_name)

  session.clear()
  # session.pop('username', None)
  # session.pop('home_zip', None)
  # session.pop('name', None)

  return render_template('change_name.html')

# Function for recommendation
def render_rec(zipcode):
  username = session.get('username')
  check = check_zipcode(zipcode)

  if check == "zipcode invalid":
    error = "zipcode invalid"
    return redirect(url_for('home'), error=error)

  degree, main_id, weather_description = get_weather(zipcode)
  degree = int(degree)
  probability = approx_probability(main_id)
  recommendation, rec_number = get_recommendation(degree, probability)
  icon = get_image(main_id)
  city, state = get_city(zipcode)
  data = {'zipcode': zipcode,
          'city': city,
          'state': state,
          'degree': degree,
          'icon': icon,
          'weather_description': weather_description,
          'recommendation': recommendation}

  insert_rec_history(username, zipcode, degree, probability, rec_number)

  return render_template("recommendation.html", data=data)


@app.route('/recommendation', methods=['POST'])
def recommendation():
  zipcode = request.form['zipcode']
  return render_rec(zipcode)

@app.route('/home_recommendation')
def home_recommendation():
  zipcode = session.get('home_zip')
  return render_rec(zipcode)



if __name__ == "__main__":
  app.secret_key = os.urandom(12)
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
