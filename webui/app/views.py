import json
from app import app
from app import producer as producer
from flask import Flask, render_template, request, redirect, url_for, Response


logged = False

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login")
def login():
    return render_template("login.html")

@app.post("/login")
def tryLogin():
    global logged
    client_id = request.form.get("client_id")
    client_secret = request.form.get("client_secret")
    if producer.login(client_id, client_secret):
        logged = True
        return redirect("/home")
    else:
        logged = False
        return redirect(url_for("login"))

@app.route("/home")
def app_route():
    if not logged:
        return redirect(url_for("login"))
    
    return render_template("home.html")

@app.route('/home/search')
def spotifySearch():
    global lista_risultati, query
    if not logged:
        return redirect(url_for("login"))
    # query = request.form.get("query")
    # query_type = request.form.get("query_type")
    query = request.args.get("query")
    query_type = request.args.get("query_type")
    if (query_type == "track"):
        lista_risultati = producer.searchTracks(query)
    else:
        lista_risultati = producer.searchPlaylists(query)
    status = lista_risultati.pop(0)
    return render_template("home.html", status=status, lista=lista_risultati, query=query)

@app.route("/send")
def sendToLogstash():
    if not logged:
        return redirect(url_for("login"))
    item_type = request.args.get("type")
    item_id = request.args.get("id")

    if item_type == "playlist":
        producer.do_playlist(item_id, None, True)
    elif item_type == "track":
        producer.do_track(item_id, None, True)
    return render_template("home.html", status="", lista=lista_risultati, query=query)

@app.route("/view")
def viewFeatures():
    if not logged:
        return redirect(url_for("login"))
    item_type = request.args.get("type")
    item_id = request.args.get("id")
    limit = int(request.args.get("limit"))
    
    if item_type == "playlist":
        item = producer.do_playlist(item_id, limit, False)
    elif item_type == "track":
        item = producer.do_track(item_id, None, False)
    else:
        return "not found", 204, {"Content-Type": "text/plain"}
    return json.dumps(item), 200, {'Content-Type': 'application/json'}
