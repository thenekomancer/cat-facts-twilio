from flask import Flask, request, redirect, render_template, session, flash
from jinja2 import StrictUndefined
from model import connect_to_db, db, User, Cat
from helper_functions import *
from pytz import timezone
import pytz
import random
import bcrypt
import os
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
# Your Account SID from twilio.com/console
account_sid = os.environ.get("account_sid")
# Your Auth Token from twilio.com/console
auth_token = os.environ.get("auth_token")
client = Client(account_sid, auth_token)
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
################################################################################

@app.route("/")
def main():
    """Render main page"""

    return render_template("home.html")


@app.route("/login", methods=["POST"])
def login():
    """Attempt to log the user in"""

    email = request.form.get("email")
    password = request.form.get("password")
    password = password.encode('utf-8')

    hashed = bcrypt.hashpw(password, bcrypt.gensalt())

    existing_email = User.query.filter_by(email=email).first()

    if existing_email is not None and bcrypt.checkpw(password, hashed):
        # add user to session
        session["user_id"] = existing_email.user_id
        user_id = session["user_id"]

        flash("Successfully logged in!")

        cat = Cat.query.filter_by(user_id=user_id).first()

        # TODO this is dupe code from main route, factor out
        cat.dinner_time = cat.dinner_time.replace(tzinfo=pytz.utc)
        # TODO get user's local time instead of hardcoding PST
        cat.dinner_time = cat.dinner_time.astimezone(timezone('US/Pacific'))

        time = [str(cat.dinner_time.hour), ":", str(cat.dinner_time.minute)]
        time = parse_time("".join(time))
        hour, minutes = time

        ampm = am_or_pm(hour) # get whether am or pm
        hour = make_12_hour_time(hour) # convert to 12 hour time

        cat.dinner_time = cat.dinner_time.replace(hour=hour)


        return render_template("main.html", name=cat.name, toy1=cat.toy1, 
                                            toy2=cat.toy2, snack=cat.snack, 
                                            activity1=cat.activity1,
                                            activity2=cat.activity2, 
                                            dinner_time=cat.dinner_time,
                                            ampm=ampm)

    elif existing_email is None:
        flash("Incorrect email.")
        return redirect('/')
    else:
        flash("Incorrect password.")
        return redirect('/')

@app.route("/logout")
def do_logout():
    """Log user out."""

    flash("Goodbye!")
    session["user_id"] = ""

    return redirect("/")

@app.route("/register", methods=["GET"])
def register():
    """Show registration form"""

    return render_template("register.html")

@app.route("/register", methods=["GET", "POST"])
def register_process():
    """Get information from registration form."""

    email = request.form.get("email")

    password = request.form.get("password")
    password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    phone = request.form.get("phone")
    country_code = '+1'
    phone = ''.join(num for num in phone if num not in '-')
    phone = country_code + phone

    name = request.form.get('cat-name')
    dinner_time = request.form.get('dinner-time')
    ampm = request.form.get('ampm')

    time = parse_time(dinner_time)
    hour = time[0]
    minutes = time[1]
    hour = make_24_hour_time(ampm, hour)
    date = convert_to_utc(hour, minutes)

    snack = request.form.get('cat-snack')
    activity1 = request.form.get('cat-activity')
    activity2 = request.form.get('cat-activity2')
    toy1 = request.form.get('cat-toy')
    toy2 = request.form.get('cat-toy2')

    existing_email = User.query.filter_by(email=email).first()

    # check if the email is in use
    if existing_email is None:
        new_user = User(email=email, password=password, phone_number=phone)
        db.session.add(new_user)
        db.session.commit()

        existing_email = User.query.filter_by(email=email).first()
        session["user_id"] = existing_email.user_id
        current_user = session["user_id"]

        new_cat = Cat(user_id=current_user, name=name, dinner_time=date, 
                  snack=snack, activity1=activity1, activity2=activity2, 
                  toy1=toy1, toy2=toy2)
        db.session.add(new_cat)
        db.session.commit()

        message = client.messages.create(
        to=phone, 
        from_="+14138486585",
        # media_url="https://static.pexels.com/photos/62321/kitten-cat-fluffy-cat-cute-62321.jpeg",
        body="Hi, it's " + name + ". I like " + snack + "! Feed me at " + dinner_time + "!")

        print(message.sid)

        flash("Successfully registered " + email + "!")
        return render_template("thanks.html")

    else:
        flash("Email already in use")
        # TODO probably handle this in AJAX on the form

    return redirect("/")


