import datetime
import random
from flask import Flask, request, session, jsonify
from datetime import timedelta, datetime
from flask_mysqldb import MySQL
import MySQLdb.cursors 

app = Flask(__name__)
app.secret_key = "key"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Jayjagtap@2291'
app.config['MYSQL_DB'] = 'Postoffice'

mysql = MySQL(app)

def delay_status(parid):
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

def change_status(parid):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(f"SELECT last_updated FROM parcel WHERE status= 'Out for delivery' and parcelid = {parid}")
    row = cursor.fetchone()
    if row:  
        last_updated = row['last_updated']  
        target_time = last_updated + timedelta(minutes=10)
        if datetime.now() >= target_time:
            return 1
        else:
            return 0

@app.route("/home")
def home():
    if "loggedin" in session:
        ui = session['userid']
        un = session["username"]
        add = session["address"]
        phone = session["phone"]
        postid = session["postal"]
        return jsonify({
                    "user":
                    {
                        'User ID': ui,
                        'Username': un,
                        'Address': add,
                        'Phone no.': phone,
                        'Postal ID': postid
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
            session["postal"] = account["postid"]
            return jsonify({
                'message': 'Login Successfull',
                
            })
        else:    
            return jsonify({'message': 'User not found.'}), 404

@app.route("/signup", methods = ["POST", "GET"])
def signup():
    if request.method == "POST" and 'username' in request.json and 'address' in request.json and 'phoneno' in request.json and 'postid' in request.json:
        username = request.json['username']
        address = request.json['address']
        phoneno = request.json['phoneno']
        postal = request.json['postid']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"INSERT INTO user (username, address, phoneno, postid) VALUES {username, address, phoneno, postal}")
        mysql.connection.commit()
        cursor.execute(f"SELECT userid FROM user WHERE username = '{username}'")
        userid = cursor.fetchone()
        return jsonify({
            "message": "Account created Successfully.",
            "Your User ID is ": userid
        })
    else:
        return jsonify({"message": "Invalid Data"}), 400

@app.route("/update", methods = ["POST", "GET"])
def update():
    if request.method == "POST" and 'username' in request.json and 'address' in request.json and 'phoneno' in request.json and 'postid' in request.json:
        ui = session['userid']
        username = request.json['username']
        address = request.json['address']
        phoneno = request.json['phoneno']
        postal = request.json['postid']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"SELECT * FROM user WHERE userid = {ui}")
        account = cursor.fetchone()
        if account:
            cursor.execute(f"UPDATE user SET username='{username}', address='{address}', phoneno='{phoneno}', postid = '{postal}' WHERE userid={ui}")
            mysql.connection.commit()
            return jsonify({"message":"Account updated Successfully"})
        else:
            return jsonify({"message":"Account not Found"})
    else:
        return jsonify({"message": "Invalid Data"}), 400

@app.route("/send", methods = ["POST", "GET"])
def send():
    if request.method == "POST" and 'recname' in request.json and 'address' in request.json and 'content' in request.json and 'phoneno' in request.json and 'postid' in request.json:
        receiver_username = request.json['recname']
        receiver_address = request.json['address']
        content = request.json['content']
        phoneno = request.json['phoneno']
        postal = request.json['postid']
        sender_username = session.get("username", "")
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"SELECT userid FROM user WHERE username = '{sender_username}'")
        sender_info = cursor.fetchone()
        cursor.execute(f"SELECT userid FROM user WHERE username = '{receiver_username}'")
        receiver_info = cursor.fetchone()
        if not receiver_info: #if receiverid not found in db
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(f"INSERT INTO user (username, address, phoneno, postid) VALUES {receiver_username, receiver_address, phoneno, postal}")
            mysql.connection.commit()
        cursor.execute(f"SELECT userid FROM user WHERE username = '{receiver_username}'")
        receiver_info = cursor.fetchone()
        sender_id = sender_info['userid']
        receiver_id = receiver_info['userid']
        cursor.execute(f"SELECT postid FROM user WHERE username = '{sender_username}'")
        senderpost = cursor.fetchone()
        senderpostid = senderpost['postid']
        cursor.execute(f"INSERT INTO parcel (senderid, receiverid, contenttype, status, senderpostid, recieverpostid) VALUES{sender_id, receiver_id, content, 'in transit', senderpostid, postal}")
        mysql.connection.commit()
        cursor.execute(f"SELECT parcelid FROM parcel ORDER BY parcelid DESC LIMIT 1;") #last row of the parcel table
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
        if postid == 1:
            cursor.execute(f"SELECT * FROM parcel WHERE status = 'Left for post:1' or senderpostid = {postid} or recieverpostid={postid}")
        else:
            cursor.execute(f"SELECT * FROM parcel WHERE senderpostid = {postid} or recieverpostid={postid}")
        
        parall = cursor.fetchall()
        if parall:
            for i in parall:
                parid = i['parcelid']
                stat  = i['status']
                res = delay_status(parid)
                if res:
                    if stat == 'Left for post:1' and postid == 1:
                        cursor.execute(f"UPDATE parcel SET status = 'Acquired at post:{postid}' WHERE parcelid ={parid}")
                    elif stat == 'in transit':
                        cursor.execute(f"UPDATE parcel SET status = 'Acquired at post:{postid}' WHERE parcelid ={parid}")
                    else:
                        cursor.execute(f"UPDATE parcel SET status = 'Acquired at post:{postid}' WHERE parcelid ={parid} and status LIKE 'Left for post:{postid}'")
                    mysql.connection.commit()
                    tim = change_status(parid)
                    if tim:
                        cursor.execute(f"UPDATE parcel SET status = 'Parcel returned' WHERE parcelid ={parid} and status ='Out for delivery'")
                        mysql.connection.commit()
                cursor.execute(f"SELECT * FROM parcel WHERE status='Acquired at post:{postid}' or status = 'Parcel returned'")
                parcels = cursor.fetchall()
            return jsonify({"Parcel": parcels}) if parcels else jsonify({"message": "No parcels acquired"}), 404
        else:
            return jsonify({"message":"NO parcels at the moment"})
    else:
        return jsonify({"message": "Invalid request method"}), 405

