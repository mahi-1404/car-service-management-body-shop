from . import db
from datetime import datetime

class WorkStatus(db.Model):
    """Work status tracking model"""
    __tablename__ = 'work_status'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with work items
    work_items = db.relationship('WorkItem', backref='work_status', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<WorkStatus {self.vehicle_number}>'

class WorkItem(db.Model):
    """Individual work item model"""
    __tablename__ = 'work_items'
    
    id = db.Column(db.Integer, primary_key=True)
    work_status_id = db.Column(db.Integer, db.ForeignKey('work_status.id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<WorkItem {self.item_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'work_status_id': self.work_status_id,
            'item_name': self.item_name,
            'is_completed': self.is_completed,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None
        }