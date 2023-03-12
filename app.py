from flask import Flask, request, url_for, session, redirect, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import pickle
import numpy as np

app = Flask(__name__)

model = pickle.load(open('models/model.pkl','rb'))

app.secret_key = "2yf8d9asDF"
app.config['SESSION_COOKIE_NAME'] = 'Matthews Cookie'
TOKEN_INFO = 'token_info'

@app.route('/')
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
    return redirect(url_for('index'))

@app.route('/index')
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
    return 0

@app.route('/predict',methods=['POST'])
def predict():
    int_features = [int(x) for x in request.form.values()]
    features = [np.array(int_features)]  
    prediction = model.predict(features) 
    result = prediction[0]

    return render_template('index.html', prediction=result)
    

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
        scope='user-library-read')