from flask import Flask, render_template, request, redirect, jsonify, \
    url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Tourism, Destination, User

# Import Login session

from flask import session as login_session
import random
import string

# imports for gconnect

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

# import login decorator

from functools import wraps

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r')
                       .read())['web']['client_id']
APPLICATION_NAME = 'Tourism Application'

engine = create_engine('sqlite:///skytravels.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_name' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login')
def showlogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():

    # validate state token

    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application-json'
        return response

    # Obtain authorization code

    code = request.data

    try:

        ''' upgrade the authorization code in credentials object '''

        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response =\
                   make_response(json.dumps('Failed to upgrade\
                   the authorization  code'), 401)
        response.headers['Content-Type'] = 'application-json'
        return response

    # Check that the access token is valid.

    access_token = credentials.access_token
    url = \
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' \
        % access_token
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1].decode('utf-8'))
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.

    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = \
            make_response(json.dumps("user ID doesn't match\
            givenuser ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    if result['issued_to'] != CLIENT_ID:
        response = \
            make_response(json.dumps("client ID does not match app's."), 401)
        print "client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = \
            make_response(json.dumps('Current user is already\
            connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    response = make_response(json.dumps('Succesfully connected', 200))

    # Get user information

    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    print 'User email is' + str(login_session['email'])
    user_id = getUserID(login_session['email'])
    if user_id:
        print 'Existing user#' + str(user_id) + 'matches this email'
    else:
        user_id = createUser(login_session)
        print 'New user_id#' + str(user_id) + 'created'
    login_session['user_id'] = user_id
    print 'Login session is tied to :id#' + str(login_session['user_id'])

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += \
        ' " style = "width: 300px; height: 300px;border-radius:150px;- \
      webkit-border-radius:150px;-moz-border-radius: 150px;">'
    flash('you are now logged in as %s' % login_session['username'])
    print 'done!'
    return output


def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).first()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).first()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).first()
        return user.id
    except:
        return None
''' DISCONNECT - Revoke a current user's token and reset their login_session'''


