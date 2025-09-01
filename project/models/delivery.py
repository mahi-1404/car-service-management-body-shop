from . import db
from datetime import datetime

class Delivery(db.Model):
    """Delivery status tracking model"""
    __tablename__ = 'deliveries'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False)
    is_delivered = db.Column(db.Boolean, default=False)
    delivery_date = db.Column(db.DateTime)
    delivered_by = db.Column(db.String(100))
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Delivery {self.vehicle_number} - {self.is_delivered}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_number': self.vehicle_number,
            'is_delivered': self.is_delivered,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'delivered_by': self.delivered_by,
            'notes': self.notes
        }