from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse
from sqlalchemy import event
from werkzeug.security import check_password_hash, generate_password_hash
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask import request
import os
from pymongo import MongoClient
import certifi
ca = certifi.where()


# app = Flask(__name__, static_folder='./build', static_url_path='/')



app = Flask(__name__)

# if __name__ == "__main__":
#     app.run(host='0.0.0.0', debug=False, port=os.environ.get('PORT', 80))


# Members API route
# @app.route('/')
# def index():
#     return app.send_static_file('index.html')  
# jbG1kDkSwwyZVssJ


client = MongoClient('mongodb+srv://gwills:jbG1kDkSwwyZVssJ@cluster0.kdtylku.mongodb.net/test?retryWrites=true&w=majority', tlsCAFile = ca)
userDB = client['userInfo']
users = userDB['random']
projectDB = client['projects']
projects = projectDB['data']

@app.route("/new/<username>/<password>/<uid>", methods=["GET"])
def newUser(username, password, uid):
    
    if users.find_one({'username': username}):
        return username + " is already a user"
    userData = {
        'username' : username,
        'password' : password,
        'uid' : uid,
        'projects' : {}
    }
    users.insert_one(userData)
    return 'done'
    

@app.route("/confirm/<username>/<password>", methods=["GET"])
def confirm(username, password):
    signIn = users.find_one({'username' : username})
    if not signIn:
        return username + " is not a user for the website"
    if signIn['password'] != password:
        return password + ' is not the correct password'
    return username + " is a user for the website"


@app.route("/members")
def members():
    return {"members": ["Member1", "Member2", "Member4"]}

    
# This function queries the projectId and quantity from the URL and returns the
# project id and quantity to the front end. The front end displays a pop-up message
# which says “<qty> hardware checked in”
@app.route('/checkIn/<projectid>/<hwset>/<qty>/<maxQty>', methods=['GET'])   #change this to 'PUT' and need to add {method: 'PUT'} to the fetch in hwset.js
def checkIn_hardware(projectid, hwset, qty, maxQty):

    hwSet = int(hwset)
    pj = projects.find_one({'projectID': projectid})
    currQty = pj['HWSet'][hwSet-1]
    qty = int(qty)
    maxQty = int(maxQty)
    
    if currQty == maxQty:
        #already full
        newQty = maxQty
        setsCheckedIn = 0
        #none can be checked in
    elif (currQty + qty) > maxQty:
        #don't update
        newQty = maxQty
        projects.update_one({'projectID': projectid},{'$set': {'HWSet.'+str(hwSet-1): maxQty}})
        setsCheckedIn = currQty
        #more are being checked in than space is avaliable
    else:
        newQty = currQty + qty
        setsCheckedIn = qty
        projects.update_one({'projectID': projectid},{'$set': {'HWSet.'+str(hwSet-1): newQty}})
        #normal

    returnData = {
        "projectid": projectid,
        "hwset": hwset,
        "qty": newQty,
        "maxQty" : maxQty,
        "setsCheckedIn": setsCheckedIn}

    print(returnData)
    return jsonify(returnData)

# This function queries the projectId and quantity from the URL and returns the
# project id and quantity to the front end. The front end displays a pop-up message
# which says “<qty> hardware checked out”
@app.route('/checkOut/<projectid>/<hwset>/<qty>/<maxQty>', methods=['GET'])
def checkOut_hardware(projectid, hwset, qty, maxQty):
    hwSet = int(hwset)
    pj = projects.find_one({'projectID': projectid})
    currQty = pj['HWSet'][hwSet-1]
    qty = int(qty)
    maxQty = int(maxQty)
    
    if currQty == 0:
        #there are zero sets when the user tries to check out sets
        newQty = 0
        setsCheckedOut = 0
        #send an error that no units are avaliable
    elif currQty - qty >= 0:
        #there is adequate sets that are trying to be checked out
        newQty = currQty - qty
        setsCheckedOut = qty
        projects.update_one({'projectID': projectid},{'$set': {'HWSet.'+str(hwSet-1): newQty}})
    else:
        #this is when the user tries to check out more sets than what is avaliable
        newQty = 0
        setsCheckedOut = currQty
        projects.update_one({'projectID': projectid},{'$set': {'HWSet.'+str(hwSet-1): 0}})
        #throw a flag that a different amount was checked in than requested

  
    returnData = {
        "projectid": projectid,
        "hwset": hwset,
        "qty": newQty,
        "maxQty": maxQty,
        "setsCheckedOut": setsCheckedOut}

    return jsonify(returnData)


# This function queries the projectId from the URL and returns the project id to the
# front end. The front end displays a pop-up message which says “Joined <projectId>”
@app.route('/joinProject/<projectid>/<userID>/<username>', methods=['GET'])
def joinProject(projectid, userID, username):
    users.update_one({'username': username},{'$set': {'projects.' + str(projectid): [0,0]}})
    projects.update_one({'projectID': projectid},{'$set': {'users.' + str(userID):  True}})
    # return "Joined " + projectid
    return projectid

# This function queries the projectId from the URL and returns the project id to the
# front end. The front end displays a pop-up message which says “Left <projectId>”
@app.route('/leaveProject/<projectid>/<userID>/<username>', methods=['GET'])
def leaveProject(projectid, userID, username):
    users.update_one({'username': username},{'$set': {'projects.' + str(projectid): [0,0]}})
    projects.update_one({'projectID': projectid},{'$set': {'users.' + str(userID):  False}})
    return projectid


if __name__ == "__main__":
    app.run(debug=True)
