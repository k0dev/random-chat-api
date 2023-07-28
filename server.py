from flask import Flask, jsonify, abort, request
import secrets
import threading
import time

app = Flask(__name__)

lobbies = {}
current_lobby_id = -1
lobbies_lock = threading.Lock()

def get_lobby_id():
    global current_lobby_id
    current_lobby_id += 1
    return current_lobby_id

def delete_lobby_after(lobby_id, s):
    time.sleep(s)
    del lobbies[lobby_id]

@app.route("/api/status")
def status():
    return jsonify({"status": "online"})

@app.route("/api/create_lobby")
def create_lobby():
    lobby_id = get_lobby_id()
    lobby_secret_a = secrets.token_hex(nbytes=16)
    lobby_secret_b = secrets.token_hex(nbytes=16)
    lobbies[lobby_id] = {
        "secret_a": lobby_secret_a, 
        "secret_b": lobby_secret_b, 
        "chatting": False,
        "messages_a": [],
        "messages_b": []
    }
    threading.Thread(target=delete_lobby_after, args=(60,))
    return jsonify({"id": lobby_id, "secret": lobby_secret_a})

@app.route("/api/lobby_list")
def lobby_list():
    return jsonify([lobby_id for (lobby_id, value) in lobbies.items() if not value["chatting"]])

@app.route("/api/join_lobby/<int:lobby_id>")
def join_lobby(lobby_id):
    lobbies_lock.acquire()
    if lobby_id in lobbies and not lobbies[lobby_id]["chatting"]:
        lobbies[lobby_id]["chatting"] = True
        lobbies_lock.release()
        return jsonify({"secret": lobbies[lobby_id]["secret_b"]})
    else:
        lobbies_lock.release()
        abort(404)

@app.route("/api/send_message/<int:lobby_id>", methods=["POST"])
def send_message(lobby_id):
    if lobby_id in lobbies:
        secret = request.form["secret"]
        message = request.form["message"]
        messages = None
        if secret == lobbies[lobby_id]["secret_a"]:
            messages = lobbies[lobby_id]["messages_a"]
        elif secret == lobbies[lobby_id]["secret_b"]:
            messages = lobbies[lobby_id]["messages_b"]
        else:
            abort(404)
        if message is not None and len(message.strip()) > 0:
            messages.append(message)
            print(lobbies[lobby_id])
            return ""
        else:
            abort(404)
    else:
        abort(404)

@app.route("/api/read_messages/<int:lobby_id>", methods=["POST"])
def read_messages(lobby_id):
    if lobby_id in lobbies:
        secret = request.form["secret"]
        messages = None
        if secret == lobbies[lobby_id]["secret_a"]:
            messages = lobbies[lobby_id]["messages_b"]
        elif secret == lobbies[lobby_id]["secret_b"]:
            messages = lobbies[lobby_id]["messages_a"]
        else:
            abort(404)
        response = {"messages": messages[:]}
        messages.clear()
        print(lobbies[lobby_id])
        return jsonify(response)
    else:
        abort(404)