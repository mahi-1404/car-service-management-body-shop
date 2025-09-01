from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
import os
from werkzeug.utils import secure_filename
from models import db, init_db
from models.inventory import Inventory
from models.photos import Photo
from models.work_status import WorkStatus, WorkItem
from models.claims import Claim
from models.approvals import Approval
from models.registration_status import RegistrationStatus
from models.delivery import Delivery
import json
from reports.generator import ReportGenerator
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///car_service.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'photos'
# Remove file size limit for images
app.config['MAX_CONTENT_LENGTH'] = None

# Initialize database
init_db(app)

# Add template globals
@app.template_global()
def moment_now():
    return datetime.now()

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_monthly_folder(vehicle_number):
    """Create monthly folder structure for photos"""
    current_date = datetime.now()
    month_folder = current_date.strftime('%Y-%m')
    vehicle_folder = os.path.join(app.config['UPLOAD_FOLDER'], month_folder, vehicle_number)
    os.makedirs(vehicle_folder, exist_ok=True)
    return vehicle_folder

@app.route('/')
def dashboard():
    """Main dashboard showing all vehicles and their progress"""
    vehicles = Inventory.query.order_by(Inventory.serial_number.asc()).all()
    
    # Calculate progress for each vehicle
    vehicle_progress = []
    for vehicle in vehicles:
        progress = calculate_vehicle_progress(vehicle)
        vehicle_progress.append({
            'vehicle': vehicle,
            'progress': progress
        })
    
    return render_template('dashboard.html', vehicle_progress=vehicle_progress)

def calculate_vehicle_progress(vehicle):
    """Calculate completion percentage for a vehicle"""
    total_steps = 4  # Inventory, Registration, Claim, Work Status
    completed_steps = 1  # Inventory is always completed if vehicle exists
    
    # Check registration
    registration = RegistrationStatus.query.filter_by(vehicle_number=vehicle.vehicle_number).first()
    if registration and registration.is_completed:
        completed_steps += 1
    
    # Check claim
    claim = Claim.query.filter_by(vehicle_number=vehicle.vehicle_number).first()
    if claim and claim.claim_number:
        completed_steps += 1
    
    # Check work status
    work_status = WorkStatus.query.filter_by(vehicle_number=vehicle.vehicle_number).first()
    if work_status:
        work_items = WorkItem.query.filter_by(work_status_id=work_status.id).all()
        if work_items and all(item.is_completed for item in work_items):
            completed_steps += 1
    
    return int((completed_steps / total_steps) * 100)

# Module 1: Inventory Management
@app.route('/add_inventory', methods=['GET', 'POST'])
def add_inventory():
    """Add new vehicle to inventory"""
    if request.method == 'POST':
        vehicle_number = request.form['vehicle_number'].upper()
        
        # Check if vehicle already exists
        existing_vehicle = Inventory.query.filter_by(vehicle_number=vehicle_number).first()
        if existing_vehicle:
            flash('Vehicle already exists in inventory!', 'error')
            return redirect(url_for('add_inventory'))
        
        # Generate serial number
        last_vehicle = Inventory.query.order_by(Inventory.serial_number.desc()).first()
        serial_number = (last_vehicle.serial_number + 1) if last_vehicle else 1
        
        vehicle = Inventory(
            serial_number=serial_number,
            vehicle_number=vehicle_number,
            vehicle_name=request.form.get('vehicle_name', ''),
            customer_name=request.form.get('customer_name', ''),
            phone_number=request.form.get('phone_number', ''),
            insurance_name=request.form.get('insurance_name', ''),
            kilometer_reading=int(request.form['kilometer_reading']),
            engine_number=request.form['engine_number'],
            chassis_number=request.form['chassis_number'],
            description=request.form['description'],
            check_in_date=datetime.now()
        )
        
        db.session.add(vehicle)
        db.session.commit()
        
        flash('Vehicle added successfully!', 'success')
        return redirect(url_for('view_inventory'))
    
    return render_template('inventory_form.html')

