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

app.secret_key = "2yf8d9asDF"
app.config['SESSION_COOKIE_NAME'] = 'Matthews Cookie'
TOKEN_INFO = 'token_info'

if __name__ == "__main__":
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
    creator = sp.user(sp.me()['id'])
    return render_template('dashboard.html',data=creator)

@app.route('/happyvsad')
def happyvsad():
    try:
        token_info = get_token()
    except:
        print('User Not Logged In!')
        return redirect('/')
    # at this part, we ensured the token info is up-to-date / fresh
    sp = spotipy.Spotify(auth=token_info['access_token'])

    playlists = []
    iter = 0
    while True:
        items = sp.current_user_playlists(limit=50,offset=iter * 50)['items']
        iter += 1
        playlists += items
        if(len(items) < 50):
            break
    pprint(playlists)
    return render_template('happyvsad.html',data=playlists) # data is list

@app.route('/predict',methods=['POST'])
def predict():
    try:
            token_info = get_token()
    except:
        print('User Not Logged In!')
        return redirect('/')
    # at this part, we ensured the token info is up-to-date / fresh
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    creator = sp.current_user
    playlist_id = [str(x) for x in request.form.values()][0]
    print('\nSelected Playlist ID: ' + playlist_id)

    def analyze_playlist(creator, playlist_id):
        # Create empty dataframe
        playlist_features_list = ["artist","album","track_name",  "track_id","danceability","energy","key","loudness","mode", "speechiness","instrumentalness","liveness","valence","tempo", "duration_ms","time_signature"]
        
        playlist_df = pd.DataFrame(columns=playlist_features_list)
        
        # Loop through every track in the playlist, extract features and append the features to the playlist df
        playlist = sp.user_playlist_tracks(creator, playlist_id)["items"]
        for track in playlist:
            # Create empty dict
            playlist_features = {}
            # Get metadata
            playlist_features["artist"] = track["track"]["album"]["artists"][0]["name"]
            playlist_features["album"] = track["track"]["album"]["name"]
            playlist_features["track_name"] = track["track"]["name"]
            playlist_features["track_id"] = track["track"]["id"]
            
            # Get audio features
            audio_features = sp.audio_features(playlist_features["track_id"])[0]
            for feature in playlist_features_list[4:]:
                playlist_features[feature] = audio_features[feature]
            
            # Concat the dfs
            track_df = pd.DataFrame(playlist_features, index = [0])
            playlist_df = pd.concat([playlist_df, track_df], ignore_index = True)
            
        return playlist_df
    
    def classify_playlist(creator, playlist_id):
        playlist = analyze_playlist(creator, playlist_id)
        playlist_predictions = model.predict(playlist.drop(['artist','album','track_name','track_id'],axis=1))
        playlist['prediction'] = playlist_predictions
        playlist['prediction'] = playlist['prediction'].replace(1, 'Happy')
        playlist['prediction'] = playlist['prediction'].replace(2, 'Sad')
        return playlist
    
    predictions = classify_playlist(creator, playlist_id)
    happy_predictions = predictions[predictions['prediction'] == 'Happy']
    sad_predictions = predictions[predictions['prediction'] == 'Sad']

    #track_ids = [predictions['track_id'] for predictions in predictions]
    #session['track_ids'] = track_ids
    return render_template('predict.html',tables=[happy_predictions.to_html(index=False,classes='data'),sad_predictions.to_html(index=False,classes='data')], titles=[happy_predictions.columns.values,sad_predictions.columns.values],data=predictions)
    
@app.route("/savePlaylist", methods=['GET', 'POST'])
def savePlaylist():
    try:
        token_info = get_token()
    except:
        print('User Not Logged In!')
        return redirect('/')
    # at this part, we ensured the token info is up-to-date / fresh
    sp = spotipy.Spotify(auth=token_info['access_token'])

    track_id = [str(x) for x in request.form.values()][0]
    track_id = pd.read_html(track_id)[0]
    if track_id['prediction'][0] == 'Happy':
        prediction = 'Happy'
    else:
        prediction = 'Sad'
    track_id.drop(['artist','album','track_name','danceability','energy','key','loudness','mode','speechiness','instrumentalness','liveness','valence','tempo','duration_ms','time_signature','prediction'],axis=1,inplace=True)
    track_id = track_id.values.tolist()
    track_id = list(np.concatenate(track_id).flat)
    
    creator = sp.me()['id']
    if prediction == 'Happy':
        playlist_name = "My Purified (Happy) Playlist"
    else:
        playlist_name = "My Purified (Sad) Playlist"

    sp.user_playlist_create(user=creator,name=playlist_name,public=False,description="Generated by Matthew Lim.")

    def getPlaylistID(creator, playlist_name):
        playlist_id = ''
        playlists = sp.user_playlists(creator)
        for playlist in playlists['items']:  # iterate through playlists I follow
            if playlist['name'] == playlist_name:  # filter for newly created playlist
                playlist_id = playlist['id']
        print(playlist_id)
        return playlist_id
    
    print('Track IDs to Pass Through Spotify API')
    pprint(track_id)

    playlist_id = getPlaylistID(creator, playlist_name)
    sp.user_playlist_add_tracks(creator, playlist_id, track_id)
    return 'Success'

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
        client_secret='581556bb23af4027a7ad75cdab471fdd',
        redirect_uri=url_for('redirectPage',_external=True),
        scope='user-library-read playlist-modify-public playlist-read-private playlist-modify-private')