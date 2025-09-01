from . import db
from datetime import datetime

class Approval(db.Model):
    """Application approval status model"""
    __tablename__ = 'approvals'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    approval_date = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Approval {self.vehicle_number} - {self.is_approved}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_number': self.vehicle_number,
            'is_approved': self.is_approved,
            'approval_date': self.approval_date.isoformat() if self.approval_date else None
        }