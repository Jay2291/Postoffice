import datetime
import random
from flask import Flask, redirect, url_for,render_template, request, session, flash, jsonify
from datetime import timedelta, datetime
from flask_mysqldb import MySQL
import MySQLdb.cursors 
import time

app = Flask(__name__)
app.secret_key = "key"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Jayjagtap@2291'
app.config['MYSQL_DB'] = 'Postoffice'

mysql = MySQL(app)

def update_status(parid):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(f"SELECT last_updated FROM parcel WHERE parcelid={parid}")
    row = cursor.fetchone()
    if row:  
        last_updated = row['last_updated']  
        target_time = last_updated + timedelta(seconds=random.uniform(10, 30))
        if datetime.now() >= target_time:
            return parid
        else:
            return 0

@app.route("/home")
def home():
    if "loggedin" in session:
        ui = session['userid'],
        un = session["username"],
        add = session["address"],
        phone = session["phone"]
        return jsonify({
                    "user":
                    {
                        'User ID': ui,
                        'Username': un,
                        'Address': add,
                        'Phone no.': phone,
                    }
                        }
                    )
    else:
        return jsonify({'message': 'User not loggedin.'})

@app.route("/")
@app.route("/login", methods = ["POST","GET"])
def login():
    if request.method == "POST" and 'user' in request.json:
        user = request.json["user"]
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"SELECT * FROM user WHERE userid = {user}")
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session["userid"] = account["userid"]
            session["username"] = account["username"]
            session["address"] = account["address"]
            session["phone"] = account["phoneno"]
            return jsonify({
                'message': 'Login Successfull',
                
            })
        else:    
            return jsonify({'message': 'User not found.'}), 404

@app.route("/signup", methods = ["POST", "GET"])
def signup():
    if request.method == "POST" and 'username' in request.json and 'address' in request.json and 'phoneno' in request.json:
        username = request.json['username']
        address = request.json['address']
        phoneno = request.json['phoneno']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"INSERT INTO user (username, address, phoneno) VALUES {username, address, phoneno}")
        mysql.connection.commit()
        cursor.execute(f"SELECT userid FROM user WHERE username = {username}")
        userid = cursor.fetchone()
        return jsonify({
            "message": "Account created Successfully.",
            "Your User ID is ": userid
        })
    else:
        return jsonify({"message": "Invalid Data"}), 400

@app.route("/update", methods = ["POST", "GET"])
def update():
    if request.method == "POST" and 'username' in request.json and 'address' in request.json and 'phoneno' in request.json:
        ui = session['userid']
        username = request.json['username']
        address = request.json['address']
        phoneno = request.json['phoneno']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"SELECT * FROM user WHERE userid = {ui}")
        account = cursor.fetchone()
        if account:
            cursor.execute(f"UPDATE user SET username='{username}', address='{address}', phoneno='{phoneno}' WHERE userid={ui}")
            mysql.connection.commit()
            return jsonify({"message":"Account updated Successfully"})
        else:
            return jsonify({"message":"Account not Found"})
    else:
        return jsonify({"message": "Invalid Data"}), 400

@app.route("/send", methods = ["POST", "GET"])
def send():
    if request.method == "POST" and 'recname' in request.json and 'address' in request.json and 'content' in request.json and 'phoneno' in request.json:
        receiver_username = request.json['recname']
        receiver_address = request.json['address']
        content = request.json['content']
        phoneno = request.json['phoneno']

        sender_username = session.get("username", "")
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        cursor.execute(f"SELECT userid FROM user WHERE username = '{sender_username}'")
        sender_info = cursor.fetchone()
        cursor.execute(f"SELECT userid FROM user WHERE username = '{receiver_username}'")
        receiver_info = cursor.fetchone()
        
        if not receiver_info:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(f"INSERT INTO user (username, address, phoneno) VALUES {receiver_username, receiver_address, phoneno}")
            mysql.connection.commit()
        cursor.execute(f"SELECT userid FROM user WHERE username = '{receiver_username}'")
        receiver_info = cursor.fetchone()
        sender_id = sender_info['userid']
        receiver_id = receiver_info['userid']
        cursor.execute(f"INSERT INTO parcel (senderid, receiverid, contenttype, status, postid) VALUES{sender_id, receiver_id, content, 'in transit', 1}")
        mysql.connection.commit()
        cursor.execute(f"SELECT parcelid FROM parcel ORDER BY parcelid DESC LIMIT 1;") 
        parid = cursor.fetchone()
        return jsonify({"message": "Parcel sent successfully",
                        "Parcel ID": parid
                        })
    else:
        return jsonify({"message": "Invalid request method"}), 405