@app.route("/main")
def main_page():
    """Render main page"""

    user_id = session["user_id"]
    cat = Cat.query.filter_by(user_id=user_id).first()

    # TODO this is dupe code from login route, factor out
    cat.dinner_time = cat.dinner_time.replace(tzinfo=pytz.utc)
    # TODO get user's local time instead of hardcoding PST
    cat.dinner_time = cat.dinner_time.astimezone(timezone('US/Pacific'))

    time = [str(cat.dinner_time.hour), ":", str(cat.dinner_time.minute)]
    time = parse_time("".join(time))
    hour, minutes = time

    ampm = am_or_pm(hour) # get whether am or pm
    hour = make_12_hour_time(hour) # convert to 12 hour time

    cat.dinner_time = cat.dinner_time.replace(hour=hour)

    return render_template("main.html", name=cat.name, toy1=cat.toy1, 
                                        toy2=cat.toy2, snack=cat.snack, 
                                        activity1=cat.activity1,
                                        activity2=cat.activity2, 
                                        dinner_time=cat.dinner_time,
                                        ampm=ampm)


@app.route("/update")
def show_update():
    """Show update page"""

    return render_template("update.html")


@app.route("/update", methods=['POST'])
def do_update():
    """Update details in db"""

    name = request.form.get('cat-name')
    dinner_time = request.form.get('dinner-time')
    ampm = request.form.get('ampm')
    snack = request.form.get('cat-snack')
    activity1 = request.form.get('cat-activity')
    activity2 = request.form.get('cat-activity2')
    toy1 = request.form.get('cat-toy')
    toy2 = request.form.get('cat-toy2')

    user_id = session["user_id"]
    cat = Cat.query.filter_by(user_id=user_id).first()

    if name:
        cat.name = name

    if dinner_time:
        time = parse_time(dinner_time)
        hour = time[0]
        minutes = time[1]
        hour = make_24_hour_time(ampm, hour)
        date = convert_to_utc(hour, minutes)    

        cat.dinner_time = date
        cat.dinner_time = cat.dinner_time.replace(tzinfo=None)

    if toy1:
        cat.toy1 = toy1
    if toy2:
        cat.toy2 = toy2
    if snack:
        cat.snack = snack
    if activity1:
        cat.activity1 = activity1
    if activity2:
        cat.activity2 = activity2

    db.session.commit()

    flash("Successfully updated " + cat.name + "'s info!")

    return render_template("main.html", name=cat.name, toy1=cat.toy1, 
                                        toy2=cat.toy2, snack=cat.snack, 
                                        activity1=cat.activity1,
                                        activity2=cat.activity2, 
                                        dinner_time=cat.dinner_time)


@app.route("/sms", methods=['POST'])
def incoming_sms():
    """Send a dynamic reply to an incoming text message"""

    phone = request.values.get('From', None)
    user_id = User.query.filter_by(phone_number=phone).one()
    cat = Cat.query.filter_by(user_id=user_id.user_id).first()

    toy1_msg = 'Can we play with my ' + cat.toy1 + '?'
    toy2_msg = "I think it's time for the " + cat.toy2 + "!!!"
    snack_msg = "I'm hungry!! I want " + cat.snack + "!"
    activity1_msg = "Whachu up to? I'm busy " + cat.activity1 + "..."
    activity2_msg = "Me? I'm just " + cat.activity2 + "..."
    # TODO make more messages! it's pretty repetitive right meow

    cat_responses = [toy1_msg, toy2_msg, snack_msg, activity1_msg, activity2_msg]

    # Get the message the user sent our Twilio number
    body = request.values.get('Body', None)
    # Start our TwiML response
    resp = MessagingResponse()

    # Determine the right reply for this message
    # TODO make more of these! it'll be more fun for the user
    if (body == 'hey') or (body == 'Hey'):
        resp.message("Hi! Where's my " + cat.snack + "?!")
    elif (body == 'bye') or (body == 'Bye'):
        resp.message("Bye? I'm just going to text you again later.")
    else:
        reply = random.choice(cat_responses)
        resp.message(reply)

    return str(resp)


if __name__ == "__main__":

    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)
    print "Connected to DB."

    app.run(port=5000, host='0.0.0.0')


