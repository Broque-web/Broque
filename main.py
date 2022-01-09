# ------------------------------------------------------
# MODULES IMPORTS
from re import X
import re
import string
import random
import os
import time
import json
from datetime import datetime
from enum import unique
import hashlib
from flask import Flask, render_template, url_for, request, flash, redirect, session, jsonify, make_response
from flask_cors.decorator import cross_origin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref, defaultload
from flask.sessions import SecureCookieSessionInterface
from werkzeug.datastructures import Headers
from werkzeug.utils import secure_filename
from flask_cors import CORS, cross_origin
from static.src.Currency_converter.pycurrency import Currency_Converter
from flask_mail import Mail, Message

# ------------------------------------------------------
# NECESSARY CONFIGURATIONS
app = Flask(__name__)
app.config["SECRET_KEY"] = "b423653a944928b2e59984be767eefa5"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///broke.db"
app.config['CORS_HEADERS'] = 'Content-Type'
app.config["UPLOAD_FOLDER"] = "static/images/slip_images/"
app.config["MAIL_SERVER"] = "smtp.googlemail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "tonygh2019@gmail.com"
app.config["MAIL_PASSWORD"] = "tony6660"

allowed_extensions = {'jpg', 'png', 'jpeg'}
db = SQLAlchemy(app)
CORS(app)
mail = Mail(app)
session_cookie = SecureCookieSessionInterface().get_signing_serializer(app)


# ------------------------------------------------------
# DATABASE MODELS

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    country = db.Column(db.Integer)
    gender = db.Column(db.String())
    referral_ref = db.Column(db.String())
    balance = db.Column(db.Float)
    is_verified = db.Column(db.Boolean, default=False)
    image = db.Column(db.String(20), nullable=False, default="default.png")
    email = db.Column(db.String(), default="")
    bio = db.Column(db.String(), default="")
    DOB = db.Column(db.String(), default="")
    phone = db.Column(db.String(), default="")

    def __repr__(self):
        return f"User('{self.username}', '{self.id}', '{self.image}')"


class Slip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    bookmaker = db.Column(db.String(20), nullable=False)
    time = db.Column(db.DateTime)
    price = db.Column(db.String(10))
    description = db.Column(db.String())
    slip_owner = db.Column(db.Integer)
    matches = db.Column(db.String(3))
    odds = db.Column(db.String())
    slip_ref = db.Column(db.String(10))
    likes = db.Column(db.Integer, default=0)
    bkl = db.Column(db.String())
    image = db.Column(db.String())
    date = db.Column(
        db.String(), default=datetime.utcnow().strftime("%d %b, %Y"))
    expired = db.Column(db.String(), default="Not expired")


class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ref = db.Column(db.String(10))
    content = db.Column(db.String())
    title = db.Column(db.String())
    blog_owner = db.Column(db.Integer)
    blog_quote = db.Column(db.String(10))
    date = db.Column(
        db.String(), default=datetime.utcnow().strftime("%d %b, %Y"))


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

class email_tokens(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    token = db.Column(db.String(20))
    is_used = db.Column(db.Boolean, default=False)

# ------------------------------------------------------
# OTHER CONFIGURATIONS
if os.path.exists("./broke.db"):
    pass
else:
    db.create_all()

# ------------------------------------------------------
# OTHER USEFUL FUNCTIONS


def get_con_balance(country):
    try:
        if country == 'Ghana':
            return float(Currency_Converter().convert("USD", "GHS", 0.1)['result'].split(" ")[1])
        elif country == 'Nigeria':
            return float(Currency_Converter().convert("USD", "NGN", 0.1)['result'].split(" ")[1])
        elif country == 'Kenya':
            return float(Currency_Converter().convert("USD", "KES", 0.1)['result'].split(" ")[1])
        else:
            return 0.00
    except:
        return 0.0


def generate_link(bookmaker, code):
    link = ''
    if bookmaker.lower() == "sportybet":
        link = f'https://sportybet.com/?shareCode={code}'

    elif bookmaker.lower() == '1xbet':
        link = ''
    elif bookmaker.lower() == 'betway':
        link = f'http://www.betway.com/bookabet/{code}'
    return link


def add_session(username):
    if 'username' in session:
        pass
    else:
        session['username'] = username


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions


def expired():
    slips = Slip.query.all()
    for slip in slips:
        i_time = slip.time
        f_time = datetime.now().replace(microsecond=0, second=0)
        time = i_time - f_time
        if str(time).startswith("-"):
            slip.expired = "Expired"
        elif int(str(time).split(":")[0]) == 0 and int(str(time).split(":")[1]) <= 2:
            slip.expired = "Expired"
        else:
            slip.expired = "Not expired"
    db.session.commit()


def get_currency(country):
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(THIS_FOLDER, "static/src/c_code.json")) as f:
        c_code = json.load(f)

    with open(os.path.join(THIS_FOLDER, "static/src/c_udt.json")) as f:
        c_udt = json.load(f)

    code = ""
    for countries in c_udt:
        if countries["name"] == country:
            code = countries["code"]
            break

    currency = ""
    for codes in c_code:
        if codes["country"] == code:
            currency = codes["currency"]
            break
    # print(code)
    return currency


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


