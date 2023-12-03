import base64
import datetime
import json
import os

from io import BytesIO
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import find_dotenv, load_dotenv
from telethon import TelegramClient, events

app = Flask(__name__)
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

# Database configuration
user = os.getenv("SQL_USER")
password = os.getenv("SQL_PASS")
port = os.getenv("SQL_PORT")
host = os.getenv("SQL_HOST")
schema_name = os.getenv("SCHEMA_NAME")
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"mysql+pymysql://{user}:{password}@{host}:{port}/{schema_name}"
db = SQLAlchemy(app)


# ORM Model
class Event(db.Model):
    __tablename__ = "event"
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255))
    date = db.Column(db.String(25))
    location = db.Column(db.String(255))
    time = db.Column(db.String(25))
    link = db.Column(db.String(100))
    additional_details = db.Column(db.String(255))
    picture = db.Column(db.JSON)
    created_at = db.Column(db.DateTime)
    title = db.Column(db.String(50))


# View
class EventView:
    @staticmethod
    def display_event(event):
        print("Event id:", event.id)
        print("Description:", event.description)
        print("Date:", event.date)
        print("Location:", event.location)
        print("Time:", event.time)
        print("Link:", event.link)
        print("Additional Details:", event.additional_details)
        print("Picture:", event.picture)
        print("Created At:", event.created_at)
        print("Title:", event.title)
        print("=======================================")


def handle_new_event():
    @client.on(events.NewMessage(chats=os.getenv("TG_CHANNEL_LINK")))
    async def my_event_handler(event):
        event_dict = {}

        try:
            print("=======================================")
            if event.photo:
                print("Event has a photo")
                img_bytes = await event.download_media(BytesIO())
                img_base64 = base64.b64encode(img_bytes.getvalue()).decode("utf-8")
                img_json = {"image": img_base64}
                event_dict["picture"] = json.dumps(img_json)

            print("Event raw msg: ", event.raw_text)

            for line in event.raw_text.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    event_dict[key.strip()] = value.strip()

            event_dict["created_at"] = datetime.datetime.now().isoformat()
            event_json = json.dumps(event_dict)

        except ValueError as e:
            print("Value Error:", str(e))

        print(f"Event id: {event.id}")
        print("=======================================")

        event_data = json.loads(event_json)
        new_event = Event(**event_data)

        EventView.display_event(new_event)

        if new_event.title is not None and new_event.description is not None:
            with app.app_context():
                db.session.add(new_event)
                db.session.commit()

    client.start()
    client.run_until_disconnected()


if __name__ == "__main__":
    api_id = os.getenv("TG_API_ID")
    api_hash = os.getenv("TG_API_HASH")

    client = TelegramClient("anon", api_id, api_hash)

    handle_new_event()
    app.run(port=os.getenv("PORT"))
