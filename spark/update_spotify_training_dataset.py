'''
Per fare l'update dei dati su cui far fare a spark il training.
Perchè le playlist cambiano anche di giorno in giorno, e anche tra mesi la moda può cambiare
'''
from getpass import getpass
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from time import sleep
import json
import pandas as pd


#Each playlist has 50 songs
Top_songs_global = "37i9dQZEVXbNG2KDcFcKOF" #updated weekly
Top_50_global = "37i9dQZEVXbMDoHDwVN2tF" #updated daily
Viral_50_global = "37i9dQZEVXbLiRSasKsNU9" #updated daily
playlists_ids = [Top_songs_global, Top_50_global, Viral_50_global]
# playlists_ids = [Top_songs_global]


class Track:
    track_id = "" #l'id del track su spotify
    name = ""
    acousticness = 0.0
    danceability = 0.0
    instrumentalness = 0.0
    liveness = 0.0  # quanto è dal vivo
    speechiness = 0.0  # quanto c'è del parlato
    valence = 0.0  # happiness
    energy = 0.0

    def __init__(
        self,
        acousticness,
        danceability,
        instrumentalness,
        liveness,
        speechiness,
        valence,
        energy,
        *args,
        **kwargs
    ):
        self.acousticness = acousticness
        self.danceability = danceability
        self.instrumentalness = instrumentalness
        self.liveness = liveness
        self.speechiness = speechiness
        self.valence = valence
        self.energy = energy

    def toJSON(self):
        return self.__dict__

    def __str__(self) -> str:
        return json.dumps(self.__dict__)

    def printJson(self):
        printJson(self.__dict__)


client_id = getpass("Client id: ")
client_secret = getpass("Client secret: ")
try:
    auth_manager = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    sp.search("a", limit=1) #ricerca di prova server
except:
    print("Can't connect to spotify client, exiting..")
    exit()

def printJson(item):
    print(json.dumps(item, indent=4))

def getPlaylistTracks(playlist_id):
    return sp.playlist_tracks(playlist_id)  # prende solo tracks (esclude episodi)

def getAudioFeatures(playlist_id):
    return sp.audio_features([playlist_id])

def loadTrack(track):
    x = Track(**json.loads(track))
    return x


def main():
    table = {"acousticness": {}, "danceability": {}, "instrumentalness": {}, "liveness": {}, "speechiness": {}, "valence": {}, "energy": {}, "track_id": {}, "name": {}}
    
    tracks_arr = []
    for playlist_id in playlists_ids:
        # prendo i brani della playlist
        tracks = list(map(lambda x: x["track"], getPlaylistTracks(playlist_id)["items"]))
        for track in tracks:
            x = loadTrack(json.dumps(getAudioFeatures(track["id"])[0]))
            x.track_id = track["id"]
            x.name = track["name"]
            tracks_arr.append(x)
            
    for i, track in enumerate(tracks_arr):
        # track.printJson()
        track = json.loads(json.dumps(track.__dict__))
        for feature in table.keys():
            table[feature].update({i: track[feature]})
    print("\nGot "+str(i+1)+" track features")
    
    table = json.dumps(table)
    df = pd.read_json(table)
    # Se non specifico "index=None" mette automaticamente un indice partendo da 0, e posso impostare il nome del campo (che altrimenti non ha nome), così: df.index.name = "id"
    df.to_csv("spark/top_songs.csv", index=None)
    
    
    return 1

main()
