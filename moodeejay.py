import requests
import urllib
import re
from flask import Flask, render_template, jsonify, request, redirect, session, url_for
from flask.ext.session import Session
import spotipy
import json
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from instagram.client import InstagramAPI
import image
import sentiment
import photo_processing
import os

SESSION_TYPE="filesystem"
app = Flask(__name__)
app.config.from_object(__name__)
Session(app)

instagram_config = {
        'client_id': os.environ["IG_CLIENT_ID"],
        'client_secret': os.environ["IG_CLIENT_SECRET"],
        'redirect_uri': 'https://moodeejay.herokuapp.com/oauth_callback'
    }

api = InstagramAPI(**instagram_config)

#recent_media, next_ = api.user_recent_media(user_id="userid", count=10)

@app.route("/")
def index():
    try:
        url = api.get_authorize_url(scope=["likes","comments"])
        return render_template('index.html', instagram_url=url)

    except Exception as e:
        print(e)
    return "Error"

@app.route("/oauth_callback")
def on_callback():
    code = request.args.get("code")
    if not code:
        return 'ERROR: Missing code'
    try:
        access_token, user_info = api.exchange_code_for_access_token(code)
        if not access_token:
            return "ERROR: Could not get access token"
        session["access_token"] = access_token
        print "getting photos"
        return get_user_photos()
    except Exception as e:
        return "Error: " + str(e)

def get_user_photos():
  access_token = session.get("access_token", None)
  try:
      api = InstagramAPI(access_token=access_token, client_secret=instagram_config['client_secret'])
      recent_media, next = api.user_recent_media()
      media_data = []
      for media in recent_media:
        caption = str(media.caption)
        text = re.sub(r".* said ", "", caption)
        data = {"image_url": media.get_standard_resolution_url(), "content_text": text}
        media_data.append(data)
    
      print "data obtained"
      print json.dumps(media_data)
      lastthing = emotions(media_data)
      if lastthing:
          #return "Success!" # try
          return render_template("result.html", playlist_uri=lastthing[0], emotion=lastthing[1], moods=",".join(map(str,MS_EMOTIONS[lastthing[1]])))
      

  except Exception as e:
      return str(e)

######
###### TERRITORIO DE RENE
######
GN_CLIENT=os.environ["GN_CLIENT"]
GN_USER=os.environ["GN_USER"]

SF_CLIENT=os.environ["SF_CLIENT"]
SF_SECRET=os.environ["SF_SECRET"]

GN_ENDPOINT="https://c1126262591.web.cddbp.net/webapi/json/1.0"

GN_MOODS={
  '42942': 'Tender',
  '42945': 'Empowering',
  '42946': 'Easygoing',
  '42947': 'Sensual',
  '42948': 'Somber',
  '42949': 'Melancholy',
  '42951': 'Defiant',
  '42953': 'Fiery',
  '42954': 'Sophisticated',
  '42955': 'Urgent',
  '42958': 'Aggressive',
  '42960': 'Excited',
  '42961': 'Energizing',
  '65322': 'Peaceful',
  '65323': 'Romantic',
  '65324': 'Sentimental',
  '65325': 'Yearning',
  '65326': 'Cool',
  '65327': 'Gritty',
  '65328': 'Serious',
  '65329': 'Brooding',
  '65330': 'Rowdy',
  '65331': 'Stirring',
  '65332': 'Lively',
  '65333': 'Upbeat'
}

GN_REVERSE_MOODS = dict()
for mood_id,mood in GN_MOODS.items():
  GN_REVERSE_MOODS[mood] = mood_id

MS_EMOTIONS={
  "anger": {"Serious", "Brooding", "Fiery", "Defiant", "Aggressive"},
  "contempt": {"Melancholy", "Yearning", "Somber", "Sentimental"},
  "disgust": {"Somber", "Brooding", "Defiant", "Serious", "Gritty"},
  "fear": {"Aggressive", "Stirring", "Gritty", "Urgent", "Energizing"},
  "happiness": {"Romantic", "Rowdy", "Lively", "Peaceful", "Sensual"},
  "neutral": {"Sophisticated", "Defiant", "Cool", "Empowering", "Easygoing"},
  "sadness": {"Yearning", "Sentimental", "Romantic", "Melancholy", "Tender"},
  "surprise": {"Upbeat", "Lively", "Cool", "Easygoing", "Excited"}
}

SF_SCOPES="playlist-modify-private playlist-modify-public playlist-read-private"
emotion_to_id = dict()
for emotion, moods in MS_EMOTIONS.items():
  emotion_to_id[emotion] = [GN_REVERSE_MOODS[mood] for mood in moods]

@app.route("/spotify")
def spotify_auth():
  sp_oauth = get_oauth()
  return redirect(sp_oauth.get_authorize_url(), code=302)

@app.route("/oauth/callback")
def oauth_callback():
  if request.args.get("code"):
    get_spotify(request.args.get("code"))
  
  return redirect("/")#json.dumps(get_spotify().current_user())

