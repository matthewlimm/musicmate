from flask import Flask, request, url_for, session, redirect, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import pickle
import pandas as pd
import numpy as np
from pprint import pprint

app = Flask(__name__)

model = pickle.load(open('models/model.pkl','rb'))

app.secret_key = "asdfd2FD2hjklfds"
app.config['SESSION_COOKIE_NAME'] = 'Matthews Cookie'
TOKEN_INFO = 'token_info'

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/login')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    print(auth_url)
    return redirect(auth_url)

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
    # at this part, we ensured the token info is up-to-date / fresh
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user = sp.user(sp.me()['id'])

    def analyze_playlist(playlist):
        # Create empty dataframe
        playlist_features_list = ["danceability","energy","valence",]
        playlist_df = pd.DataFrame(columns=playlist_features_list)
        
        # Loop through every track in the playlist, extract features and append the features to the playlist df
        for track in saved_tracks:
            # Create empty dict
            playlist_features = {}
            # Get metadata
            playlist_features["track_id"] = track["track"]["id"]
            
            # Get audio features
            audio_features = sp.audio_features(playlist_features["track_id"])[0]
            for feature in playlist_features_list:
                playlist_features[feature] = audio_features[feature]
            
            # Concat the dfs
            track_df = pd.DataFrame(playlist_features, index = [0])
            playlist_df = pd.concat([playlist_df, track_df], ignore_index = True)
    
        return playlist_df
    
    def get_top_artist_picture():
        return sp.current_user_top_artists()['items'][0]['images'][0]['url']
    
    def get_top_track_picture():
        return sp.current_user_top_tracks()['items'][0]['album']['images'][0]['url']
    
    # Calculate average percentages of the happy, energy, and danceability
    def calc_happy(playlist_df):
        return playlist_df['valence'].mean()
    def calc_energy(playlist_df):
        return playlist_df['energy'].mean()
    def calc_danceable(playlist_df):
        return playlist_df['danceability'].mean()
    
    saved_tracks = sp.current_user_saved_tracks(50)['items']
    playlist_df = analyze_playlist(saved_tracks)

    happy_percent = round(calc_happy(playlist_df)*100)
    energy_percent = round(calc_energy(playlist_df)*100)
    danceable_percent = round(calc_danceable(playlist_df)*100)
    
    top_artist_picture = get_top_artist_picture()
    top_track_picture = get_top_track_picture()

    return render_template('dashboard.html',user=user,happy_percent=happy_percent,energy_percent=energy_percent,danceable_percent=danceable_percent,top_artist_picture=top_artist_picture,top_track_picture=top_track_picture)

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
            artist_features['artist'] = artist['name'] 
            artist_features['artist_genre'] = artist['genres'][0]
            artist_features['artist_image_url'] = artist['images'][0]['url']
            artist_features['artist_url'] = artist['external_urls']['spotify']
            
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
    # at this part, we ensured the token info is up-to-date / fresh
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user = sp.user(sp.me()['id'])

    toptracks = sp.current_user_top_tracks()['items']
    pprint(toptracks)
    def analyze_artists(toptracks):
        # Create empty dataframe
        tracks_features_list = ["artist","album","track_name", "track_image_url", "track_url"]
        tracks_df = pd.DataFrame(columns=tracks_features_list)

        for track in toptracks:
            # Create empty dict
            track_features = {}

            # Get metadata
            track_features["artist"] = track["artists"][0]["name"]
            track_features["album"] = track["album"]["name"]
            track_features["track_name"] = track["name"]
            track_features["track_image_url"] = sp.track(track["id"])['album']['images'][0]['url']
            track_features["track_url"] = track["external_urls"]["spotify"][0]
            
            # Concat the dfs
            track_features_df = pd.DataFrame(track_features, index = [0])
            tracks_df = pd.concat([tracks_df, track_features_df], ignore_index = True)
            
        return tracks_df
    
    tracks = analyze_artists(toptracks)

    return render_template('toptracks.html',columns=[tracks.columns.values], rows=[list(tracks.values.tolist())],user=user)

@app.route('/happyvsad')
def happyvsad():
    try:
        token_info = get_token()
    except:
        print('User Not Logged In!')
        return redirect('/')
    # at this part, we ensured the token info is up-to-date / fresh
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user = sp.user(sp.me()['id'])

    playlists = []
    iter = 0
    while True:
        items = sp.current_user_playlists(limit=50,offset=iter * 50)['items']
        iter += 1
        playlists += items
        if(len(items) < 50):
            break
    pprint(playlists)
    return render_template('happyvsad.html',user=user,playlists=playlists) # data is list