@app.route('/view_inventory')
def view_inventory():
    """View all vehicles in inventory"""
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'check_in_date')
    order = request.args.get('order', 'asc')  # Default to ascending
    
    query = Inventory.query
    
    if search:
        query = query.filter(db.or_(
                Inventory.vehicle_number.contains(search.upper()),
                Inventory.customer_name.contains(search),
                Inventory.insurance_name.contains(search),
                Inventory.phone_number.contains(search)
            ))
    
    if sort_by == 'vehicle_number':
        if order == 'desc':
            query = query.order_by(Inventory.vehicle_number.desc())
        else:
            query = query.order_by(Inventory.vehicle_number.asc())
    elif sort_by == 'serial_number':
        if order == 'desc':
            query = query.order_by(Inventory.serial_number.desc())
        else:
            query = query.order_by(Inventory.serial_number.asc())
    elif sort_by == 'customer_name':
        if order == 'desc':
            query = query.order_by(Inventory.customer_name.desc())
        else:
            query = query.order_by(Inventory.customer_name.asc())
    else:
        # Default sort by check_in_date
        if order == 'desc':
            query = query.order_by(Inventory.check_in_date.desc())
        else:
            query = query.order_by(Inventory.check_in_date.asc())
    
    vehicles = query.all()
    
    # Get first photo for each vehicle for thumbnail display
    photos_dict = {}
    for vehicle in vehicles:
        photos = Photo.query.filter_by(vehicle_number=vehicle.vehicle_number).limit(1).all()
        if photos:
            photos_dict[vehicle.vehicle_number] = photos
    
    return render_template('inventory_list.html', vehicles=vehicles, search=search, 
                         sort_by=sort_by, order=order, photos_dict=photos_dict)
@app.route('/edit_inventory/<int:vehicle_id>', methods=['GET', 'POST'])
def edit_inventory(vehicle_id):
    """Edit vehicle inventory details"""
    vehicle = Inventory.query.get_or_404(vehicle_id)
    
    if request.method == 'POST':
        vehicle.vehicle_number = request.form['vehicle_number'].upper()
        vehicle.vehicle_name = request.form.get('vehicle_name', '')
        vehicle.customer_name = request.form.get('customer_name', '')
        vehicle.phone_number = request.form.get('phone_number', '')
        vehicle.insurance_name = request.form.get('insurance_name', '')
        vehicle.kilometer_reading = int(request.form['kilometer_reading'])
        vehicle.engine_number = request.form['engine_number']
        vehicle.chassis_number = request.form['chassis_number']
        vehicle.description = request.form['description']
        
        db.session.commit()
        flash('Vehicle details updated successfully!', 'success')
        return redirect(url_for('view_inventory'))
    
    return render_template('edit_inventory.html', vehicle=vehicle)

# Module 2: Photo Upload & Inspection
@app.route('/upload_photos/<vehicle_number>', methods=['GET', 'POST'])
def upload_photos(vehicle_number):
    """Upload inspection photos for a vehicle"""
    vehicle = Inventory.query.filter_by(vehicle_number=vehicle_number).first_or_404()
    
    if request.method == 'POST':
        photo_types = ['front', 'right_front', 'full_right', 'right_back', 'full_back', 
                      'left_back', 'full_left', 'left_front', 'odometer', 'chassis_number']
        
        vehicle_folder = get_monthly_folder(vehicle_number)
        uploaded_count = 0
        
        for photo_type in photo_types:
            if photo_type in request.files:
                file = request.files[photo_type]
                if file and file.filename and allowed_file(file.filename):
                    filename = f"{photo_type}.{file.filename.rsplit('.', 1)[1].lower()}"
                    filepath = os.path.join(vehicle_folder, filename)
                    file.save(filepath)
                    
                    # Save to database
                    photo = Photo(
                        vehicle_number=vehicle_number,
                        photo_type=photo_type,
                        filename=filename,
                        filepath=filepath,
                        upload_date=datetime.now()
                    )
                    db.session.add(photo)
                    uploaded_count += 1
        
        # Handle damage photos (multiple allowed)
        damage_files = request.files.getlist('damages')
        for i, file in enumerate(damage_files):
            if file and file.filename and allowed_file(file.filename):
                filename = f"damage_{i+1}.{file.filename.rsplit('.', 1)[1].lower()}"
                filepath = os.path.join(vehicle_folder, filename)
                file.save(filepath)
                
                photo = Photo(
                    vehicle_number=vehicle_number,
                    photo_type='damage',
                    filename=filename,
                    filepath=filepath,
                    upload_date=datetime.now()
                )
                db.session.add(photo)
                uploaded_count += 1
        
        db.session.commit()
        flash(f'{uploaded_count} photos uploaded successfully!', 'success')
        return redirect(url_for('view_photos', vehicle_number=vehicle_number))
    
    return render_template('photo_upload.html', vehicle=vehicle)

