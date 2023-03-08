#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate=Migrate(app,db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
artist_venue = db.Table('artist_venue',
  db.Column('Artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True),
  db.Column('Venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True))

class Venue(db.Model):
  __tablename__ = 'Venue'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  genres = db.Column(db.ARRAY(db.String), nullable=False)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  address = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  website = db.Column(db.String(500))
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  seeking_talent = db.Column(db.Boolean)
  seeking_description = db.Column(db.String(500))
  venues = db.relationship('Venue', secondary=artist_venue, backref=db.backref('Artist', lazy=True))


class Artist(db.Model):
  __tablename__ = 'Artist'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  website = db.Column(db. String(500))
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  seeking_venue=db.Column(db.Boolean)
  seeking_description = db.Column(db.String(500))
  genres = db.Column(db.ARRAY(db.String), nullable=False)
  artists = db.relationship('Artist', secondary=artist_venue, backref=db.backref('Venue', lazy=True))

class Show(db.Model):
  __tablename__ = 'shows'
  id = db.Column(db.Integer, primary_key=True)
  start_time = db.Column(db.DateTime, nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  artist = db.relationship('Artist', backref=db.backref('shows', cascade='all, delete-orphan'))
  venue = db.relationship('Venue', backref=db.backref('shows', cascade='all, delete-orphan'))
  def __repr__(self):
      return f'<Show {self.id}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

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
  venues = Venue.query.all()
  cities_states = set([(venue.city, venue.state) for venue in venues])
  data = []
  for city, state in cities_states:
      city_data = {'city': city, 'state': state, 'venues': []}
      for venue in venues:
          if venue.city == city and venue.state == state:
              num_upcoming_shows = 0
              for show in venue.shows:
                  if show.start_time > datetime.utcnow():
                      num_upcoming_shows += 1
              city_data['venues'].append({
                  'id': venue.id,
                  'name': venue.name,
                  'num_upcoming_shows': num_upcoming_shows
              })
      data.append(city_data)
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  venues = Venue.query.filter(or_(func.lower(Venue.name).contains(search_term.lower()))).all()
  response = {
        "count": len(venues),
        "data": [] }
  for venue in venues:
        response["data"].append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": len([show for show in venue.shows if show.start_time > datetime.now()])
        })
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)

  data = {
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres,
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": [],
      "upcoming_shows": [],
      "past_shows_count": 0,
      "upcoming_shows_count": 0
  }

  past_shows = Show.query.join(Artist).filter(
      Show.venue_id == venue_id,
      Show.start_time < datetime.now()
  ).all()

  for show in past_shows:
      data["past_shows"].append({
          "artist_id": show.artist_id,
          "artist_name": show.artist.name,
          "artist_image_link": show.artist.image_link,
          "start_time": format_datetime(str(show.start_time))
      })
  data["past_shows_count"] = len(past_shows)

  upcoming_shows = Show.query.join(Artist).filter(
      Show.venue_id == venue_id,
      Show.start_time >= datetime.now()
  ).all()

  for show in upcoming_shows:
      data["upcoming_shows"].append({
          "artist_id": show.artist_id,
          "artist_name": show.artist.name,
          "artist_image_link": show.artist.image_link,
          "start_time": format_datetime(str(show.start_time))
      })
  data["upcoming_shows_count"] = len(upcoming_shows)

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  name = request.form.get('name')
  city = request.form.get('city')
  state = request.form.get('state')
  address = request.form.get('address')
  phone = request.form.get('phone')
  genres = request.form.get('genres')
  facebook_link = request.form.get('facebook_link')
  image_link = request.form.get('image_link')
  website_link = request.form.get('website_link')
  seeking_talent = request.form.get('seeking_talent')
  seeking_description = request.form.get('seeking_description')


  new_venue = Venue(
      name=name,
      city=city,
      state=state,
      address=address,
      phone=phone,
      genres=genres,
      facebook_link=facebook_link,
      image_link=image_link,
      website=website_link,
      seeking_talent=seeking_talent,
      seeking_description=seeking_description
  )

  try:
      db.session.add(new_venue)
      db.session.commit()

      flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
      # On unsuccessful
      db.session.rollback()
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
      db.session.close()

  return render_template('pages/home.html')
 

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try:
      venue = Venue.query.get(venue_id)
      db.session.delete(venue)
      db.session.commit()
  except:
      # if an error occurred
      db.session.rollback()
      error = True
  finally:
      db.session.close()
  if error:
      flash('An error occurred. Venue could not be deleted.')
  else:
      flash('Venue was successfully deleted!')
      
  return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  data = []

  for artist in artists:
      data.append({
          "id": artist.id,
          "name": artist.name,
      })

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  artists = Artist.query.filter(func.lower(Artist.name).contains(search_term.lower())).all()
  response = {
      "count": len(artists),
      "data": []
  }
  for artist in artists:
      response["data"].append({
          "id": artist.id,
          "name": artist.name,
          "num_upcoming_shows": len([show for show in artist.shows if show.start_time > datetime.now()])
      })
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  artist = Artist.query.get(artist_id)
  data = {
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": [{
          "venue_id": show.venue_id,
          "venue_name": show.venue.name,
          "venue_image_link": show.venue.image_link,
          "start_time": str(show.start_time)
      } for show in artist.shows if show.start_time < datetime.now()],
      "upcoming_shows": [{
          "venue_id": show.venue_id,
          "venue_name": show.venue.name,
          "venue_image_link": show.venue.image_link,
          "start_time": str(show.start_time)
      } for show in artist.shows if show.start_time > datetime.now()],
      "past_shows_count": len([show for show in artist.shows if show.start_time < datetime.now()]),
      "upcoming_shows_count": len([show for show in artist.shows if show.start_time > datetime.now()]),
  }
  return render_template('pages/show_artist.html', artist=data)
   
