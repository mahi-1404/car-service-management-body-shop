from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    
    # Import all models to ensure they're registered
    from . import inventory, photos, work_status, claims, approvals, registration_status, delivery
    
    return db