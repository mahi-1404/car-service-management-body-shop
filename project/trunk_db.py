from app import app, db
from models.inventory import Inventory
from models.photos import Photo
from models.work_status import WorkStatus, WorkItem
from models.claims import Claim
from models.approvals import Approval
from models.registration_status import RegistrationStatus
from models.delivery import Delivery

def truncate_tables():
    """Truncate all tables in the database."""
    with app.app_context():
        # Delete all data from tables
        db.session.query(WorkItem).delete()
        db.session.query(WorkStatus).delete()
        db.session.query(Photo).delete()
        db.session.query(Delivery).delete()
        db.session.query(RegistrationStatus).delete()
        db.session.query(Approval).delete()
        db.session.query(Claim).delete()
        db.session.query(Inventory).delete()
        
        # Commit the changes
        db.session.commit()
        print("All tables have been truncated.")

if __name__ == '__main__':
    truncate_tables()
