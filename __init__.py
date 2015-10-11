from flask import Flask, render_template, session, redirect, request
import pymongo
import hashlib
import uuid
import time
import json
import base64
import bson

app = Flask(__name__)
app.secret_key = "askdk2k12k31231239asd9dsfsdf0024l123llsdflsdlf;34;123i1239w0fd0sd0f0123k12k3kksdfksdkfq1241293123papsdpasdp1203012eafksdkf"
db = pymongo.MongoClient("localhost", 27017).text

@app.route("/login/", methods=['GET', 'POST'])
def login():
    if "login" in session:
        return redirect("/text/")
    if request.method == "POST":
        username = request.form['username']
        password = protect(request.form['password'])
        if db.members.find_one({"username":username, "password":password}):
            db.queue.insert({"cmd":"getUnreadMessages", "username":username,  "args":[]})
            session['login'] = username
            return redirect("/text/")
        else:
            return "Login Failed"

    return render_template("login.html")

@app.route("/register/", methods=['GET', 'POST'])
def register():
    if "login" in session:
        return redirect("/text/")
    if request.method == "POST":
        username = request.form['username']
        password = protect(request.form['password'])
        if db.members.find_one({"username":username}):
            return "Username already taken"
        else:
            db.queue.insert({"cmd":"getUnreadMessages", "username":username, "args":[]})
            db.members.insert({"username":username, "password":password})
            session['login'] = username
            return redirect("/text/")
    
    return render_template("register.html")

@app.route("/text/", methods=['GET', 'POST'])
def text_default():
    if "login" not in session:
        return redirect("/login/")
    conversations = db.texts.find({"username":session['login']})
    cout = {}
    for x in conversations:
        if x['number'] not in cout:
            cout[x['number']] = x
        elif int(x['uid']) > int(cout[x['number']]['uid']):
            cout[x['number']] = x
    return render_template("text_default.html", conversations=cout, fetchLabel=fetchLabel)

@app.route("/text/raw/")
def text_def_2():
    if "login" not in session:
        return redirect("/login/")
    conversations = db.texts.find({"username":session['login']})
    cout = {}
    for x in conversations:
        if x['number'] not in cout:
            cout[x['number']] = x
        elif int(x['uid']) > int(cout[x['number']]['uid']):
            cout[x['number']] = x
    return render_template("text_raw.html", conversations=cout, fetchLabel=fetchLabel)

@app.route("/text/<number>", methods=['GET', 'POST'])
def text(number):
    if "login" not in session:
        return redirect("/login/")
    if request.method == "POST":
        if request.form.get("text"):
            text = request.form['text']
            db.texts.insert({"username":session['login'], "number":number, "uid":time.time(), "message":text, "sent":True})
            sendCommand("sendMessage", [number, text[:255]])
            return redirect("/text/{}".format(number))
        else:
            label = request.form['label']
            return redirect("/label/{0}/{1}".format(number, label))
    return render_template("text.html", number=number, fetchLabel=fetchLabel)

@app.route("/text/raw/<number>")
def text_raw_2(number):
    if "login" not in session:
        return redirect("/login/")
    conversation = db.texts.find({"username":session['login'], "number":number}).sort("_id", -1)
    return render_template("text_raw_bubbles.html", conversation=conversation, fetchLabel=fetchLabel)

def sendCommand(command, args, username=None):
    if not username:
        username = session['login']
    if not db.queue.find_one({"username":username, "cmd":command}):
        db.queue.insert({"username":username, "args":args, "cmd":command})

@app.route("/api/sendUnreadMessages/<data>/<key>")
def sendUnreadMessages(data, key):
    username = db.keys.find_one({"key":key})
    if not username:
        return "None"
    else:
        username = username['username']
        data = json.loads(base64.b64decode(data.replace("[", "/")))
        for x in data['data']:
            uid = x['date']
            message = x['body']
            number = x['address']
            if not db.texts.find_one({"username":username, "uid":uid}):
                db.texts.insert({"username":username , "uid":uid, "message":message, "number":number, "sent":False})
        return "Success"

@app.route("/api/login/<username>/<password>")
def api_login(username, password):
    check = db.members.find_one({"username":username, "password":protect(password)})
    if check:
        db.keys.remove({"username":username})
        key = uuid.uuid4().hex
        db.keys.insert({"key":key, "username":username, "timestamp":time.time()})
        return json.dumps({"success":True, "key":key}), 200
    else:
        return json.dumps({"success":False}), 200

@app.route("/api/ping/<key>")
def api_ping(key):
    key = db.keys.find_one({"key":key})
    if key:
        for x in db.queue.find({"username":key['username']}):
            db.queue.remove({"_id":bson.ObjectId(x['_id'])})
            return json.dumps({"success":True, "data":{"command":x['cmd'], "args":x['args']}}), 200
        sendCommand("sendUnreadMessages", [], username=key['username'])
        return "{\"data\":false}"
    else:
        return "{\"data\":false}"

@app.route("/label/<number>/<label>")
def label(number, label):
    if "login" not in session:
        return redirect("/login/")
    check = db.labels.remove({"number":number, "username":session['login']})
    db.labels.insert({"number":number, "username":session['login'], "label":label})
    return redirect("/text/{}".format(number))

def fetchLabel(number, username):
    check = db.labels.find_one({"number":number, "username":username})
    if not check:
        return number
    else:
        return check['label']

def protect(string):
    for x in range(1000):
        string = hashlib.sha512(string).hexdigest()
    return string

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