# ------------------------------------------------------
# ROUTES
@app.before_request
def before_request():
    expired()
    if 'currency' in session and 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        session['balance'] = format(user.balance, '.2f')
        session['image'] = user.image
    else:
        session['currency'] = "USD"


@app.route("/")
def home():
    home_slips = Slip.query.filter_by(expired="Not expired").all()[0:7]
    blogs = Blog.query.all()[0:2]
    if request.args.get('ref'):
        print(request.args.get('ref'))
        session['ref'] = request.args.get('ref')
        return redirect(url_for('home'))
    return render_template("index.html", home_slips=home_slips, blogs=blogs)


@app.route("/referral")
def referral():
    if not is_logged_in():
        flash("Please login first", "warning")
        session['redirect'] = request.url
        return redirect(url_for("signin"))
    user = User.query.filter_by(username=session['username']).first()
    try:
        ref_people = int((User.query.filter_by(username=session['username']).first(
        ).balance / get_con_balance(User.query.filter_by(username=session['username']).first().country)) - 1)
    except:
        ref_people = "-"
    return render_template("referral.html", ref=request.root_url+'?ref='+user.referral_ref, ref_people=ref_people)


@app.route("/about")
def about():
    users = len(User.query.all())
    slips = len(Slip.query.filter_by(expired="Not expired").all())
    return render_template("about.html", users=users, slips=slips)


@app.route("/blog-sub", methods=["POST", "GET"])
def blogSub():
    if not is_logged_in():
        flash("Please login first", "warning")
        session['redirect'] = request.url
        return redirect(url_for("signin"))
    elif request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        quote = request.form["quote"]
        id = User.query.filter_by(username=session['username']).first().id
        blog = Blog(content=content, title=title, blog_owner=id,
                    blog_quote=quote, ref=generate_ref(12))
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
        balance = get_con_balance(country)
        referral_ref = generate_ref(12)
        user = User.query.filter_by(username=username).all()
        if user != []:
            flash("Username already exist", "warning")
        elif password != v_password:
            flash("Passwords do not match", "warning")
        else:
            if 'ref' in session:
                User.query.filter_by(referral_ref=session['ref']).first(
                ).balance += get_con_balance(User.query.filter_by(referral_ref=session['ref']).first().country)
            new_user = User(balance=balance, firstname=firstname, lastname=lastname, username=username,
                            password=password, country=country, gender=gender, referral_ref=referral_ref)
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
            flash("Username does not exist", "warning")
        elif password != user.password:
            flash("Incorrerct password", "warning")
        elif username == "" or password == "":
            flash("No field should be left blank")
        else:
            add_session(username)
            session['currency'] = get_currency(user.country)
            if 'redirect' in session:
                redirect_lk = session['redirect']
                session.pop('redirect', None)
                return redirect(redirect_lk)
            return redirect(url_for("home"))
        return render_template("signin.html")
    return render_template("signin.html")


@app.route("/logout")
def logout():
    delete_session()
    return redirect(url_for("signin"))


@app.route("/slips")
def slips():
    query = request.args.get('query')
    if query is None:
        slips = Slip.query.filter_by(expired="Not expired").all()[0:11]
    else:
        i = int(query) * 12
        x = (int(query) + 1) * 2
        slips = Slip.query.filter_by(expired="Not expired").all()[i:x]
    return render_template("slips.html", slips=slips)


