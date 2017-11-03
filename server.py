from flask import Flask, request, redirect, render_template
from twilio.twiml.messaging_response import MessagingResponse
import random
from twilio.rest import Client
import os
# Your Account SID from twilio.com/console
account_sid = os.environ.get("account_sid")
# Your Auth Token from twilio.com/console
auth_token = os.environ.get("auth_token")
client = Client(account_sid, auth_token)
phone_number = os.environ.get("phone_number")

app = Flask(__name__)
############################################################################

# CAT_INFO = {}

@app.route("/")
def main():
    """Render main page"""

    return render_template("homepage.html")

@app.route("/sms", methods=['POST'])
def incoming_sms():
    """Send a dynamic reply to an incoming text message"""
    # Get the message the user sent our Twilio number
    body = request.values.get('Body', None)
    cat_facts = ['a', 'b', 'c']
    # Start our TwiML response
    resp = MessagingResponse()

    # Determine the right reply for this message
    if body == 'hello':
        resp.message('sdgsg')
    elif body == 'bye':
        resp.message("Goodnight meow!")
    else:
        reply = random.choice(cat_facts)
        resp.message(reply)

    return str(resp)


@app.route("/welcome", methods=['GET', 'POST'])
def welcome():
    """Welcome to the user to Cat Texts"""

    # CAT_INFO[cat_name] = request.args.get("cat-name")
    cat_name = request.args.get("cat_name")
    print cat_name
    # CAT_INFO[snack] = request.args.get("cat-snack")

    message = client.messages.create(
    to=phone_number, 
    from_="+14138486585",
    media_url="https://static.pexels.com/photos/62321/kitten-cat-fluffy-cat-cute-62321.jpeg",
    body="Hi it's " + cat_name + "!!!! Reply 'hello' to say hi, 'bye' to say goodnight, and anything else to get a random message from yours truly!")

    print(message.sid)
    return render_template("homepage.html")

if __name__ == "__main__":

    app.run(port=5000, host='0.0.0.0')