@app.route('/view_photos/<vehicle_number>')
def view_photos(vehicle_number):
    """View all photos for a vehicle"""
    vehicle = Inventory.query.filter_by(vehicle_number=vehicle_number).first_or_404()
    photos = Photo.query.filter_by(vehicle_number=vehicle_number).all()
    
    # Group photos by type
    photo_groups = {}
    for photo in photos:
        if photo.photo_type not in photo_groups:
            photo_groups[photo.photo_type] = []
        # Replace backslashes with forward slashes for URL compatibility
        photo.filepath = photo.filepath.replace('\\', '/')
        photo_groups[photo.photo_type].append(photo)
    
    total_photos = len(photos)
    
    return render_template('photo_gallery.html', vehicle=vehicle, photo_groups=photo_groups, total_photos=total_photos)

@app.route('/photo/<path:filepath>')
def serve_photo(filepath):
    """Serve uploaded photos"""
    try:
        # Check if file exists
        if os.path.exists(filepath):
            return send_file(filepath)
        else:
            # Return placeholder image if file not found
            return send_file('static/images/placeholder.jpg')
    except FileNotFoundError:
        # Return a default placeholder image if file not found
        return send_file('static/images/placeholder.jpg')

# Module 3: Registration Status
@app.route('/update_registration/<vehicle_number>', methods=['POST'])
def update_registration(vehicle_number):
    """Update registration status"""
    is_completed = request.json.get('is_completed', False)
    
    registration = RegistrationStatus.query.filter_by(vehicle_number=vehicle_number).first()
    if not registration:
        registration = RegistrationStatus(vehicle_number=vehicle_number)
        db.session.add(registration)
    
    registration.is_completed = is_completed
    registration.completion_date = datetime.now() if is_completed else None
    
    db.session.commit()
    return jsonify({'success': True})

# Module 4: Claim Number Management
@app.route('/update_claim/<vehicle_number>', methods=['POST'])
def update_claim(vehicle_number):
    """Update claim number"""
    claim_number = request.json.get('claim_number', '').strip()
    
    claim = Claim.query.filter_by(vehicle_number=vehicle_number).first()
    if not claim:
        claim = Claim(vehicle_number=vehicle_number)
        db.session.add(claim)
    
    claim.claim_number = claim_number
    claim.updated_date = datetime.now()
    
    db.session.commit()
    return jsonify({'success': True})

# Module 5: Application Approval Status
@app.route('/update_approval/<vehicle_number>', methods=['POST'])
def update_approval(vehicle_number):
    """Update approval status"""
    is_approved = request.json.get('is_approved', False)
    
    approval = Approval.query.filter_by(vehicle_number=vehicle_number).first()
    if not approval:
        approval = Approval(vehicle_number=vehicle_number)
        db.session.add(approval)
    
    approval.is_approved = is_approved
    approval.approval_date = datetime.now() if is_approved else None
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/validate_claim', methods=['POST'])
def validate_claim():
    """Validate claim number for duplicates"""
    claim_number = request.json.get('claim_number', '').strip()
    vehicle_number = request.json.get('vehicle_number', '')
    
    existing_claim = Claim.query.filter(
        Claim.claim_number == claim_number,
        Claim.vehicle_number != vehicle_number
    ).first()
    
    return jsonify({
        'is_duplicate': existing_claim is not None,
        'message': 'Claim number already exists for another vehicle' if existing_claim else 'Claim number is available'
    })

# Module 6: Work Status Tracker
@app.route('/work_status/<vehicle_number>')
def work_status(vehicle_number):
    """View and manage work status"""
    vehicle = Inventory.query.filter_by(vehicle_number=vehicle_number).first_or_404()
    
    work_status = WorkStatus.query.filter_by(vehicle_number=vehicle_number).first()
    if not work_status:
        # Create default work status with standard checklist
        work_status = WorkStatus(vehicle_number=vehicle_number)
        db.session.add(work_status)
        db.session.commit()
        
        # Add default work items
        default_items = ['Tinkering', 'Painting', 'Fitting', 'Polish', 'Washing']
        for item_name in default_items:
            work_item = WorkItem(
                work_status_id=work_status.id,
                item_name=item_name,
                is_completed=False
            )
            db.session.add(work_item)
        db.session.commit()
    
    work_items = WorkItem.query.filter_by(work_status_id=work_status.id).all()
    
    # Calculate progress
    completed_items = sum(1 for item in work_items if item.is_completed)
    total_items = len(work_items)
    progress = int((completed_items / total_items) * 100) if total_items > 0 else 0
    
    return render_template('work_status.html', vehicle=vehicle, work_items=work_items, progress=progress)

