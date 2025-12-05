from App.database import db


class Stop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driveId = db.Column(db.Integer, db.ForeignKey('drive.id'), nullable=False)
    residentId = db.Column(db.Integer,
                           db.ForeignKey('resident.id'),
                           nullable=False)

    status = db.Column(db.String(20), default="Pending")  # "Pending", "Subscribed", "Rejected"
    eta = db.Column(db.String(20), nullable=True)         # simple string like "12:30 PM"
    driver_status_msg = db.Column(db.String(120), nullable=True)

    drive = db.relationship('Drive', back_populates='stops')
    resident = db.relationship('Resident', back_populates='stops')

    def __init__(self, residentId, driveId, status=None):
        self.residentId = residentId
        self.driveId = driveId
        # if a status is passed, use it; otherwise the column default ("Pending") is used
        if status is not None:
            self.status = status
            
    def get_json(self):
        return {
            'id': self.id,
            'driveId': self.driveId,
            'residentId': self.residentId
        }