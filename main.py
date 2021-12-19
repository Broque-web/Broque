#------------------------------------------------------
# MODULES IMPORTS
from re import X
import string
import random
import os
from datetime import datetime, timezone
from enum import unique
import hashlib
from flask import Flask, render_template, url_for, request, flash, redirect, session, jsonify, make_response
from flask_cors.decorator import cross_origin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref, defaultload
import json
from flask.sessions import SecureCookieSessionInterface
from werkzeug.datastructures import Headers
from flask_cors import CORS, cross_origin

#------------------------------------------------------
#NECESSARY CONFIGURATIONS

app = Flask(__name__)
app.config["SECRET_KEY"] = "b423653a944928b2e59984be767eefa5"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///broke.db"
app.config['CORS_HEADERS'] = 'Content-Type'
db = SQLAlchemy(app)
CORS(app)
session_cookie = SecureCookieSessionInterface().get_signing_serializer(app)

#------------------------------------------------------
#DATABASE MODELS

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    country = db.Column(db.Integer)
    gender = db.Column(db.String())
    verified = db.Column(db.String(3), nullable=False, default="no")
    image = db.Column(db.String(20), nullable=False, default="default.png")

    def __repr__(self):
        return f"User('{self.username}', '{self.id}', '{self.image}')"


class Slip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    bookmaker = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(10))
    price = db.Column(db.String(10))
    description = db.Column(db.String())
    slip_owner = db.Column(db.Integer)
    matches = db.Column(db.String(3))
    odds = db.Column(db.String())
    slip_ref = db.Column(db.String(10))
    likes = db.Column(db.Integer, default=0)
    bkl = db.Column(db.String())
    date = db.Column(db.String(), default=datetime.utcnow().strftime("%d %b, %Y"))

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ref  = db.Column(db.String(10))
    content = db.Column(db.String())
    title = db.Column(db.String())
    blog_owner = db.Column(db.Integer)
    blog_quote = db.Column(db.String(10))
    date = db.Column(db.String(), default=datetime.utcnow().strftime("%d %b, %Y"))

class SlipComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(210))
    commenter = db.Column(db.Integer)
    slip_id = db.Column(db.Integer)
    commenter_name = db.Column(db.String())

class SlipLikes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Liker = db.Column(db.Integer)
    slip_id = db.Column(db.Integer)
    like = db.Column(db.Integer)
#------------------------------------------------------
#OTHER CONFIGURATIONS
if os.path.exists("./broke.db"):
    pass
else:
    db.create_all()

#------------------------------------------------------
#OTHER USEFUL FUNCTIONS
def generate_link(bookmaker, code):
    link = ''
    if bookmaker.lower() == "sportybet":
        link = f'https://sportybet.com/?shareCode={code}'

    elif bookmaker.lower() == '1xbet':
        link = f'http://www.betway.com/bookabet/{code}'
    elif bookmaker.lower() == 'betway':
        link = ''
    return  link
def add_session(username):
    if 'username' in session:
        pass
    else:
        session['username'] = username

def hash(password):
    hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hash
def delete_session():
    session.pop("username", None)

def is_logged_in():
    if 'username' in session:
        return True
    else:
        return False


def generate_ref(size):
    chars = string.ascii_uppercase + string.digits
    ref = ''.join(random.choice(chars) for _ in range(size))
    slip = Slip.query.filter_by(slip_ref=ref).first()
    if slip is not None:
        generate_ref()
    return ref


#------------------------------------------------------
#ROUTES

@app.route("/")
def home():
    home_slips = Slip.query.all()[0:8]
    blogs = Blog.query.all()[0:3]
    return render_template("index.html", home_slips=home_slips, blogs=blogs)

@app.route("/about")
def about():
    return render_template("about.html")
    
@app.route("/blog-sub", methods=["POST", "GET"])
def blogSub():
    if not is_logged_in():
        flash("Please login first", "danger")
        return redirect(url_for("signin"))
    elif request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        quote = request.form["quote"]
        id = User.query.filter_by(username=session['username']).first().id
        blog = Blog(content=content, title=title, blog_owner=id, blog_quote=quote, ref=generate_ref(12))
        db.session.add(blog)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("blog-sub.html")

@app.route("/signup", methods=["POST", "GET"])
def signup():
    if is_logged_in():
        return redirect(url_for("home"))
    elif request.method == "POST":
        firstname = request.form["firstname"]
        lastname = request.form["lastname"]
        username = request.form["username"]
        country = request.form["country"]
        gender = request.form["gender"]
        password = hash(request.form["password"])
        v_password = hash(request.form["v_password"])
        user = User.query.filter_by(username=username).all()
        if user != []:
            flash("Username already exist", "danger")
        elif password != v_password:
            flash("Passwords do not match", "danger")
        else:
            new_user = User(firstname=firstname, lastname=lastname, username=username, password=password, country=country, gender=gender)
            db.session.add(new_user)
            db.session.commit()
            flash("Now Sign in", "info")
            return redirect(url_for("signin"))
        return render_template("signup.html")
    return render_template("signup.html")



@app.route("/signin", methods=["POST", "GET"])
def signin():
    if is_logged_in():
        return redirect(url_for("home"))
    elif request.method == "POST":
        username = request.form["username"]
        password = hash(request.form["password"])
        user = User.query.filter_by(username=username).first()
        if user == None:
            flash("Username does not exist", "danger")
        elif password != user.password:
            flash("Incorrerct password", "danger")
        elif username == "" or password == "":
            flash("No field should be left blank")
        else:
            add_session(username)
            return redirect(url_for("home"))
        return render_template("signin.html")
    return render_template("signin.html")

