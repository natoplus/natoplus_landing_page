# Import required libraries and packages
from flask import Flask, render_template, request, redirect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
from flask_sqlalchemy import SQLAlchemy
import socket
import time
import os

import smtplib
from email.message import EmailMessage
import ssl

# Pseudo-constants
MAIL_ADDRESS = os.environ.get("NATO_GMAIL")
MAIL_APP_PW = os.environ.get("MAIL_PASSWORD")

# Create flask application
app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECR_KEY")


# Create database
class Base(DeclarativeBase):
    pass


app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("NATO_DB_URI", "sqlite:///email-addrs.db")
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///email-addrs.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Create and configure Table
class Emails(db.Model):
    __tablename__ = "Email_addresses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, unique=True)


with app.app_context():
    db.create_all()
email_list = []


def read_data(llist, class_):
    with app.app_context():
        all_mails = db.session.execute(db.select(class_).order_by(class_.id)).scalars()
        llist.clear()
        llist.extend(all_mails)


def send_welcome_mail(name, email, new=True):
    message = EmailMessage()
    message["From"] = MAIL_ADDRESS
    message["To"] = email
    message["Subject"] = "Newsletter signup confirmation"
    message.add_header("Reply-To", "noreply@natomail.com")

    disclaimer = "This mail is sent from an unmonitored mailbox. Please do not reply."
    welcome_msg = f"Welcome aboard {name}! 🎉 You're now part of our exclusive newsletter community.\n" \
                  f"Get ready to unlock exciting updates, special offers, and insider insights delivered straight" \
                  f"to your inbox.\nStay tuned for a journey filled with knowledge, inspiration, and surprises! 🚀" \
                  f"\n\n\n{disclaimer}"
    overdo_msg = f"Welcome back {name}! 🌟 It looks like you're already part of our amazing newsletter community.\n" \
                 f"No need to sign up again – you're already set to receive our latest updates, exclusive offers, and" \
                 f"insider content.\nSit back, relax, and enjoy the journey ahead! ✨" \
                 f"\n\n\n{disclaimer}"
    if new:
        message.set_content(welcome_msg)
    else:
        message.set_content(overdo_msg)

    context = ssl.create_default_context()

    while True:
        try:
            with smtplib.SMTP_SSL(host="smtp.gmail.com", port=465, context=context) as connection:
                connection.login(user=MAIL_ADDRESS, password=MAIL_APP_PW)
                connection.sendmail(from_addr=MAIL_APP_PW, to_addrs=email, msg=message.as_string())
        except smtplib.SMTPConnectError as f:
            print("error as", f)
        except smtplib.SMTPException as e:
            print("Encountered smtp error :", e)
            print(MAIL_APP_PW)
            print(MAIL_ADDRESS)
            break
        except socket.gaierror as e:
            time.sleep(3)
            print("there is an error:", e)
        else:
            break


# Create flask routes
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        read_data(email_list, Emails)
        data = request.form
        user_email = data["email"]
        user_name = next((email.name for email in email_list if email.address == user_email), None)
        if not user_name:
            user_name = data["name"]
            new_email = Emails(name=user_name, address=user_email)
            with app.app_context():
                db.session.add(new_email)
                db.session.commit()
            send_welcome_mail(name=user_name, email=user_email)
        else:

            send_welcome_mail(name=user_name, email=user_email, new=False)
        return render_template("done.html")
    return render_template("index.html")

@app.route("/success")
def go_back():
    # time.sleep(3)
    return redirect("https://natoplus.framer.ai")

@app.route("/test")
def temp():
    return render_template("done.html")

if __name__ == "__main__":
    app.run(debug=True)
