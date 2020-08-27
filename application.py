import os
from flask import Flask, session, request, redirect, render_template
from flask_session import Session
import spotipy
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)


def session_cache_path():
    return caches_folder + session.get('uuid')

# weighted avg to determine top artists popularity score. The artists are weighted roughly according to their ranking by the Spotify user
#higher the rank, the more the popularity score is counted.
def WeightedAvg(artists):
    pop = 0
    n = len(artists)
    d = 0
    for i, artist in enumerate(artists):
        pop += (artist['popularity']*(2*n-i))
        d += (2*n-i)
    return round(pop/d)

#default routing handles login with Spotify
@app.route('/')
def index():
    if not session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())

    auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-top-read',
                                               cache_path=session_cache_path(),
                                               show_dialog=True)

    if request.args.get("code"):
        # Step 3. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.get_cached_token():
        # Step 2. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return render_template('login.html', auth_url=auth_url)
        # return f'<h2><a href="{auth_url}">Sign in</a></h2>'

    # # Step 4. Signed in, display data

    return redirect('/shortterm')
# FIXME: hese 3 routes do the exact same shit. There should be a better way to do it.
@app.route('/shortterm')
def shortTerm():
    if session.get('uuid') is None:
        return redirect('/') 
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    if not auth_manager.get_cached_token():
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    results = spotify.current_user_top_artists(20, 0, "short_term")

    weighted_avg = WeightedAvg(results['items'])

    return render_template('index.html', timeFrame = "4 weeks", weighted_avg=weighted_avg, artists = results['items'])


#routing with long, short and medium term routing. Displays differently in index.html
@app.route('/mediumterm')
def mediumTerm():
    if session.get('uuid') is None:
        return redirect('/') 
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    if not auth_manager.get_cached_token():
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    results = spotify.current_user_top_artists(20, 0, "medium_term")

    weighted_avg = WeightedAvg(results['items'])

    return render_template('index.html', timeFrame = "6 months", weighted_avg=weighted_avg, artists = results['items'])

@app.route('/longterm')
def longTerm():
    if session.get('uuid') is None:
        return redirect('/') 
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    if not auth_manager.get_cached_token():
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    results = spotify.current_user_top_artists(20, 0, "long_term")

    weighted_avg = WeightedAvg(results['items'])

    return render_template('index.html', timeFrame = "all time", weighted_avg=weighted_avg, artists = results['items'])


@app.route('/sign_out')
def sign_out():
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path())
        session.clear()
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
    return redirect('/')



@app.route('/current_user')
def current_user():
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    if not auth_manager.get_cached_token():
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user()


if __name__ == '__main__':
    app.run()