@app.route("/phishing")
def phishing():
    return render_template("slips.html")
    
@app.route("/logout")
def logout():
    delete_session()
    return redirect(url_for("signin"))



@app.route("/slips")
def slips():
    query = request.args.get('query')
    if query is None:
        slips = Slip.query.all()[0:12]
    else:
        i = int(query) * 12
        x = (int(query) + 1) * 2
        slips = Slip.query.all()[i:x]
    return render_template("slips.html", slips=slips)


@app.route('/dashboard')
def cart():
    return render_template('dashboard.html')



@app.route("/submission", methods=["POST", "GET"])
def submission():
    if not is_logged_in():
        flash("Please login first", "danger")
        return redirect(url_for("signin"))
    elif request.method == "POST":
        code = request.form["code"]
        time = request.form["time"]
        bookmaker = request.form["bookmaker"]
        price = request.form["price"]
        description = request.form["description"]
        matches = request.form['matches']
        odds = request.form['odds']
        slip_ref = generate_ref(10)
        id = User.query.filter_by(username=session['username']).first().id
        es = Slip.query.filter_by(code=code).first()
        link = generate_link(bookmaker, code)
        if es is not None:
            flash("Oops! Bet code already exists", "danger")
            return redirect(url_for("submission"))
        new_slip = Slip(bkl=link, code=code, odds=odds, time=time, bookmaker=bookmaker, price=price, description=description, slip_ref=slip_ref, slip_owner=id, matches=matches)
        db.session.add(new_slip)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template('submission.html')

@app.route("/detail",  methods=["POST", "GET"])
def detail():
    ref = request.args.get('ref')
    if not is_logged_in():
        flash("Please login first", "danger")
        return redirect(url_for("signin"))
    elif ref == None:
        return redirect(url_for("home"))
    elif Slip.query.filter_by(slip_ref=ref).first() == None:
        return redirect(url_for("home"))
    slip = Slip.query.filter_by(slip_ref=ref).first()
    owner = User.query.filter_by(id=slip.slip_owner).first()
    name = owner.firstname + " " + owner.lastname
    comments = SlipComment.query.filter_by(slip_id=slip.id)
    addt_slips = Slip.query.all()[0:4]
    return render_template("slip-detail.html", slip=slip, name=name, comments=comments, noc=len(comments.all()), addt_slips=addt_slips)

@app.route("/blog-detail",  methods=["POST", "GET"])
def blogDetail():
    ref = request.args.get('ref')
    if ref == None:
        return redirect(url_for("home"))
    elif Blog.query.filter_by(ref=ref).first() == None:
        return redirect(url_for("home"))
    blog = Blog.query.filter_by(ref=ref).first()
    owner = User.query.filter_by(id=blog.blog_owner).first()
    name = owner.firstname + " " + owner.lastname
    #comments = SlipComment.query.filter_by(slip_id=slip.id)
    return render_template("blog-details.html", blog=blog, owner=owner)

@app.route('/getcomments',  methods=["GET"])
def getComments():
    jsons = {'comments':[]}
    ref = request.args.get("ref")
    id = Slip.query.filter_by(slip_ref=ref).first().id
    comments = SlipComment.query.filter_by(slip_id=id).all()
    for comment in comments:
        x = {
            'comment':comment.comment, 
            'name': comment.commenter_name
            }
        jsons['comments'].append(x)
    ress = jsonify(jsons)
    #ress.headers.add('Access-Control-Allow-Origin', "*")
    res = make_response(ress, 200)
    return res



@app.route("/addcomments", methods=["POST"])
def addCommentS():
    if not is_logged_in():
        flash("Please login first", "danger")
        return make_response(jsonify({'url': url_for('signin')}), 201)
    else:
        req = request.get_json()
        comment = req['comment']
        ref = req['ref']
        slip = Slip.query.filter_by(slip_ref=ref).first()
        user = User.query.filter_by(username=session['username']).first()
        commenter_name = user.firstname + " " + user.lastname
        newComment = SlipComment(comment=comment, commenter=user.id, slip_id=slip.id, commenter_name=commenter_name)
        db.session.add(newComment)
        db.session.commit() 
        ress = jsonify({'message': 'OK'})
        #ress.headers.add('Access-Control-Allow-Origin', "*")
        res = make_response(ress, 200)
        return res


@app.route("/addlike", methods=["POST"])
def addLikes():
    if not is_logged_in():
        flash("Please login first", "danger")
        return make_response(jsonify({'url': url_for('signin')}), 201)
    else:
        flag = False
        req = request.get_json()
        likeq = req['like']
        ref = req['ref']
        slip = Slip.query.filter_by(slip_ref=ref).first()
        user = User.query.filter_by(username=session['username']).first()
        userlike = SlipLikes.query.filter_by(slip_id=slip.id).all()
        for like in userlike:
            if like.Liker == user.id:
                flag = True
        ress = jsonify({'message': 'OK'})
        res = make_response(ress, 200)
        #ress.headers.add('Access-Control-Allow-Origin', "*")
        if not flag:
            like = SlipLikes(slip_id=slip.id, Liker=user.id, like=likeq)
            db.session.add(like)
            slip.likes += int(likeq)
            db.session.commit()
            return res
        else:
            return res

@app.route("/settings")
def settings():
    if not is_logged_in():
        flash("Please login first", "danger")
        return redirect(url_for("signin"))
    profile = User.query.filter_by(username=session['username']).first()
    return render_template("settings.html", profile=profile)
#---------------------------------------------------
#RUNNING APP
if __name__ == "__main__":
    app.run(debug=True)