@app.route('/gdisconnect')
def gdisconnect():

    # only disconnect a connected User

    access_token = login_session.get('access_token')
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
        % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is'
    print result
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:

        response = \
            make_response(json.dumps('Failed to revoke token for\
            given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/logout')
def logout():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash('you have succesfully been logout')
        return redirect(url_for('places'))


@app.route('/tourist/<int:tourist_id>/area/JSON')
def touristMenuJSON(tourist_id):
    tourist = session.query(Tourism).filter_by(id=tourist_id).one()
    looks = \
        session.query(Destination).filter_by(tourist_id=tourist_id).all()
    return jsonify(Destinations=[a.serialize for a in looks])


@app.route('/tourist/<int:tourist_id>/area/<int:area_id>/JSON')
def spotJSON(tourist_id, area_id):
    pack = session.query(Destination).filter_by(id=area_id).one()
    return jsonify(pack=pack.serialize)


@app.route('/tourist/JSON')
def touristsJSON():
    tourists = session.query(Tourism).all()
    return jsonify(tourists=[r.serialize for r in tourists])


# Show all Tourist Places

@app.route('/')
@app.route('/tourist/')
def places():
    tourists = session.query(Tourism).all()
    return render_template('tourists.html', tourists=tourists)


# Create a new tourists

@app.route('/tourist/new/', methods=['GET', 'POST'])
def newTourism():
    if 'username' not in login_session:
        return redirect('/login')
    if Tourism.user_id != login_session['user_id']:
        return "<script>function myFunction(){alert('You are not authorized to\
        create this touristplace. please create your own touristplace in order\
        to create.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        newTourism = Tourism(name=request.form['name'])
        session.add(newTourism)
        session.commit()
        return redirect(url_for('places'))
    else:
        return render_template('newTourism.html')
    
    # return "This page will be for making a newtourists"
    # Edit a tourist place


@app.route('/tourist/<int:tourist_id>/edit/', methods=['GET', 'POST'])
def editTourism(tourist_id):
    if 'username' not in login_session:
        return redirect('/login')
    if Tourism.user_id != login_session['user_id']:
        return "<script>function myFunction(){alert('You are not authorized to\
        edit this touristplace. please create your own touristplace in order\
        to edit.');}</script><body onload='myFunction()'>"
    editedTourism = \
        session.query(Tourism).filter_by(id=tourist_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedTourism.name = request.form['name']
            return redirect(url_for('places'))
    else:
        return render_template('editTourism.html',
                               tourist=editedTourism)
    
    # return 'This page will be for editing tourist %s' %tourists_id
    # Delete a tourist place


@app.route('/tourist/<int:tourist_id>/delete/', methods=['GET', 'POST'])
def deleteTourism(tourist_id):
    if 'username' not in login_session:
        return redirect('/login')
    if Tourism.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('you are not authorized to\
         delete this tourist.please create your own tourist to delete');}\
         </script><body onLoad = 'myFunction()'>"
    touristToDelete = \
        session.query(Tourism).filter_by(id=tourist_id).one()
    if request.method == 'POST':
        session.delete(touristToDelete)
        session.commit()
        return redirect(url_for('places', tourist_id=tourist_id))
    else:
        return render_template('deleteTourism.html',
                               tourist=touristToDelete)
    
    # return 'This page will be for deleting tourist %s' % tourists_id
    ''' Show a tourist spot'''


@app.route('/tourist/<int:tourist_id>/')
@app.route('/tourist/<int:tourist_id>/area/')
def showplace(tourist_id):
    if 'username' not in login_session:
        return redirect('/login')
    tourist = session.query(Tourism).filter_by(id=tourist_id).one()
    looks = \
        session.query(Destination).filter_by(tourist_id=tourist_id).all()
    return render_template('area.html', looks=looks, tourist=tourist)
    # return 'This page is the look for tourist %s' % tourist_id
    # Create a new spot


@app.route('/tourist/<int:tourist_id>/area/new/', methods=['GET', 'POST'])
def newDestination(tourist_id):
    if 'username' not in login_session:
        return redirect('/login')
    if login_session['user_id'] != Destination.user_id:
        return "<script>function myFunction() {alert('You are not authorized to\
          create spots to this tourist.Please create your own tourist in\
          order to create spots.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        newlook = Destination(name=request.form['name'],
                              details=request.form['details'],
                              charge=request.form['charge'],
                              course=request.form['course'],
                              tourist_id=tourist_id)
        session.add(newlook)
        session.commit()

        return redirect(url_for('showplace', tourist_id=tourist_id))
    else:
        return render_template('newspot.html', tourist_id=tourist_id)

    return render_template('newDestination.html', tourist=tourist)
    
    # return 'This page is for making a new spot for tourist places %s'
    # %tourist_id
    # Edit a spot


@app.route('/tourist/<int:tourist_id>/area/<int:area_id>/edit',
           methods=['GET', 'POST'])
def editDestination(tourist_id, area_id):
    if 'username' not in login_session:
        return redirect('/login')
    if login_session['user_id'] != Destination.user_id:
        return "<script>function myFunction() {alert('You are not authorized to\
          edit spots to this tourist.Please create your own tourist in\
          order to edit spots.');}</script><body onload='myFunction()'>"
    editedlook = session.query(Destination).filter_by(id=area_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedlook.name = request.form['name']
        if request.form['details']:
            editedlook.details = request.form['name']
        if request.form['charge']:
            editedlook.price = request.form['charge']
        if request.form['course']:
            editedlook.course = request.form['course']
        session.add(editedlook)
        session.commit()
        return redirect(url_for('showplace', tourist_id=tourist_id))
    else:

        return render_template('editspot.html', tourist_id=tourist_id,
                               area_id=area_id, look=editedlook)
    
        # return 'This page is for editing spot %s' % area_id
        # Delete a spot


@app.route('/tourist/<int:tourist_id>/area/<int:area_id>/delete',
           methods=['GET', 'POST'])
def deleteDestination(tourist_id, area_id):
    if 'username' not in login_session:
        return redirect('/login')
    if login_session['user_id'] != Destination.user_id:
        return "<script>function myFunction() {alert ('you are not authorized to\
         delete spots to this tourist.please create your own tourist\
         in order to delete spots');}</script><body onload='myFunction()'>"

    lookToDelete = \
        session.query(Destination).filter_by(id=area_id).one()

    if request.method == 'POST':
        session.delete(lookToDelete)
        session.commit()
        return redirect(url_for('showplace', tourist_id=tourist_id))
    else:
        return render_template('deleteDestination.html',
                               look=lookToDelete)
    
    # return "This page is for deleting spot %s" %area_id

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
