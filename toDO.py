from flask import Flask, redirect, render_template, url_for, request, session, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from authlib.integrations.flask_client import OAuth

import os
import pathlib
import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
#from flask_github import GitHub

app = Flask(__name__)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

############ 1. Sign in using any one of: gmail, facebook or github login.
oauth = OAuth(app)
#set up home page for log in

@app.route('/')
def homePage():
    return render_template("home.html")

app.config['SECRET_KEY'] = "123098"
app.config['GOOGLE_CLIENT_ID'] = "269996139987-gp7j5mjjchkeh03dsvgvq5jjmdbumgg3.apps.googleusercontent.com" 
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "googleclient.json")  
flow = Flow.from_client_secrets_file(  
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],  
    redirect_uri="http://127.0.0.1:5000/callback"  
)

def login_is_required(function):  #a function to check if the user is authorized or not
    def wrapper(*args, **kwargs):
        if "google_id" not in session:  #authorization required
            return abort(401)
        else:
            return function()

    return wrapper

#   GOOGLE: login
@app.route('/login')
def google_login():
    authorization_url, state = flow.authorization_url()  
    session["state"] = state
    return redirect(authorization_url)

#   GOOGLE: authorize
@app.route("/callback")  
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=app.config["GOOGLE_CLIENT_ID"]
    )

    session["google_id"] = id_info.get("sub")  
    session["name"] = id_info.get("name")
    return redirect(url_for("dashboard"))


#   DATABASE: Initialise 
app.config['SQLALCHEMY_DATABASE_URL']='sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db=SQLAlchemy(app)

#   DATABASE: Create
class TODO(db.Model):
    setID = db.Column(db.Integer, primary_key=True)             #assign id 
    setNAME=db.Column(db.String(250))                           #write name 
    setCOMP=db.Column(db.Boolean)                               #mark as completed or not

    def __repr__(self):
        return '<Task %r>'% self.setID

#Avoid sqlalchemy OperationalError
@app.before_first_request
def create_tables():
    db.create_all()

############ 2. Add TODO items.

@app.route("/add", methods=["POST"])
def addTask():
    setNAME=request.form.get("title")
    create_task=TODO(setNAME=setNAME, setCOMP=False)
    db.session.add(create_task)
    db.session.commit()
    return redirect(url_for("dashboard"))


############ 3. Delete TODO items.

@app.route("/delete/<int:taskID>")
def deleteTask(taskID):
    task=TODO.query.filter_by(setID=taskID).first()
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("dashboard"))

############ 4. List all TODO items.

@app.route("/all")  
def dashboard():
    #show all tasks
    all_task=TODO.query.all()
    return render_template("dashboard.html",all_task=all_task)

############ 5. Mark TODO items as complete.

@app.route("/update/<int:taskID>")
def updateTask(taskID):
    task=TODO.query.filter_by(setID=taskID).first()
    task.setCOMP=not task.setCOMP
    db.session.commit()
    return redirect(url_for("dashboard"))

if __name__=="__main__":    
    app.run(debug=True)