@app.route('/update_work_item/<int:item_id>', methods=['POST'])
def update_work_item(item_id):
    """Update work item completion status"""
    is_completed = request.json.get('is_completed', False)
    
    work_item = WorkItem.query.get_or_404(item_id)
    work_item.is_completed = is_completed
    work_item.completion_date = datetime.now() if is_completed else None
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/add_work_item/<vehicle_number>', methods=['POST'])
def add_work_item(vehicle_number):
    """Add custom work item"""
    item_name = request.json.get('item_name', '').strip()
    
    if not item_name:
        return jsonify({'success': False, 'error': 'Item name is required'})
    
    work_status = WorkStatus.query.filter_by(vehicle_number=vehicle_number).first()
    if not work_status:
        return jsonify({'success': False, 'error': 'Work status not found'})
    
    work_item = WorkItem(
        work_status_id=work_status.id,
        item_name=item_name,
        is_completed=False
    )
    db.session.add(work_item)
    db.session.commit()
    
    return jsonify({'success': True, 'item_id': work_item.id})

@app.route('/remove_work_item/<int:item_id>', methods=['POST'])
def remove_work_item(item_id):
    """Remove work item"""
    work_item = WorkItem.query.get_or_404(item_id)
    db.session.delete(work_item)
    db.session.commit()
    
    return jsonify({'success': True})

# Module 7: Search & Status Overview
@app.route('/search_vehicle')
def search_vehicle():
    """Search for a specific vehicle"""
    vehicle_number = request.args.get('vehicle_number', '').upper()
    
    if not vehicle_number:
        return render_template('search_vehicle.html')
    
    vehicle = Inventory.query.filter_by(vehicle_number=vehicle_number).first()
    if not vehicle:
        flash('Vehicle not found!', 'error')
        return render_template('search_vehicle.html')
    
    # Get all related data
    photos = Photo.query.filter_by(vehicle_number=vehicle_number).all()
    registration = RegistrationStatus.query.filter_by(vehicle_number=vehicle_number).first()
    claim = Claim.query.filter_by(vehicle_number=vehicle_number).first()
    approval = Approval.query.filter_by(vehicle_number=vehicle_number).first()
    work_status = WorkStatus.query.filter_by(vehicle_number=vehicle_number).first()
    work_items = WorkItem.query.filter_by(work_status_id=work_status.id).all() if work_status else []
    
    progress = calculate_vehicle_progress(vehicle)
    
    return render_template('vehicle_status.html', 
                         vehicle=vehicle, 
                         photos=photos,
                         registration=registration,
                         claim=claim,
                         approval=approval,
                         work_items=work_items,
                         progress=progress)

# Module 8: Delivery Management
@app.route('/delivery_details')
def delivery_details():
    """Show delivery management page"""
    vehicles = Inventory.query.all()
    pending_vehicles = []
    delivered_vehicles = []
    
    for vehicle in vehicles:
        # Check if all steps are completed
        registration = RegistrationStatus.query.filter_by(vehicle_number=vehicle.vehicle_number).first()
        claim = Claim.query.filter_by(vehicle_number=vehicle.vehicle_number).first()
        approval = Approval.query.filter_by(vehicle_number=vehicle.vehicle_number).first()
        work_status = WorkStatus.query.filter_by(vehicle_number=vehicle.vehicle_number).first()
        
        # Vehicle is ready for delivery if all major steps are completed
        is_ready = (
            registration and registration.is_completed and
            claim and claim.claim_number and
            approval and approval.is_approved and
            work_status
        )
        
        if work_status:
            work_items = WorkItem.query.filter_by(work_status_id=work_status.id).all()
            work_completed = all(item.is_completed for item in work_items) if work_items else False
            is_ready = is_ready and work_completed
        
        # Check delivery status
        delivery = Delivery.query.filter_by(vehicle_number=vehicle.vehicle_number).first()
        
        if is_ready:
            if delivery and delivery.is_delivered:
                delivered_vehicles.append((vehicle, delivery))
            else:
                pending_vehicles.append(vehicle)
    
    return render_template('delivery_details.html', 
                         pending_vehicles=pending_vehicles,
                         delivered_vehicles=delivered_vehicles,
                         current_date=date.today())

