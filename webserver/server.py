#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Weather Vane Application
Danielle Su and Shadi Fadaee


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
                          insert_rec_history, get_numstates, get_topcity
                          )

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

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

  top_city, top_state = get_topcity(username)
  num_states = get_numstates(username)
  if top_city == None:
    message = 'No search history yet!'
    context = dict(data=history, name=name, search_no=message, num_states=num_states)
  else:
    context = dict(data=history, name=name, top_city=top_city, top_state=top_state, num_states=num_states)

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
    flash('You have successfully logged in!')
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


@app.route('/register_account', methods=['POST'])
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


@app.route('/register_success')
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

  return render_template('change_homezip.html')

@app.route('/change_name', methods=['POST'])
def change_name():
  username = session.get('username')
  new_name = request.form['firstname']

  # Function to update name
  update_name(username, new_name)

  session.clear()

  return render_template('change_name.html')

# Function for recommendation
def render_rec(zipcode):
  username = session.get('username')
  check = check_zipcode(zipcode)

  if check[0] == "zipcode invalid":
    error = "zipcode invalid"
    return render_template('error.html', error=error)

  else:
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

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
