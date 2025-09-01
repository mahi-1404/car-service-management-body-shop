from . import db
from datetime import datetime

class RegistrationStatus(db.Model):
    """Registration completion status model"""
    __tablename__ = 'registration_status'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<RegistrationStatus {self.vehicle_number} - {self.is_completed}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_number': self.vehicle_number,
            'is_completed': self.is_completed,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None
        }