from flask import Flask, request, url_for, session, redirect, render_template
import spotipy
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv, dotenv_values
import time
import pickle
import pandas as pd
import numpy as np
from pprint import pprint
import concurrent.futures
import json
import time
from flask import Flask, request, redirect, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)

model = pickle.load(open('models/model.pkl','rb'))

app.secret_key = "asdfd2FD2hjklfds"
app.config['SESSION_COOKIE_NAME'] = 'Matthews Cookie'
TOKEN_INFO = 'token_info'

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

print(client_id, client_secret)

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/login')
def login():
    cache_file = '.cache'
    if os.path.exists(cache_file):
        os.remove(cache_file)
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    print(auth_url)
    return redirect(auth_url)

@app.route('/logout')
def logout():
    # Clear the session data to log the user out
    session.clear()
    return redirect(url_for('index'))  # Redirect to the homepage or login page

@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('dashboard'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/getTracks')
def getTracks():
    try:
        token_info = get_token()
    except:
        print('User Not Logged In!')
        return redirect('/')
    # at this part, we ensured the token info is up-to-date / fresh
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    all_songs = []
    iter = 0
    while True:
        items = sp.current_user_saved_tracks(limit=50,offset=iter * 50)['items']
        iter += 1
        all_songs += items
        if(len(items) < 50):
            break
    return str(len(all_songs))

@app.route('/dashboard')
def dashboard():
    try:
        token_info = get_token()
    except:
        print('User Not Logged In!')
        return redirect('/')

    # Define 'user' consistently
    user = session.get("user")  # Retrieve cached user info if available

    # Check if user data and other metrics are cached
    user_data_cache = session.get("user_data_cache")

    if not user_data_cache or not user:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        
        # Fetch user profile data and cache it
        user = sp.user(sp.me()['id'])
        session["user"] = user  # Cache user info

        # Fetch and cache additional dashboard data as needed
        top_artists = sp.current_user_top_artists(limit=1)['items']
        top_tracks = sp.current_user_top_tracks(limit=1)['items']
        saved_tracks = sp.current_user_saved_tracks(limit=50)['items']

        # Prepare data for display
        top_artist_picture = (
            top_artists[0]['images'][0]['url'] if top_artists and top_artists[0].get('images') else "default_artist_image.jpg"
        )
        top_track_picture = (
            top_tracks[0]['album']['images'][0]['url'] if top_tracks and top_tracks[0]['album'].get('images') else "default_track_image.jpg"
        )

        # Calculate track metrics (e.g., happiness, energy, danceability)
        track_ids = [track["track"]["id"] for track in saved_tracks]
        if track_ids:
            audio_features = sp.audio_features(track_ids)
            playlist_df = pd.DataFrame(audio_features)[["danceability", "energy", "valence"]].dropna()
            happy_percent = round(playlist_df['valence'].mean() * 100)
            energy_percent = round(playlist_df['energy'].mean() * 100)
            danceable_percent = round(playlist_df['danceability'].mean() * 100)
        else:
            happy_percent = energy_percent = danceable_percent = 0

        # Cache data for session reuse
        user_data_cache = {
            "happy_percent": happy_percent,
            "energy_percent": energy_percent,
            "danceable_percent": danceable_percent,
            "top_artist_picture": top_artist_picture,
            "top_track_picture": top_track_picture
        }
        session["user_data_cache"] = user_data_cache
    else:
        # Retrieve cached values if present
        happy_percent = user_data_cache["happy_percent"]
        energy_percent = user_data_cache["energy_percent"]
        danceable_percent = user_data_cache["danceable_percent"]
        top_artist_picture = user_data_cache["top_artist_picture"]
        top_track_picture = user_data_cache["top_track_picture"]

    # Pass data to template
    return render_template(
        'dashboard.html',
        user=user,
        happy_percent=happy_percent,
        energy_percent=energy_percent,
        danceable_percent=danceable_percent,
        top_artist_picture=top_artist_picture,
        top_track_picture=top_track_picture
    )

@app.route('/about')
def about():
    try:
        token_info = get_token()
    except:
        print('User Not Logged In!')
        return redirect('/')
    # at this part, we ensured the token info is up-to-date / fresh
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user = sp.user(sp.me()['id'])

    return render_template('about.html',user=user)

@app.route('/topartists')
def topartists():
    try:
        token_info = get_token()
    except:
        print('User Not Logged In!')
        return redirect('/')

    # Check if the top artists data is already cached in the session
    top_artists_cache = session.get("top_artists_cache")

    if not top_artists_cache:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        user = sp.user(sp.me()['id'])

        # Fetch top artists from Spotify API
        try:
            top_artists = sp.current_user_top_artists(limit=20)['items']
        except SpotifyException as e:
            print("Spotify API error:", e)
            return redirect('/')

        # Structure artist data for template rendering
        artist_data = [
            {
                "artist": artist["name"],
                "artist_genre": artist["genres"][0] if artist.get("genres") else "unknown genre",
                "artist_image_url": artist["images"][0]["url"] if artist.get("images") else "default_artist_image.jpg",
                "artist_url": artist["external_urls"]["spotify"]
            }
            for artist in top_artists
        ]

        # Cache the structured data in the session
        session["top_artists_cache"] = artist_data
    else:
        # Use cached data if available
        artist_data = top_artists_cache

    # Pass the artist data directly to the template
    return render_template(
        'topartists.html',
        columns=["artist", "artist_genre", "artist_image_url", "artist_url"],
        rows=artist_data,
        user=session.get('user')
    )

def topartists():
    try:
        token_info = get_token()
    except:
        print('User Not Logged In!')
        return redirect('/')
    # at this part, we ensured the token info is up-to-date / fresh
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user = sp.user(sp.me()['id'])

    topartists = sp.current_user_top_artists()['items']
    pprint(topartists)
    def analyze_artists(topartists):
        # Create empty dataframe
        artists_features_list = ['artist','artist_genre','artist_image_url','artist_url']
        artists_df = pd.DataFrame(columns=artists_features_list)

        for artist in topartists:
            # Create empty dict
            artist_features = {}

            # Get metadata
            artist_features['artist'] = artist['name'] if 'name' in artist else 'unknown artist'
            artist_features['artist_genre'] = artist['genres'][0] if artist.get('genres') else 'unknown genre'
            artist_features['artist_image_url'] = artist['images'][0]['url'] if artist.get('images') else None
            artist_features['artist_url'] = artist['external_urls']['spotify'] if 'external_urls' in artist and 'spotify' in artist['external_urls'] else None
            
            # Concat the dfs
            artists_features_df = pd.DataFrame(artist_features, index = [0])
            artists_df = pd.concat([artists_df, artists_features_df], ignore_index = True)
            
        return artists_df
    
    artists = analyze_artists(topartists)

    return render_template('topartists.html',columns=[artists.columns.values], rows=[list(artists.values.tolist())],user=user)

@app.route('/toptracks')
def toptracks():
    try:
        token_info = get_token()
    except:
        print('User Not Logged In!')
        return redirect('/')

    # Check if top tracks data is already cached
    top_tracks_cache = session.get("top_tracks_cache")
    
    # If not cached, fetch the data from Spotify API
    if not top_tracks_cache:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        user = sp.user(sp.me()['id'])
        
        # Fetch top tracks from Spotify API
        try:
            top_tracks = sp.current_user_top_tracks(limit=20)['items']
        except SpotifyException as e:
            print("Spotify API error:", e)
            return redirect('/')

        # Extract relevant data for each track
        track_data = []
        for track in top_tracks:
            track_info = {
                "artist": track["artists"][0]["name"] if track["artists"] else "Unknown Artist",
                "album": track["album"]["name"] if track.get("album") and "name" in track["album"] else "Unknown Album",
                "track_name": track["name"] if "name" in track else "Unknown Track",
                "track_image_url": track["album"]["images"][0]["url"] if track["album"].get("images") else "default_track_image.jpg",
                "track_url": track["external_urls"]["spotify"] if track.get("external_urls") else None
            }
            track_data.append(track_info)
        
        # Cache the processed data in session
        session["top_tracks_cache"] = track_data
    else:
        # Use cached data if available
        track_data = top_tracks_cache

    # Render template with track data
    return render_template(
        'toptracks.html',
        columns=["artist", "album", "track_name", "track_image_url", "track_url"],
        rows=track_data,
        user=session.get('user')
    )

@app.route('/happyvsad')
def happyvsad():
    try:
        token_info = get_token()
    except:
        print('User Not Logged In!')
        return redirect('/')

    # Check for cached playlists in session
    playlists_cache = session.get("playlists_cache")
    
    if not playlists_cache:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        user = sp.user(sp.me()['id'])
        
        # Fetch user playlists with pagination for large collections
        playlists = []
        offset = 0
        while True:
            response = sp.current_user_playlists(limit=50, offset=offset)
            playlists.extend(response['items'])
            if len(response['items']) < 50:
                break
            offset += 50
        
        # Extract relevant playlist data for template
        playlists_data = [
            {
                "id": playlist['id'],
                "name": playlist['name'],
                "description": playlist['description'] or "no description available",
                "image_url": playlist['images'][0]['url'] if playlist['images'] else "default-playlist-image.jpg"
            }
            for playlist in playlists
        ]
        
        # Cache the data in session
        session["playlists_cache"] = playlists_data
    else:
        playlists_data = playlists_cache

    return render_template('happyvsad.html', user=session.get('user'), playlists=playlists_data)


@app.route('/happyvsadpred', methods=['POST'])
def predict():
    try:
        token_info = get_token()
    except:
        print('User Not Logged In!')
        return redirect('/')

    sp = spotipy.Spotify(auth=token_info['access_token'])
    selected_playlist_id = request.form.get('playlist')

    # Retrieve cached user info for use in the template
    user = session.get('user')

    # Fetch playlist details (title and image)
    playlist = sp.playlist(selected_playlist_id)
    playlist_name = playlist['name']

    # Fetch playlist tracks in one request
    playlist_tracks = sp.playlist_tracks(selected_playlist_id)["items"]
    track_ids = [track["track"]["id"] for track in playlist_tracks if track["track"]]

    # Fetch audio features in batch
    audio_features = sp.audio_features(track_ids)
    playlist_df = pd.DataFrame(audio_features).dropna()

    # Predict track moods in batch
    feature_columns = ["danceability", "energy", "key", "loudness", "mode", "speechiness", "instrumentalness", "liveness", "valence", "tempo", "duration_ms", "time_signature"]
    predictions = model.predict(playlist_df[feature_columns])
    playlist_df["prediction"] = predictions

    # Split tracks by prediction (1=Happy, 2=Sad) and prepare data for template
    happy_tracks = playlist_df[playlist_df["prediction"] == 1]
    sad_tracks = playlist_df[playlist_df["prediction"] == 2]

    # Compile data for rendering
    def format_track_data(tracks, original_tracks):
        return [
            {
                "artist": next(track["track"]["artists"][0]["name"] for track in original_tracks if track["track"]["id"] == row["id"]),
                "album": next(track["track"]["album"]["name"] for track in original_tracks if track["track"]["id"] == row["id"]),
                "track_name": next(track["track"]["name"] for track in original_tracks if track["track"]["id"] == row["id"]),
                "track_image_url": next(track["track"]["album"]["images"][0]["url"] for track in original_tracks if track["track"]["id"] == row["id"])
            }
            for _, row in tracks.iterrows()
        ]

    happy_data = format_track_data(happy_tracks, playlist_tracks)
    sad_data = format_track_data(sad_tracks, playlist_tracks)

    return render_template(
        'happyvsadpred.html',
        user=user,
        rows=[happy_data, sad_data],
        playlist_name=playlist_name  # Pass the playlist name to the template
    )

@app.route("/saveplaylist", methods=['POST'])
def savePlaylist():
    try:
        token_info = get_token()  # Assuming `get_token` retrieves Spotify OAuth token
    except:
        print('User Not Logged In!')
        return redirect('/')

    sp = spotipy.Spotify(auth=token_info['access_token'])

    # Retrieve the 'save_button' data
    save_button_value = request.form.get('save_button', '')
    print(f"Received save_button data: {save_button_value}")  # Debugging

    try:
        # Parse the JSON data
        prediction_table = json.loads(save_button_value)
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return "Invalid JSON data received.", 400

    # Access the nested 'data' key in the parsed JSON
    track_data = prediction_table.get('data', [])
    playlist_type = prediction_table.get('type', 'Unknown')  # Get the playlist type (Happy, Sad, etc.)
    base_playlist_name = prediction_table.get('playlist_name', 'Playlist')  # Get the playlist name from the input or use 'vibes' as default

    if not track_data:
        return "No track data found in the request.", 400

    # Ensure the necessary fields are present in each track
    required_fields = ['artist', 'album', 'track_name', 'track_image_url']
    for track in track_data:
        missing_fields = [field for field in required_fields if field not in track]
        if missing_fields:
            print(f"Missing fields in track: {missing_fields}")
            return f"Missing data fields: {', '.join(missing_fields)}", 400
    
    # Parallelize the track searching using ThreadPoolExecutor
    def search_for_track(track):
        query = f"track:{track['track_name']} artist:{track['artist']}"
        results = sp.search(query, type='track', limit=1)
        if results['tracks']['items']:
            return results['tracks']['items'][0]['id']
        else:
            print(f"Track not found on Spotify: {track['track_name']} by {track['artist']}")
            return None

    track_ids = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        track_ids = list(executor.map(search_for_track, track_data))

    if not any(track_ids):  # Ensure at least one track was found
        return "No tracks found on Spotify.", 400

    user_id = sp.me()['id']
    
    # Modify the playlist name based on the selected type
    playlist_name = f"{base_playlist_name} ({playlist_type.lower()})"  # e.g., "vibes (sad)" or "vibes (happy)"

    # Check if the playlist already exists
    def getPlaylistID(user_id, playlist_name):
        playlist_id = ''
        playlists = sp.current_user_playlists(limit=50)
        while playlists:
            for playlist in playlists['items']:
                if playlist['name'] == playlist_name:
                    return playlist['id']
            if playlists['next']:
                playlists = sp.next(playlists)
            else:
                break
        return playlist_id
    
    # Check if a playlist with the given name already exists
    check_existing_playlist_id = getPlaylistID(user_id, playlist_name)
    if check_existing_playlist_id:
        return "Playlist already exists", 400
    
    # Create a new playlist if it doesn't exist
    new_playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=False, description="Generated by Music Mate.")
    playlist_id = new_playlist['id']
    
    # Filter out None values (tracks that weren't found)
    track_ids = [track_id for track_id in track_ids if track_id is not None]
    
    # Add tracks to the newly created playlist in batches
    BATCH_SIZE = 100  # Maximum number of tracks per request
    for i in range(0, len(track_ids), BATCH_SIZE):
        sp.user_playlist_add_tracks(user_id, playlist_id, track_ids[i:i + BATCH_SIZE])
    
    # Optionally, fetch updated playlists
    playlists = []
    iter = 0
    while True:
        items = sp.current_user_playlists(limit=50, offset=iter * 50)['items']
        iter += 1
        playlists += items
        if len(items) < 50:
            break
    
    user = sp.user(sp.me()['id'])
    return render_template('saveplaylist.html', user=user, playlists=playlists, new_playlist_id=playlist_id, prediction=playlist_type)


def get_token():
    token_info = session.get(TOKEN_INFO, None) # if token value DNE, return none
    if not token_info:
        raise 'exception'
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=url_for('redirectPage',_external=True),
        scope='user-library-read playlist-modify-public playlist-read-private playlist-modify-private user-top-read',
        #cache_path=None,  # Disable caching
        #show_dialog=True  # Force re-authentication dialog
        )