@app.route("/sendpost", methods=["POST", "GET"])
def sendpost():
    if request.method == "POST" and 'postid' in request.json:
        postid = request.json["postid"]
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if postid == 1:
            cursor.execute(f"SELECT * FROM parcel WHERE status = 'Acquired at post:1' or senderpostid = {postid} or recieverpostid={postid}")
        else:
            cursor.execute(f"SELECT * FROM parcel WHERE senderpostid = {postid} or recieverpostid={postid}")          
        parall = cursor.fetchall()
        if parall:
            for i in parall:
                parid = i['parcelid']
                recpostid = i['recieverpostid']
                res = delay_status(parid)
                if res:
                    if postid == recpostid:
                        cursor.execute(f"UPDATE parcel SET status = 'Out for delivery' WHERE parcelid ={parid} and status ='Acquired at post:{postid}'")
                    elif postid == 1:
                        cursor.execute(f"UPDATE parcel SET status = 'Left for post:{recpostid}' WHERE parcelid ={parid} and status ='Acquired at post:1'")
                    else:
                        cursor.execute(f"UPDATE parcel SET status = 'Left for post:1' WHERE parcelid ={parid} and status ='Acquired at post:{postid}'")
                    mysql.connection.commit()
                    
                cursor.execute(f"SELECT * FROM parcel WHERE parcelid = {parid} and status = 'Out for delivery' or status LIKE 'Left for post%'")
            parcels = cursor.fetchall()
            return jsonify({"Parcel": parcels}) if parcels else jsonify({"message": "No parcels at moment"}), 404
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
                recid = i['parcelid']
                cursor.execute(f"UPDATE parcel SET status = 'Delivered' WHERE parcelid ={recid} and status = 'Out for delivery'")
                mysql.connection.commit()
            cursor.execute(f"SELECT * FROM parcel WHERE status='Delivered' and receiverid={ui}")
            parcels = cursor.fetchall()
            return jsonify({"Parcel": parcels}) if parcels else jsonify({"message": "No parcels delivered"}), 404    
        else:
            return jsonify({"message": "No parcels found for this user"})
    else:
        return jsonify({"message": "User ID not found"})

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

    