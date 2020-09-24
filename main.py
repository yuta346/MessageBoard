from flask import Flask, render_template, request, session, url_for, redirect, flash, logging
import os,  requests
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt


app = Flask(__name__)                     #create a flask object

#config mysql
app.config["MYSQL_HOST"]='localhost'
app.config["MYSQL_USER"]='yuta'
app.config["MYSQL_PASSWORD"]='ricefam'
app.config["MYSQL_DB"]='msgboardapp'
app.config["MYSQL_CURSORCLASS"]='DictCursor'

#initialize mysql
mysql = MySQL(app)

#homepage route
@app.route("/top", methods=["GET"])
def top():
    if request.method == "POST":
        return redirect(url_for("signup"))
    return render_template("top.html", title="Top page")

#send top route
@app.route("/", methods=["GET"])
def send_top():                            #changed send login to send home
  if not session.get("USERNAME") is None:  #if username is in the session, redirect to home
    return redirect("/home")
  return redirect(url_for("top"))

#home page route
@app.route("/home")
def home():
    if not session.get("USERNAME") is None:
        return render_template("home.html", title="Home")
    return redirect(url_for("top"))


#signup route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        req = request.form
        username = str(req.get("username"))
        email = str(req.get("email"))
        # username = str(req.get("username"))
        # password = str(req.get("password"))
        password = sha256_crypt.encrypt(str(req.get("password")))
        

        print(username, email, password)
        session["USERNAME"] = username      #set username to the session
        session['EMAIL'] = email            #set email to the session

     #create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users(username, email,  password) VALUES (%s, %s, %s)", (username,  email,  password))

        #commit to db

        mysql.connection.commit()

        #close connection
        cur.close()

        flash("Sign up successful!")
        return redirect(url_for("home"))     #redirect to home after sign up
    return render_template("signup.html", title="Sign up")


#sign in route
@app.route("/signin", methods=["GET", "POST"])
def signin():   
    if request.method == "POST":
        req = request.form
        username = req.get('username')
        password_candidate = req.get('password')        #get the password from the user

        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM users WHERE username =%s", [username])

        if result > 0:
            data = cur.fetchone()
            password = data["password"]

            if sha256_crypt.verify(password_candidate, password):
                session["logged_in"]= True
                session['USERNAME'] = username
                flash("Login Successful!" )
                return redirect(url_for('home'))  #redirect to home after signing in
        else:
            return render_template('signin.html', message = "Invalid credential, please try again" , title="Sign in")
        cur.close()
    else:
        return render_template('signin.html', title="Sign in")

#sign out route
#pre: user already signed in
#post: clear the cookie and redirect to top
@app.route("/signout", methods=["GET"])
def signout():
    
    session.clear()
    flash("You have been logged out!", "info")
    print("signed out")
    return redirect(url_for("send_top"))


#message board route
#pre:user is signed in
#post: display messages 
@app.route("/msgboard", methods=["GET"])
def msgboard():
    if not session.get("USERNAME") is None:    #if username is in the session, redirect to top 
        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM messages")
        
        messages = cur.fetchall()

        if result>0:
            return render_template('msgboard.html', messages = messages, title="Message Board")
        else:
            flash("No massages to display.")
            return redirect(url_for("home"))
        
    return redirect(url_for("top"))


#add message route
#user is signed in
#get the user inputs and store the to the database
@app.route("/addmsg", methods=["GET", "POST"])
def addmsg():
    if request.method == "POST":
        if session.get("USERNAME"): 
            req = request.form
            username = session["USERNAME"]
            message = str(req.get("message"))
            cur  = mysql.connection.cursor()
            cur.execute("INSERT INTO messages(author, body) VALUES(%s, %s)", (username, message))
            mysql.connection.commit()
            cur.close()
        return redirect(url_for("msgboard"))
    return render_template("addmsg.html", title="Add Message")


#edit message, show the window for editing
@app.route("/edit_message/<string:id>", methods=["GET", "POST"])
def edit_message(id):
    # Create cursor
    cur = mysql.connection.cursor()
    # Get article by id
    cur.execute("SELECT * FROM messages WHERE id = %s", [id])
    message = cur.fetchone()
    body = message["body"]
    cur.close()

    if request.method == "POST":
        req = request.form
        body = str(req.get("message"))
        cur = mysql.connection.cursor()
        cur.execute ("UPDATE messages SET body=%s WHERE id=%s",(body, id))
        mysql.connection.commit()
        cur.close()
        print("hello and hi")
        return redirect(url_for('msgboard'))
    return render_template("edit_message.html", message = body)

#delete message
@app.route("/delete_message/<string:id>", methods = ["POST"])
def delete_message(id):
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM messages WHERE id=%s", [id])


    mysql.connection.commit()

    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('home'))


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                 endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

if __name__ == "__main__":
    app.config['SECRET_KEY'] = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT' #set the secret key
    app.run(debug="True")