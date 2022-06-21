# from app import app
import webbrowser
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import json
import socket
from time import sleep


playlist_limit = 10
tracks_limit = 10
debug = False

client_id = ""
client_secret = ""
sp = None

logstash = ("logstash", 6000)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

online = False

def tryLogstashConnection()-> bool:
    global online
    try:
        s.connect(logstash)
        s.close()
        online = True
    except socket.error as e:
        # print("\nCan't connect to logstash, error: "+str(e)+", number: "+str(e.errno)+"\n")
        pass
    return online

if (not debug):
    if (not online and not tryLogstashConnection()):
            print("\nWaiting for logstash...\n")

    while not online:
        sleep(4)
        if (tryLogstashConnection()):
            online = True
            print("Connected to logstash")
else:
    print("\nDebug mode")

# Apro automaticamente la pagina nel browser
webbrowser.open("http://localhost:5001")

def login(id: str, secret: str)-> bool:
    global sp
    try:
        auth_manager = SpotifyClientCredentials(
            client_id=id,
            client_secret=secret
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        sp.search("a", limit=1)
        return True
    except:
        print("Can't connect to spotify client, exiting..")
        return False
    
def log_send(message):
    message = json.dumps(message)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(logstash)
        s.sendall(message.encode())
        s.close()
        # print("Inviato")

# ritorna un oggetto json, con i campi "name", "id", "energy", ..
def do_track(track_id: str, playlist_name: str, auto_send: bool)-> object:
    track = sp.track(track_id)
    feats = sp.audio_features(track_id)[0]
    res = {
        "name": (track["name"]+" - "+getArtistsNames(track)),
        "id": track["id"],
        "acousticness": feats["acousticness"],
        "speechiness": feats["speechiness"],
        "valence": feats["valence"],
        "energy": feats["energy"],
        "instrumentalness": feats["instrumentalness"],
        "liveness": feats["liveness"],
        "danceability": feats["danceability"],
    }
    if playlist_name:
        res["playlist"] = playlist_name
    if auto_send:
        if online and not debug:
            log_send(res)
        else:
            print(json.dumps(res, indent=4))
    return res

# ritorna una lista di oggetti json (i tracks)
def do_playlist(playlist_id: str, limit: int, auto_send: bool)-> list:
    playlist = sp.playlist(playlist_id)
    playlist_tracks = sp.playlist_tracks(playlist_id)
    res = []
    
    while playlist_tracks:
        
        for i, item in enumerate(playlist_tracks["items"]):
            track = item["track"]
            res.append(do_track(track["id"], playlist["name"], auto_send))
            if limit and len(res) >= limit:
                return res

        if playlist_tracks["next"]:
            playlist_tracks = sp.next(playlist_tracks)
        else:
            playlist_tracks = None

    return res

def getPlaylistAudioFeatures(playlist_id: str)-> object:
    l = []
    for item in sp.playlist_tracks(playlist_id)["items"]:
        l.append(item["track"])
    return sp.audio_features([playlist_id])

def getArtistsNames(track)-> str:
    artists_arr = []
    for artist in track["artists"]:
        artists_arr.append(artist["name"])
    return ', '.join(artists_arr)



# --------------------------------Querying--------------------------

def searchPlaylists(query: str)-> list:
     # Cerca playlist su spotify da stringa utente
    results = None
    try:
        results = sp.search(query, limit=playlist_limit, type="playlist")["playlists"]["items"]
    except:
        return ["Retry"]
    if not results:
        return ["No results"]

    # raccoglie in lista le playlist risultate
    playlists = [""]
    for playlist in results:
        playlists.append({"name": playlist["name"], "id": playlist["id"], "type": "playlist"})
    return playlists

def searchTracks(query: str)-> list:
    results = None
    try:
        results = sp.search(query, limit=tracks_limit, type="track")["tracks"]["items"]
    except:
        return ["Retry"]
    if not results:
        return ["No results"]

    # raccoglie in lista i track risultati
    tracks = [""]
    for track in results:
        tracks.append({"name": track["name"]+" - "+getArtistsNames(track), "id": track["id"], "type": "track"})
    return tracks