@app.route('/dashboard')
def cart():
    return render_template('dashboard.html')


@app.route("/submission", methods=["POST", "GET"])
def submission():
    if not is_logged_in():
        flash("Please login first", "warning")
        session['redirect'] = request.url
        return redirect(url_for("signin"))
    elif request.method == "POST":
        code = request.form["code"]
        time = datetime.strptime(
            f"{datetime.now().date()} {request.form['time']}", "%Y-%m-%d %H:%M")
        bookmaker = request.form["bookmaker"]
        image = request.files['image']
        #price = request.form["price"]
        price = "0.00"
        description = request.form["description"]
        matches = request.form['matches']
        odds = request.form['odds']
        slip_ref = generate_ref(10)
        id = User.query.filter_by(username=session['username']).first().id
        es = Slip.query.filter_by(code=code).first()
        link = generate_link(bookmaker, code)
        if es is not None:
            flash("Oops! Bet code already exists", "warning")
            return redirect(url_for("submission"))
        elif (image and allowed_file(image.filename)) == False:
            flash("Oops! File type not supported.", "warning")
            return redirect(url_for("submission"))
        filename = secure_filename(
            bookmaker.lower()+"_"+generate_ref(6)+".png")
        image.save(os.path.join(os.path.dirname(os.path.abspath(__file__)) ,app.config['UPLOAD_FOLDER']+filename))
        new_slip = Slip(image=filename, bkl=link, code=code, odds=odds, time=time, bookmaker=bookmaker,
                        price=price, description=description, slip_ref=slip_ref, slip_owner=id, matches=matches)
        db.session.add(new_slip)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template('submission.html')


@app.route("/detail",  methods=["POST", "GET"])
def detail():
    ref = request.args.get('ref')
    if not is_logged_in():
        flash("Please login first", "warning")
        session['redirect'] = request.url
        return redirect(url_for("signin"))
    elif ref == None:
        return redirect(url_for("home"))
    elif Slip.query.filter_by(slip_ref=ref).first() == None:
        return redirect(url_for("home"))
    elif Slip.query.filter_by(slip_ref=ref).first().expired == "Expired":
        return redirect(url_for("home"))
    slip = Slip.query.filter_by(slip_ref=ref).first()
    owner = User.query.filter_by(id=slip.slip_owner).first()
    name = owner.firstname + " " + owner.lastname
    comments = SlipComment.query.filter_by(slip_id=slip.id)
    addt_slips = Slip.query.filter_by(expired="Not expired").all()[0:3]
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
    jsons = {'comments': []}
    ref = request.args.get("ref")
    id = Slip.query.filter_by(slip_ref=ref).first().id
    comments = SlipComment.query.filter_by(slip_id=id).all()
    for comment in comments:
        x = {
            'comment': comment.comment,
            'name': comment.commenter_name
        }
        jsons['comments'].append(x)
    ress = jsonify(jsons)
    #ress.headers.add('Access-Control-Allow-Origin', "*")
    res = make_response(ress, 200)
    return res


@app.route("/addcomments", methods=["POST"])
def addCommentS():
    req = request.get_json()
    if not is_logged_in():
        flash("Please login first", "warning")
        session['redirect'] = "http://127.0.0.1:5000/detail?ref="+req['ref']
        return make_response(jsonify({'url': url_for('signin')}), 201)
    else:
        comment = req['comment']
        ref = req['ref']
        slip = Slip.query.filter_by(slip_ref=ref).first()
        user = User.query.filter_by(username=session['username']).first()
        commenter_name = user.firstname + " " + user.lastname
        newComment = SlipComment(
            comment=comment, commenter=user.id, slip_id=slip.id, commenter_name=commenter_name)
        db.session.add(newComment)
        db.session.commit()
        ress = jsonify({'message': 'OK'})
        #ress.headers.add('Access-Control-Allow-Origin', "*")
        res = make_response(ress, 200)
        return res


@app.route("/addlike", methods=["POST"])
def addLikes():
    req = request.get_json()
    if not is_logged_in():
        flash("Please login first", "warning")
        session['redirect'] = "http://127.0.0.1:5000/detail?ref="+req['ref']
        return make_response(jsonify({'url': url_for('signin')}), 201)
    else:
        flag = False
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