#@app.route("/emotion", methods=["GET"])
def emotions(photos):
  if not session.get("token", None):
    redirect("/spotify", code=302)
  
  #ars = [{'image_url': 'https://instagram.faep3-1.fna.fbcdn.net/t51.2885-15/s640x640/sh0.08/35/17881508_1190724064383967_3993470105173360640_n.jpg', 'content_text': 'No warning, no nothing, just missiles.'},{'image_url': 'https://instagram.faep3-1.fna.fbcdn.net/t51.2885-15/e35/17818806_527522910705172_1778182577270554624_n.jpg', 'content_text': 'El peor dia de mi vida'}]

  photo_res = photo_ml(photos[:5])
  #print json.dumps(photo_res)
  emotions = {emotion : photo_res["emotions"][emotion] for emotion in MS_EMOTIONS.keys()}
  #print json.dumps(emotions)
  top_emotion = max(emotions, key=emotions.get)#jsonify(emotions)
  #print "top emotion: " + top_emotion
  #top_emotion = "anger"
  # construct playlist
  payload = {"client": GN_CLIENT, "user": GN_USER, "filter_mood": ", ".join(map(str,emotion_to_id[top_emotion])), "era": "42877"}
  r = requests.get(GN_ENDPOINT+"/radio/create", params=payload)
  response = r.json()["RESPONSE"][0]["ALBUM"]
  #print "gn res: " + json.dumps(response)
  playlist = []
  for album in response:
    artist = album["ARTIST"][0]["VALUE"]
    track = album["TRACK"][0]["TITLE"][0]["VALUE"]
    playlist.append((artist, track))

  print "playlist: " + json.dumps(playlist)
  # search in spotify
  spotify = get_spotify()#spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(SF_CLIENT, SF_SECRET))
  spotify_ids = []
  for track in playlist:
    s_track = spotify.search(" ".join(track), type="track", limit=1)
    if len(s_track["tracks"]["items"]) > 0:
      spotify_ids.append(s_track["tracks"]["items"][0]["id"])

  # create playlists if doesnt exist
  playlist = spotify.user_playlist_create(spotify.current_user()["id"], "Your Instagram photos: " + top_emotion)
  print "uris: " + json.dumps(spotify_ids)
  recommended_tracks = spotify.recommendations(seed_tracks=spotify_ids, min_popularity=80, limit=30)
  for track in recommended_tracks["tracks"]:
    spotify_ids.append(track["uri"])

  updated_playlist = spotify.user_playlist_add_tracks(spotify.current_user()["id"], playlist["id"], spotify_ids)

  return (urllib.quote_plus(playlist["uri"]), top_emotion)#jsonify(updated_playlist)

def get_oauth():
  return SpotifyOAuth(SF_CLIENT, SF_SECRET, "https://moodeejay.herokuapp.com/oauth/callback", scope=SF_SCOPES, cache_path=None)

def get_spotify(auth_token=None):
  oauth = get_oauth()
  token_info = session.get("token", None)
  if not token_info and auth_token:
    token_info = oauth.get_access_token(auth_token)
    session["token"] = token_info
  return spotipy.Spotify(token_info["access_token"])


###
### ML
###
def photo_ml(array):
  image_age = image_sentiment = 0
  image_emotions = {"anger":0,"contempt":0,"disgust":0,"fear":0,"happiness":0,"neutral":0,"sadness":0,"surprise":0} 
  response = {}
  for i in array:
    url = i["image_url"] #'https://instagram.fsst1-2.fna.fbcdn.net/t51.2885-15/e35/17818239_241984309542803_360515474607308800_n.jpg'
    text = i["content_text"]
    if image.process_image(url) != False:
        emotions = photo_processing.total_score(image.process_image(url)[0])

        info = image.process_image(url)[1]
        age = sum([j["age"] for j in info["faces"]])/len(info["faces"])

        #sentiment_score = sentiment.process_text(text)

        image_age += age
        #if sentiment_score:
        #    image_sentiment += sentiment_score
        image_emotions["anger"] += emotions[0]["anger"]
        image_emotions["contempt"] += emotions[0]["contempt"]
        image_emotions["disgust"] += emotions[0]["disgust"]
        image_emotions["fear"] += emotions[0]["fear"]
        image_emotions["happiness"] += emotions[0]["happiness"]
        image_emotions["neutral"] += 0#emotions[0]["neutral"]
        image_emotions["sadness"] += emotions[0]["sadness"]
        image_emotions["surprise"] += emotions[0]["surprise"]
  n = len(array)
  response['emotions']={"anger": image_emotions["anger"], "contempt": image_emotions["contempt"], "disgust": image_emotions["disgust"], "fear": image_emotions["fear"],"happiness": image_emotions["happiness"],"neutral": image_emotions["neutral"],"sadness": image_emotions["sadness"],"surprise": image_emotions["surprise"]}
  response['age']= image_age/n
  #response['sentiment']= image_sentiment/n
  return response


if __name__ == "__main__":
  app.run(debug = True)