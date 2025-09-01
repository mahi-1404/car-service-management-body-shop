from . import db
from datetime import datetime

class Claim(db.Model):
    """Claim number management model"""
    __tablename__ = 'claims'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False)
    claim_number = db.Column(db.String(100))
    updated_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Claim {self.vehicle_number} - {self.claim_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_number': self.vehicle_number,
            'claim_number': self.claim_number,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None
        }