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
from flask import Flask
from flask import Flask, flash, request, render_template, g, redirect, Response, session, abort, url_for
from sql_functions import check_login, get_history, get_recommendation, get_weather, approx_probability

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
  message = 'Welcome, %s' % (session['name'])
  flash(message)

  username = session.get('username')
  history = get_history(username)
  context = dict(data = history)

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
    session['name'] = check
    # return home()
    return redirect(url_for('home'))



@app.route('/logout')
def logout():
   # remove the username from the session if it is there
   session.pop('username', None)
   session.pop('home_zip', None)
   session.pop('name', None)
   return redirect(url_for('index'))


@app.route('/home_recommendation')
def home_recommendation():
  home_zip = session.get('home_zip')
  degree, main_id, weather_description = get_weather(home_zip)
  probability = approx_probability(main_id)
  recommendation = get_recommendation(degree, probability)
  data = {'zipcode': home_zip,
          'degree': degree,
          'weather_description': weather_description,
          'recommendation': recommendation}

  return render_template("recommendation.html", recommendation=recommendation, zipcode=home_zip, data=data)


@app.route('/recommendation', methods=['POST'])
def recommendation():
  zipcode = request.form['zipcode']
  degree, main_id, weather_description = get_weather(zipcode)
  probability = approx_probability(main_id)
  recommendation = get_recommendation(degree, probability)
  data = {'zipcode': zipcode,
          'degree': degree,
          'weather_description': weather_description,
          'recommendation': recommendation}

  return render_template("recommendation.html", recommendation=recommendation, zipcode=zipcode, data=data)

# Example of adding new data to the database
# @app.route('/add', methods=['POST'])
# def add():
#   name = request.form['name']
#   print name
#   cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
#   g.conn.execute(text(cmd), name1 = name, name2 = name);
#   return redirect('/')



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
