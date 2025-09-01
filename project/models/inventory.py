from . import db
from datetime import datetime

class Inventory(db.Model):
    """Vehicle inventory model"""
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.Integer, unique=True, nullable=False)
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False)
    vehicle_name = db.Column(db.String(100))
    customer_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(15))
    insurance_name = db.Column(db.String(100))
    kilometer_reading = db.Column(db.Integer, nullable=False)
    engine_number = db.Column(db.String(50), nullable=False)
    chassis_number = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    check_in_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Inventory {self.vehicle_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'serial_number': self.serial_number,
            'vehicle_number': self.vehicle_number,
            'vehicle_name': self.vehicle_name,
            'customer_name': self.customer_name,
            'phone_number': self.phone_number,
            'insurance_name': self.insurance_name,
            'kilometer_reading': self.kilometer_reading,
            'engine_number': self.engine_number,
            'chassis_number': self.chassis_number,
            'description': self.description,
            'check_in_date': self.check_in_date.isoformat() if self.check_in_date else None
        }