@app.route("/settings", methods=['POST', 'GET'])
def settings():
    message = ""
    if not is_logged_in():
        flash("Please login first", "warning")
        session['redirect'] = request.url
        return redirect(url_for("signin"))
    elif request.method == "POST":
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        bio = request.form['bio']
        birthdate = request.form['birthdate']
        phone = request.form['phone']

        user = User.query.filter_by(username=session['username']).first()
        user.firstname = firstname
        user.lastname = lastname
        user.DOB = birthdate
        user.phone = phone
        user.bio = bio
        image = request.files['image']

        if email != "":
            emails = User.query.filter_by(email=email).first()
            if emails:
                if emails.id == user.id:
                    user.email = email
                else:
                    flash("Email has already been used by another account. Try a new one.", "warning")
                    return redirect(url_for("settings"))
            else:
                 user.email = email
        if image.filename == '':
            pass
        elif (image and allowed_file(image.filename)) == False:
            flash("File type not supported.", "warning")
            return redirect(url_for("settings"))
        else:
            filename = secure_filename(user.username.lower(
            )+"_"+generate_ref(20)+"."+image.filename.split(".")[-1].lower())
            image.save(os.path.join(os.path.dirname(os.path.abspath(__file__)),"static/images/profiles/"+filename))
            user.image = filename

        password = request.form['password']
        new_password = request.form['new_password']
        verify_new_password = request.form['verify_new_password']

        if password == '' and (new_password != '' or verify_new_password != ''):
            profile = User.query.filter_by(
                username=session['username']).first()
            message = "Please enter your current password before."
        elif password != '' and (new_password == '' or verify_new_password == ''):
            profile = User.query.filter_by(
                username=session['username']).first()
            message = "Please enter new password."
        elif password != '' and new_password != '' or verify_new_password != '':
            if hash(password) != user.password:
                profile = User.query.filter_by(
                    username=session['username']).first()
                message = "You entered an incorrect password."
            elif verify_new_password != new_password:
                profile = User.query.filter_by(
                    username=session['username']).first()
                message = "New password does not match."
            else:
                user.password = hash(new_password)

    db.session.commit()
    if message != '':
        flash(message, "warning")
    profile = User.query.filter_by(username=session['username']).first()
    return render_template("settings.html", profile=profile)

@app.route("/send-email")
def send_email():
    if not is_logged_in():
        flash("Please login first", "warning")
        session['redirect'] = request.url
        return redirect(url_for("signin"))
    user = User.query.filter_by(
                username=session['username']).first()
    if user.email == "":
        flash("You have not added an email to your account yet, please add one and try again", "warning")
        return redirect(url_for("settings"))
    else:
        token = generate_ref(20)
        new_token = email_tokens(user_id=user.id, token=token)
        db.session.add(new_token)
        db.session.commit()
        msg = Message("Broque.com email confirmation", 
        sender=("Broque.com", "noreply@broque.com"), 
        recipients=[user.email])
        msg.html = render_template("email_confirmation.html", token=token)
        try:
            mail.send(msg)
            flash(f"A confirmation email has been sent to {user.email}. Open and follow the instructions given", "success")
            return redirect(url_for("settings"))
        except Exception as e:
            print(e)
            flash(f"There was an error sending email to {user.email}", "warning")
            return redirect(url_for("settings"))
    

@app.route("/email-confirm/<token>", methods=['POST', 'GET'])
def email_confirm(token):
    tokens = email_tokens.query.filter_by(token=token).first()
    
    if not tokens or tokens.is_used:
        delete_session()
        flash("There was an error confirming your email. Please sign in and try again.", "danger")
        return redirect(url_for("signin"))
    else:
        user = User.query.filter_by(
                id=tokens.user_id).first()
        if user.is_verified:
            flash("Your email has already been verified. Please sign in.", "success")
            return redirect(url_for("signin"))
        user.is_verified = True
        tokens.is_used = True
        db.session.commit()
        delete_session()
        flash("Your email has been confirmed. Please sign in.", "success")
        return redirect(url_for("signin"))
        

# ---------------------------------------------------
# RUNNING APP
if __name__ == "__main__":
    app.run(debug=True)
