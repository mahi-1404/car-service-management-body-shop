from . import db
from datetime import datetime

class Photo(db.Model):
    """Photo storage model"""
    __tablename__ = 'photos'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), nullable=False)
    photo_type = db.Column(db.String(50), nullable=False)  # front, right_front, damage, etc.
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Photo {self.vehicle_number} - {self.photo_type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_number': self.vehicle_number,
            'photo_type': self.photo_type,
            'filename': self.filename,
            'filepath': self.filepath,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None
        }