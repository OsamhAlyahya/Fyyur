#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
from models import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
db = database_Connection(app) #from models

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  """Fetches all venues data in the venues table.

  Args:
    None.
  returns:
    areas: All the venues data in venues table.  
  """
  final_data =[]

  city_State_Query = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state)

  for city_State in city_State_Query:
    venues_data = []
    venues = db.session.query(Venue.id, Venue.name).filter(Venue.city == city_State.city).filter(Venue.state == city_State.state)
    for venue in venues:
      venue_Upcoming_Shows_Number = db.session.query(Show).join(Venue).filter(Show.start_time > datetime.now(), Show.venue_id == Venue.id).count()
      venues_data.append({
        "id": venue.id,
        "name":venue.name,
        "num_upcoming_shows": venue_Upcoming_Shows_Number
      })
    final_data.append({
      "city": city_State.city,
      "state": city_State.state,
      "venues": venues_data
      })
  return render_template('pages/venues.html', areas=final_data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  """Searches for a search input match in the venues table.

  Args:
    search_term: The search term input from the user. 
  returns:
    results: The result data from querying venues table.  
    search_term: The original user input.
  """
  final_data =[]
  count = 0

  search_term = request.form.get('search_term', '')
  search = "%{}%".format(search_term) # I got the solution for the case-insensitive query from here https://stackoverflow.com/questions/3325467/sqlalchemy-equivalent-to-sql-like-statement 
  search_Query = db.session.query(Venue.id, Venue.name).filter(Venue.name.ilike(search))
  for venue in search_Query:
    count += 1
    venue_Upcoming_Shows_Number = db.session.query(Show).join(Venue).filter(Show.start_time > datetime.now(), Show.venue_id == Venue.id).count()
    final_data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": venue_Upcoming_Shows_Number
      })
    
  response={
    "count": count,
    "data": final_data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  """Fetches all data for a specific venue id in venues table.

  Args:
    venue_id: The venue id of the desired venue to be fetched. 
  returns:
    venue: An object that contains all the data of the desired venue.  
  """
  venue = Venue.query.get(venue_id)
  past_Shows = []
  upcoming_Shows = []
  venue_Upcoming_Shows_Number = db.session.query(Show).join(Venue).filter(Show.start_time > datetime.now(), Show.venue_id == venue.id).count()
  venue_Past_Shows_Number = db.session.query(Show).join(Venue).filter(Show.start_time < datetime.now(), Show.venue_id == venue.id).count()
  Shows_Query = db.session.query(Show).join(Venue).filter(Show.venue_id == venue.id)
  for show in Shows_Query:
    if(show.start_time > datetime.now()):
      upcoming_Shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.isoformat()
      })
    else:
      past_Shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.isoformat()
      })  
  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": list((venue.genres).split(',')),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_Shows,
    "upcoming_shows": upcoming_Shows,
    "past_shows_count": venue_Past_Shows_Number,
    "upcoming_shows_count": venue_Upcoming_Shows_Number,
  }
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  """Creates a new venue in the venues table.

  Args:
    name: The name of the new venue. 
    city: The city of the new venue.
    state: The state of the new venue.
    address: The address of the new venue.
    phone: The phone number of the new venue.
    genres: The genres played in of the new venue.
    facebook_link: The facebook_link of the new venue.
    image_link: The image_link of the new venue.
    website: The website of the new venue.
    seeking_talent: A boolean variable which defines whether the venue is looking for artists or not.
    seeking_description: The description shown in the venue page when it's seeking for talents.
  returns:
    None.
  """
  error = False
  try:
    venue = Venue()
    venue.name = request.form.get('name', '')
    venue.city = request.form.get('city', '')
    venue.state = request.form.get('state', '')
    venue.address = request.form.get('address', '')
    venue.phone = request.form.get('phone', '')
    venue.genres = ','.join(request.form.getlist('genres'))
    venue.facebook_link = request.form.get('facebook_link', '') 
    venue.image_link = request.form.get('image_link', '')
    venue.website = request.form.get('website', '')
    if(request.form.get('seeking_talent', '') == 'True'):
      venue.seeking_talent = True
      venue.seeking_description = request.form.get('seeking_description', '')
    else:
      venue.seeking_talent = False
      venue.seeking_description = ''
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:  
    db.session.close()
    if(error):
      flash('Venue ' + request.form.get('name') + ' could not be listed!')
    else:
      flash('Venue ' + request.form.get('name') + ' was successfully listed!')  
      # on successful db insert, flash success
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  """Deletes a venue data given it's id.

  Args:
    venue_id: The venue id of the desired venue to be deleted. 
  returns:
    None. 
  """
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
  finally:  
    db.session.close()


  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  """Fetches all artists data in the artists table.

  Args:
    None.
  returns:
    areas: All the artists data in database.  
  """
  data = db.session.query(Artist.id, Artist.name)

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  """Searches for a search input match in the artists table.

  Args:
    search_term: The search term input from the user. 
  returns:
    results: The result data from querying artists table.  
    search_term: The original user input.
  """
  final_data =[]
  count = 0

  search_term = request.form.get('search_term', '')
  search = "%{}%".format(search_term) # I got the solution for the case-insensitive query from here https://stackoverflow.com/questions/3325467/sqlalchemy-equivalent-to-sql-like-statement 
  search_Query = db.session.query(Artist.id, Artist.name).filter(Artist.name.ilike(search))
  for artist in search_Query:
      count += 1
      artist_Upcoming_Shows_Number = db.session.query(Show).join(Artist).filter(Show.start_time > datetime.now(), Show.artist_id == Artist.id).count()
      final_data.append({ 
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": artist_Upcoming_Shows_Number
      })
  response={
    "count": count,
    "data": final_data
     }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  """Fetches all data for a specific artist id in artists table.

  Args:
    venue_id: The artist id of the desired artist to be fetched. 
  returns:
    venue: An object that contains all the data of the desired artist.  
  """

  artist = Artist.query.get(artist_id)
  past_Shows = []
  upcoming_Shows = []
  artist_Upcoming_Shows_Number = db.session.query(Show).join(Artist).filter(Show.start_time > datetime.now(), Show.artist_id == artist.id).count()
  artist_Past_Shows_Number = db.session.query(Show).join(Artist).filter(Show.start_time < datetime.now(), Show.artist_id == artist.id).count()
  Shows_Query = db.session.query(Show).join(Artist).filter(Show.artist_id == artist.id)
  for show in Shows_Query:
    if(show.start_time > datetime.now()):
      upcoming_Shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.isoformat()
      })
    else:
      past_Shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.isoformat()
      })

  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": list((artist.genres).split(',')),
    "address": artist.address,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_Shows,
    "upcoming_shows": upcoming_Shows,
    "past_shows_count": artist_Past_Shows_Number,
    "upcoming_shows_count": artist_Upcoming_Shows_Number,
  }
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  artistObj = {
    "id": artist.id,
    "name": artist.name,
    "genres": list((artist.genres).split(',')),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
    }
   # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artistObj)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  """Updates the information of an existing artist in the artists table.

  Args:
    name: The name of the new artist. 
    city: The city of the new artist.
    state: The state of the new artist.
    address: The address of the new artist.
    phone: The phone number of the new artist.
    genres: The genres played in of the new artist.
    facebook_link: The facebook_link of the new artist.
    image_link: The image_link of the new artist.
    website: The website of the new artist.
    seeking_venue: A boolean variable which defines whether the artist is looking for venues or not.
    seeking_description: The description shown in the artist page when he is seeking for venues.
  returns:
    None.
  """

  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form.get('name', '')
    artist.city = request.form.get('city', '')
    artist.state = request.form.get('state', '')
    artist.address = request.form.get('address', '')
    artist.phone = request.form.get('phone', '')
    artist.genres = ','.join(request.form.getlist('genres'))
    artist.facebook_link = request.form.get('facebook_link', '') 
    artist.image_link = request.form.get('image_link', '')
    artist.website = request.form.get('website', '')
    if(request.form.get('seeking_venue', '') == 'True'):
      artist.seeking_venue = True
      artist.seeking_description = request.form.get('seeking_description', '')
    else:
      artist.seeking_venue = False
      artist.seeking_description = ''
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:  
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  venueObj={
    "id": venue.id,
    "name": venue.name,
    "genres": list((venue.genres).split(',')),
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_venue": venue.seeking_venue,
    "seeking_description":venue.seeking_description,
    "image_link": venue.image_link
    }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venueObj)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  """Updates the information of an existing venue in the venues table.

  Args:
    name: The name of the new venue. 
    city: The city of the new venue.
    state: The state of the new venue.
    address: The address of the new venue.
    phone: The phone number of the new venue.
    genres: The genres played in of the new venue.
    facebook_link: The facebook_link of the new venue.
    image_link: The image_link of the new venue.
    website: The website of the new venue.
    seeking_talent: A boolean variable which defines whether the venue is looking for artists or not.
    seeking_description: The description shown in the venue page when it's seeking for talents.
  returns:
    None.
  """
  try:
    venue = Venue.query.get(venue_id)
    venue.name = request.form.get('name', '')
    venue.city = request.form.get('city', '')
    venue.state = request.form.get('state', '')
    venue.address = request.form.get('address', '')
    venue.phone = request.form.get('phone', '')
    venue.genres = ' '.join(request.form.getlist('genres'))
    venue.facebook_link = request.form.get('facebook_link', '') 
    venue.image_link = request.form.get('image_link', '')
    venue.website = request.form.get('website', '')
    if(request.form.get('seeking_talent', '') == 'True'):
      venue.seeking_talent = True
      venue.seeking_description = request.form.get('seeking_description', '')
    else:
      venue.seeking_talent = False
      venue.seeking_description = ''
    db.session.commit()
  except:
    db.session.rollback()
  finally:  
    db.session.close()
    
    return redirect(url_for('show_venue', venue_id=venue_id))
#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  """Creates a new artist in the artists table.

  Args:
    name: The name of the new artist. 
    city: The city of the new artist.
    state: The state of the new artist.
    address: The address of the new artist.
    phone: The phone number of the new artist.
    genres: The genres played in of the new artist.
    facebook_link: The facebook_link of the new artist.
    image_link: The image_link of the new artist.
    website: The website of the new artist.
    seeking_venue: A boolean variable which defines whether the artist is looking for venues or not.
    seeking_description: The description shown in the artist page when he is seeking for venues.
  returns:
    None.
  """
  error = False
  try:
    artist = Artist()
    artist.name = request.form.get('name', '')
    artist.city = request.form.get('city', '')
    artist.state = request.form.get('state', '')
    artist.address = request.form.get('address', '')
    artist.phone = request.form.get('phone', '')
    artist.genres = ','.join(request.form.getlist('genres'))
    artist.facebook_link = request.form.get('facebook_link', '') 
    artist.image_link = request.form.get('image_link', '')
    artist.website = request.form.get('website', '')
    if(request.form.get('seeking_venue', '') == 'True'):
      artist.seeking_venue = True
      artist.seeking_description = request.form.get('seeking_description', '')
    else:
      artist.seeking_venue = False
      artist.seeking_description = ''
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:  
    db.session.close()
    if(error):
      flash('Artist ' + request.form.get('name') + ' could not be listed!')
    else:
      flash('Artist ' + request.form.get('name') + ' was successfully listed!')

  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  """Fetches all shows data in the shows table.

  Args:
    None.
  returns:
    areas: All the shows data in shows table.  
  """
  data = []
  shows_Query = Show.query.order_by('start_time').all()
  for show in shows_Query:
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.isoformat()
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  """Creates a new show in the shows table.

  Args:
    venue_id: The id of the show venue. 
    city: The id of the show artist. 
    state: The time and date of the show.
  returns:
    None.
  """
  error = False
  try:
    show = Show()
    show.venue_id = request.form.get('venue_id', '')
    show.artist_id = request.form.get('artist_id', '')
    show.start_time = request.form.get('start_time', '')
    db.session.add(show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:  
    db.session.close()
    if(error):
      flash('Show could not be listed!')
    else:
      flash(' was successfully listed!')  
  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