#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  form.name.data = artist.name
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.genres.data = artist.genres
  form.facebook_link.data = artist.facebook_link
  form.image_link.data = artist.image_link
  form.website_link.data = artist.website
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  try:
      artist = Artist.query.get(artist_id)
      artist.name = request.form['name']
      artist.city = request.form['city']
      artist.state = request.form['state']
      artist.phone = request.form['phone']
      artist.genres = request.form.getlist('genres')
      artist.facebook_link = request.form['facebook_link']
      artist.image_link = request.form['image_link']
      artist.website = request.form['website_link']
      artist.seeking_venue = True if 'seeking_venue' in request.form else False
      artist.seeking_description = request.form['seeking_description']

      db.session.commit()
  except Exception as e:
      error = True
      db.session.rollback()
      print(e)
  finally:
      db.session.close()

  if not error:
      flash('Artist ' + request.form['name'] + ' was successfully updated!')
  else:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')

  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  form.name.data = venue.name
  form.genres.data = venue.genres
  form.address.data = venue.address
  form.city.data = venue.city
  form.state.data = venue.state
  form.phone.data = venue.phone
  form.website_link.data = venue.website
  form.facebook_link.data = venue.facebook_link
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  form.image_link.data = venue.image_link

  return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  venue = Venue.query.get(venue_id)

  venue.name = request.form['name']
  venue.genres = request.form.getlist('genres')
  venue.address = request.form['address']
  venue.city = request.form['city']
  venue.state = request.form['state']
  venue.phone = request.form['phone']
  venue.website = request.form['website_link']
  venue.facebook_link = request.form['facebook_link']
  venue.seeking_talent = True if 'seeking_talent' in request.form else False
  venue.seeking_description = request.form['seeking_description']
  venue.image_link = request.form['image_link']

  db.session.commit()
  flash('Venue ' + request.form['name'] + ' was successfully edited!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # Get form data and create new artist record
  name = request.form.get('name')
  city = request.form.get('city')
  state = request.form.get('state')
  phone = request.form.get('phone')
  genres = request.form.get('genres')
  website_link = request.form.get('website_link')
  image_link = request.form.get('image_link')
  facebook_link = request.form.get('facebook_link')
  seeking_venue = request.form.get('seeking_venue')
  seeking_description = request.form.get('seeking_description')
  
  artist = Artist(name=name, city=city, state=state, phone=phone, website=website_link,
                  image_link=image_link, facebook_link=facebook_link, seeking_venue=seeking_venue,
                  seeking_description=seeking_description,genres=genres)

  # Add new artist record to database
  try:
      db.session.add(artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
      db.session.rollback()
      flash('An error occurred. Artist ' + name + ' could not be listed.')
  finally:
      db.session.close()
  
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  s=Show.query.all()
  print(s)
  data = []
  for show in s:
      venue = Venue.query.get(show.venue_id)
      artist = Artist.query.get(show.artist_id)
      data.append({
          "venue_id": venue.id,
          "venue_name": venue.name,
          "artist_id": artist.id,
          "artist_name": artist.name,
          "artist_image_link": artist.image_link,
          "start_time": str(show.start_time)
      })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form)
  if form.validate():
      artist_id = form.artist_id.data
      venue_id = form.venue_id.data
      start_time = form.start_time.data
      new_show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
      try:
          db.session.add(new_show)
          db.session.commit()
          flash('Show was successfully listed!')
          return render_template('pages/home.html')
      except:
          flash('An error occurred. Show could not be listed.')
          db.session.rollback()
          return render_template('pages/home.html')
  else:
      flash(form.errors)
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
