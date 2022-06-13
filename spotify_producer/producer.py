'''
Per non inviare a logstash, ma stampare i risultati su console (per debug), imposta la variabile "debug" a True (linea ~71)
'''
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from time import sleep
import json
import socket
from getpass import getpass


class Track:
    id = ""
    playlist = ""
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
        # return str(self.__dict__)
        return json.dumps(self.__dict__)

    def printJson(self):
        printJson(self.__dict__)
        
os.system("clear -x")
client_id = getpass("Client id: ")
client_secret = getpass("Client secret: ")
try:
    auth_manager = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    sp.search("a", limit=1)
except:
    print("Can't connect to spotify client, exiting..")
    exit()
logstash = ("logstash", 6000)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

online = False
debug = False

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



def log_send(message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(logstash)
        s.sendall(message.encode())
        s.close()
        # print("Inviato")


def getUserPlaylists(username):
    return sp.user_playlists(username)


def getPlaylistTracks(playlist_id):
    return sp.playlist_tracks(playlist_id)  # prende solo tracks (esclude episodi)


def getAudioFeatures(playlist_id):
    return sp.audio_features([playlist_id])


def getAudioAnalysis(track_id):
    sp.audio_analysis(track_id)


def printJson(item):
    print(json.dumps(item, indent=4))


def loadTrack(track):
    x = Track(**json.loads(track))
    return x


def getArtistsNames(track):
    artists_arr = []
    for artist in track["artists"]:
        artists_arr.append(artist["name"])
    return ', '.join(artists_arr)




# --------------------------------Querying--------------------------

def searchPlaylists():
    # Cerca playlist su spotify da stringa utente
    results = ""
    while not results:
        query = input("\nPlaylists search keyword ('exit' to exit): ")
        if (query == "exit"): return 0
        try:
            results = sp.search(query, limit=10, type="playlist")["playlists"]["items"]
        except:
            print("Again")
            continue
        if not results:
            print("No results")

    # Lista le playlist risultate
    print()
    for i, playlist in enumerate(results):
        print(str(1 + i) + ". " + playlist["name"])
    print("0. Search again")
    
    # Scegli quale playlist analizzare
    choice = -1
    while choice < 0 or choice > len(results):
        try:
            choice = int(input("Select result number: "))
        except:
            continue
    if (choice == 0): return 0
    
    playlist_id = results[choice - 1]["id"]

    # prendo i brani della playlist
    # tracks = list(map(lambda x: x["track"], getPlaylistTracks(playlist_id)["items"]))
    res = sp.playlist_tracks(playlist_id)
    i = 0
    if (online and not debug):
        print("\nSending tracks...\n")
    while res:
        for item in res["items"]:
            track = item["track"]
            # Costruisco il nuovo oggetto brano
            track_obj = loadTrack(json.dumps(getAudioFeatures(track["id"])[0]))
            track_obj.id = track["id"]
            track_obj.name = (track["name"] + " - " + getArtistsNames(track))
            track_obj.playlist = results[choice -1]["name"]
            
            # Invio a logstash o stampo su console l'oggetto brano
            if (online and not debug):
                log_send(track_obj.__str__())
                i+=1
            else:
                track_obj.printJson()
                
        # Prendo i successivi 100 brani nella playlist
        if res["next"]:
            res = sp.next(res)
        else:
            res = None
    
    print("\nSent "+str(i)+" track features to logstash")

    return 1


def searchTracks():
    results = ""
    while not results:
        query = input("\nTrack search keyword ('exit' to exit): ")
        if (query == "exit"): return 0
        try:
            results = sp.search(query, limit=10, type="track")["tracks"]["items"]
        except:
            print("Again")
            continue
        if not results:
            print("No results")

    # Lista i track risultati
    print()
    artists_arr = []
    for i, track in enumerate(results):
        print(str(1 + i) + ". " + track["name"] + " - " + getArtistsNames(track))
    print("0. Search again")
        
    choice = -1
    while choice < 0 or choice > len(results):
        try:
            choice = int(input("Select result number: "))
        except:
            continue
    if (choice == 0): return 0

    track_id = results[choice - 1]["id"]
    
    track = loadTrack(json.dumps(getAudioFeatures(track_id)[0]))
    track.id = track_id
    track.name = (results[choice-1]["name"] + " - " + getArtistsNames(results[choice-1]))
    
    if (online and not debug):
        log_send(track.__str__())
        print("\nSent track features")
    else:
        track.printJson()

    return 1



def main():
    while True:
        menu = input("\n\nSearch for:\n1.Track\n2.Playlist\n0.Exit\n> ")
        if (menu == "2"):
            searchPlaylists()
        elif (menu == "1"):
            searchTracks()
        elif (menu == "0"): break
        else: print("Again\n\n")
            

main()