@app.route("/status")
def status():
    if "loggedin" in session:
        ui = session['userid']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"SELECT * FROM parcel WHERE senderid = {ui}")
        parcel_info = cursor.fetchall()
        return jsonify({"Parcel": parcel_info})

@app.route("/getstatus", methods= ["POST", "GET"])
def getstatus():
    if request.method == "POST" and 'parcelid' in request.json:
        parcelid = request.json['parcelid']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"SELECT * FROM parcel WHERE parcelid = {parcelid}")
        parcel_info = cursor.fetchone()
        return jsonify({"Parcel": parcel_info})

@app.route("/recievedpost", methods=["POST", "GET"])
def recievedpost():
    if request.method == "POST" and 'postid' in request.json:
        postid = request.json["postid"]
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"SELECT * FROM parcel WHERE postid = {postid}")
        parall = cursor.fetchall()
        if parall:
            for i in parall:
                parid = i['parcelid']  
                res = update_status(parid)
                if res:
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cursor.execute(f"SELECT status FROM parcel WHERE parcelid = {parid}")
                    stat = cursor.fetchall()
                    for i in stat:
                        tus = i['status']
                        if tus == 'in transit':
                            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                            cursor.execute(f"UPDATE parcel SET status = 'Acquired' WHERE parcelid ={parid}")
                            mysql.connection.commit()
            cursor.execute(f"SELECT * FROM parcel WHERE status='Acquired' and parcelid={parid}")
            parcels = cursor.fetchall()
            return jsonify({"Parcel": parcels})
        else:
            return jsonify({"message":"NO parcels at the moment"})
    else:
        return jsonify({"message": "Invalid request method"}), 405

@app.route("/sendpost", methods=["POST", "GET"])
def sendpost():
    if request.method == "POST" and 'postid' in request.json:
        postid = request.json["postid"]
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"SELECT parcelid FROM parcel WHERE postid = {postid}")
        parall = cursor.fetchall()
        if parall:
            for i in parall:
                parid = i['parcelid']  
                res = update_status(parid)
                if res:
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cursor.execute(f"SELECT status FROM parcel WHERE parcelid = {parid}")
                    stat = cursor.fetchall()
                    for i in stat:
                        tus = i['status'] 
                        if tus.lower() == 'acquired':
                            cursor.execute(f"UPDATE parcel SET status = 'On the way' WHERE parcelid ={parid}")
                            mysql.connection.commit()
            cursor.execute(f"SELECT * FROM parcel WHERE status='On the way' and parcelid={parid}")
            parcels = cursor.fetchall()
            
            return jsonify({"Parcel": parcels})
           
        else:
            return jsonify({"message":"NO parcels at the moment"})
    else:
        return jsonify({"message": "Invalid request method"}), 405

@app.route("/recieve")
def recieve():
    if "loggedin" in session:
        ui = session['userid']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"SELECT parcelid FROM parcel WHERE receiverid = {ui}")
        receiver_info = cursor.fetchall()
        if receiver_info:
            for i in receiver_info:   
                parid = i['parcelid']
                cursor.execute(f"SELECT status FROM parcel WHERE parcelid = {parid}")
                stat = cursor.fetchall()
                
                for i in stat:
                    tus = i['status']  
                    if tus.lower() == "on the way":
                        cursor.execute(f"UPDATE parcel SET status = 'Delivered' WHERE receiverid ={ui}")
                        mysql.connection.commit()
            cursor.execute(f"SELECT * FROM parcel WHERE status='Delivered' and receiverid={ui}")
            parcels = cursor.fetchall()
            return jsonify({"Parcel": parcels})
            
        else:
            return jsonify({"message": "No parcels found for this receiver"})
    else:
        return jsonify({"message": "Receiver ID not found"})

@app.route("/logout")
def logout():
    if "loggedin" in session:
        user = session['username']
        session.pop('loggedin', None)
        return jsonify({user: "User Logged out"})  
    else:    
            return jsonify({'message': 'User not logged in.'})

if __name__ == "__main__":          
    app.run(debug=True)

    