@app.route('/mark_delivered/<vehicle_number>', methods=['POST'])
def mark_delivered(vehicle_number):
    """Mark vehicle as delivered"""
    delivered_by = request.json.get('delivered_by', '')
    notes = request.json.get('notes', '')
    
    delivery = Delivery.query.filter_by(vehicle_number=vehicle_number).first()
    if not delivery:
        delivery = Delivery(vehicle_number=vehicle_number)
        db.session.add(delivery)
    
    delivery.is_delivered = True
    delivery.delivery_date = datetime.now()
    delivery.delivered_by = delivered_by
    delivery.notes = notes
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/undo_delivery/<vehicle_number>', methods=['POST'])
def undo_delivery(vehicle_number):
    """Undo delivery status"""
    delivery = Delivery.query.filter_by(vehicle_number=vehicle_number).first()
    if delivery:
        delivery.is_delivered = False
        delivery.delivery_date = None
        delivery.delivered_by = None
        delivery.notes = None
        db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/dashboard_stats')
def dashboard_stats():
    """API endpoint for dashboard statistics"""
    vehicles = Inventory.query.all()
    total_vehicles = len(vehicles)
    completed_vehicles = 0
    
    for vehicle in vehicles:
        progress = calculate_vehicle_progress(vehicle)
        if progress == 100:
            completed_vehicles += 1
    
    in_progress = total_vehicles - completed_vehicles
    completion_rate = int((completed_vehicles / total_vehicles) * 100) if total_vehicles > 0 else 0
    
    return jsonify({
        'total': total_vehicles,
        'completed': completed_vehicles,
        'in_progress': in_progress,
        'completion_rate': completion_rate
    })

@app.route('/generate_report')
def generate_report():
    """Generate and download reports"""
    report_type = request.args.get('type', 'daily')
    format_type = request.args.get('format', 'pdf')
    
    generator = ReportGenerator()
    
    if report_type == 'daily':
        filename = generator.generate_daily_report(format_type)
    elif report_type == 'monthly':
        filename = generator.generate_monthly_report(format_type)
    elif report_type == 'all_cars':
        filename = generator.generate_all_cars_report(format_type)
    else:
        flash('Invalid report type!', 'error')
        return redirect(url_for('dashboard'))
    
    return send_file(filename, as_attachment=True)

@app.route('/reports')
def reports():
    """Reports page"""
    return render_template('reports.html')

@app.route('/all_cars_report')
def all_cars_report():
    """Display all cars in a table"""
    vehicles = Inventory.query.order_by(Inventory.serial_number.asc()).all()
    claims = {c.vehicle_number: c.claim_number for c in Claim.query.all()}
    return render_template('all_cars_report.html', vehicles=vehicles, claims=claims)

@app.route('/daily_report')
def daily_report():
    """Display daily report in a table"""
    today = date.today()
    vehicles = Inventory.query.filter(
        Inventory.check_in_date >= datetime.combine(today, datetime.min.time()),
        Inventory.check_in_date < datetime.combine(today + timedelta(days=1), datetime.min.time())
    ).all()
    claims = {c.vehicle_number: c.claim_number for c in Claim.query.all()}
    return render_template('daily_report.html', vehicles=vehicles, claims=claims)

@app.route('/monthly_report')
def monthly_report():
    """Display monthly report in a table"""
    today = date.today()
    first_day = today.replace(day=1)
    vehicles = Inventory.query.filter(
        Inventory.check_in_date >= datetime.combine(first_day, datetime.min.time()),
        Inventory.check_in_date < datetime.combine(today + timedelta(days=1), datetime.min.time())
    ).all()
    claims = {c.vehicle_number: c.claim_number for c in Claim.query.all()}
    return render_template('monthly_report.html', vehicles=vehicles, claims=claims)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=9696)
