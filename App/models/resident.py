import re
from datetime import datetime
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import JSON

from App.database import db
from .user import User
from .driver import Driver
from .stop import Stop

MAX_INBOX_SIZE = 20


class Resident(User):
    __tablename__ = "resident"

    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    areaId = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=False)
    streetId = db.Column(db.Integer,
                         db.ForeignKey('street.id'),
                         nullable=False)
    houseNumber = db.Column(db.Integer, nullable=False)
    inbox = db.Column(MutableList.as_mutable(JSON), default=[])

    area = db.relationship("Area", backref='residents')
    street = db.relationship("Street", backref='residents')
    stops = db.relationship('Stop', backref='resident')

    __mapper_args__ = {
        "polymorphic_identity": "Resident",
    }

    def __init__(self, username, password, areaId, streetId, houseNumber):
        super().__init__(username, password)
        self.areaId = areaId
        self.streetId = streetId
        self.houseNumber = houseNumber

    def get_json(self):
        user_json = super().get_json()
        user_json['areaId'] = self.areaId
        user_json['streetId'] = self.streetId
        user_json['houseNumber'] = self.houseNumber
        user_json['inbox'] = self.inbox
        return user_json

    def request_stop(self, driveId):
        try:
            new_stop = Stop(driveId=driveId, residentId=self.id)
            db.session.add(new_stop)
            db.session.commit()
            return (new_stop)
        except Exception:
            db.session.rollback()
            return None
        
    def request_stop_from_notification(self, notification):

        if isinstance(notification, dict):
            drive_id = notification.get("drive_id")
            if drive_id is None:
                raise ValueError("Notification payload has no 'drive_id'; cannot request stop.")
            return self.request_stop(drive_id)

        if isinstance(notification, int):
            if self.inbox is None:
                raise ValueError("Inbox is empty")
            try:
                notif_str = self.inbox[notification]
            except (IndexError, TypeError):
                raise ValueError("Invalid notification index")

        elif isinstance(notification, str):
            notif_str = notification
        else:
            raise TypeError("Unsupported notification type")

        if "]: " in notif_str:
            _, body = notif_str.split("]: ", 1)
        else:
            body = notif_str

        match = re.search(r"Drive #(\d+)", body)
        if not match:
            raise ValueError("Notification does not contain a drive id in the form 'Drive #<id>'")

        drive_id = int(match.group(1))
        return self.request_stop(drive_id)

    def cancel_stop(self, stopId):
        stop = Stop.query.get(stopId)
        if stop:
            db.session.delete(stop)
            db.session.commit()
        return

    def receive_notif(self, message):
        if self.inbox is None:
            self.inbox = []

        if len(self.inbox) >= MAX_INBOX_SIZE:
            self.inbox.pop(0)

        timestamp = datetime.now().strftime("%Y:%m:%d:%H:%M:%S")
        notif = f"[{timestamp}]: {message}"
        self.inbox.append(notif)
        db.session.add(self)
        db.session.commit()

    def view_inbox(self):
        return self.inbox
    
    def viewNotificationHistory(self):
        return self.view_inbox()

    def view_driver_stats(self, driverId):
        driver = Driver.query.get(driverId)
        return driver

    def subscribe(self, drive):
        if not hasattr(self, "_subscriptions"):
            self._subscriptions = set()

        if hasattr(drive, "registerObserver"):
            drive.registerObserver(self)

        if hasattr(drive, "id"):
            self._subscriptions.add(drive.id)

    def unsubscribe(self, drive):
        if not hasattr(self, "_subscriptions"):
            self._subscriptions = set()

        if hasattr(drive, "removeObserver"):
            drive.removeObserver(self)

        if hasattr(drive, "id") and drive.id in self._subscriptions:
            self._subscriptions.remove(drive.id)

    
    def update(self, payload):
        if self.inbox is None:
            self.inbox = []

        drive_id = payload.get("drive_id")
        base_message = (payload.get("message") or "").strip()

        if drive_id is not None:
            message_text = f"Drive #{drive_id}: {base_message}".strip()
        else:
            message_text = base_message

        for entry in self.inbox:
            if "]: " in entry:
                _, body = entry.split("]: ", 1)
            else:
                body = entry

            if body == message_text:
                return 
            
        self.receive_notif(message_text)