@app.route('/happyvsadpred',methods=['POST'])
def predict():
    try:
            token_info = get_token()
    except:
        print('User Not Logged In!')
        return redirect('/')
    # at this part, we ensured the token info is up-to-date / fresh
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    user = sp.current_user
    selected_playlist_id = [str(x) for x in request.form.values()][0]
    print('\nSelected Playlist ID: ' + selected_playlist_id)

    def analyze_playlist(user, playlist_id):
        # Create empty dataframe
        playlist_features_list = ["artist","album","track_name", "track_id","track_image_url","danceability","energy","key","loudness","mode", "speechiness","instrumentalness","liveness","valence","tempo", "duration_ms","time_signature"]
        playlist_df = pd.DataFrame(columns=playlist_features_list)
        
        # Loop through every track in the playlist, extract features and append the features to the playlist df
        playlist = sp.user_playlist_tracks(user, selected_playlist_id)["items"]
        for track in playlist:
            # Create empty dict
            playlist_features = {}
            # Get metadata
            playlist_features["artist"] = track["track"]["album"]["artists"][0]["name"]
            playlist_features["album"] = track["track"]["album"]["name"]
            playlist_features["track_name"] = track["track"]["name"]
            playlist_features["track_id"] = track["track"]["id"]
            playlist_features["track_image_url"] = sp.track(track["track"]["id"])['album']['images'][0]['url']
            
            # Get audio features
            audio_features = sp.audio_features(playlist_features["track_id"])[0]
            for feature in playlist_features_list[5:]:
                playlist_features[feature] = audio_features[feature]
            
            # Concat the dfs
            track_df = pd.DataFrame(playlist_features, index = [0])
            playlist_df = pd.concat([playlist_df, track_df], ignore_index = True)
            
        return playlist_df
    
    def classify_playlist(user, playlist_id):
        playlist_pred_df = analyze_playlist(user, playlist_id)
        playlist_predictions = model.predict(playlist_pred_df.drop(['artist','album','track_name','track_id','track_image_url'],axis=1))
        playlist_pred_df['prediction'] = playlist_predictions
        playlist_pred_df['prediction'] = playlist_pred_df['prediction'].replace(1, 'Happy')
        playlist_pred_df['prediction'] = playlist_pred_df['prediction'].replace(2, 'Sad')
        return playlist_pred_df
    
    predictions = classify_playlist(user, selected_playlist_id)
    print(predictions)
    happy_predictions = predictions[predictions['prediction'] == 'Happy']
    sad_predictions = predictions[predictions['prediction'] == 'Sad']

    user = sp.user(sp.me()['id'])
    return render_template('happyvsadpred.html',columns=[happy_predictions.columns.values,sad_predictions.columns.values], rows=[list(happy_predictions.values.tolist()),list(sad_predictions.values.tolist())],user=user,selected_playlist_id=selected_playlist_id)
    
@app.route("/saveplaylist", methods=['GET', 'POST'])
def savePlaylist():
    try:
        token_info = get_token()
    except:
        print('User Not Logged In!')
        return redirect('/')
    # at this part, we ensured the token info is up-to-date / fresh
    sp = spotipy.Spotify(auth=token_info['access_token'])
    prediction_table = request.form['save_button']
    prediction_table = np.array(eval(prediction_table))
    prediction_table = pd.DataFrame(data=prediction_table,columns=['artist','album','track_name','track_id','track_image_url','danceability','energy','key','loudness','mode','speechiness','instrumentalness','liveness','valence','tempo','duration_ms','time_signature','prediction'])

    if prediction_table['prediction'][0] == 'Happy':
        prediction = 'Happy'
        print('Selected Happy Playlist for Import')
    else:
        prediction = 'Sad'
        print('Selected Sad Playlist for Import')
    track_ids = prediction_table.drop(['artist','album','track_name','track_image_url','danceability','energy','key','loudness','mode','speechiness','instrumentalness','liveness','valence','tempo','duration_ms','time_signature','prediction'],axis=1)
    track_ids = track_ids.values.tolist()
    track_ids = list(np.concatenate(track_ids).flat)
    
    user_id = sp.me()['id']
    if prediction == 'Happy':
        playlist_name = "My Happy Playlist"
    else:
        playlist_name = "My Sad Playlist"

    def getPlaylistID(user_id, playlist_name):
        playlist_id = ''
        playlists = sp.user_playlists(user_id)
        for playlist in playlists['items']:  # iterate through playlists I follow
            if playlist['name'] == playlist_name:  # filter for newly created playlist
                playlist_id = playlist['id']
        print(playlist_id)
        return playlist_id
    
    check_existing_playlist_id = getPlaylistID(user_id, playlist_name)
    if check_existing_playlist_id != '':
        return "Playlist already exists"
    
    # create empty playlist with name and description
    sp.user_playlist_create(user=user_id,name=playlist_name,public=False,description="Generated by Matthew Lim.")
    # get playlist id of empty playlist
    playlist_id = getPlaylistID(user_id, playlist_name)
    
    # pass tracks of previous track ids
    print('Track IDs to Pass Through Spotify API')
    pprint(track_ids)
    sp.user_playlist_add_tracks(user_id, playlist_id, track_ids)

    playlists = []
    iter = 0
    while True:
        items = sp.current_user_playlists(limit=50,offset=iter * 50)['items']
        iter += 1
        playlists += items
        if(len(items) < 50):
            break

    user = sp.user(sp.me()['id'])
    return render_template('saveplaylist.html',user=user,prediction=prediction,playlists=playlists)

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
        client_id='9ad5134785d349878a600cac03f8a9e2',
        client_secret='2d21a0cee3a142daaae4c64f5d6de9d2',
        redirect_uri=url_for('redirectPage',_external=True),
        scope='user-library-read playlist-modify-public playlist-read-private playlist-modify-private user-top-read')