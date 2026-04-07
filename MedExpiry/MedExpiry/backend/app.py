# backend/app.py
"""
MedExpiry — Flask API Server
Main application entry point with all API routes.
"""

import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import Config
from ocr_engine import MedicineOCR
from medicine_db import MedicineDB
from donation_service import DonationService
from ai_predictor import ConsumptionPredictor

# ─────────────────────────────────────
# App Initialization
# ─────────────────────────────────────

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)
app.config.from_object(Config)

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# Service instances
ocr = MedicineOCR()
db = MedicineDB()
donation_service = DonationService()
predictor = ConsumptionPredictor()


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# ─────────────────────────────────────
# Frontend Serving
# ─────────────────────────────────────

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')


# ═══════════════════════════════════════
# 📸 SCAN API ROUTES
# ═══════════════════════════════════════

@app.route('/api/scan', methods=['POST'])
def scan_medicine():
    """
    Scan a medicine strip image and extract data via OCR.
    Accepts: multipart/form-data with 'image' file
    Returns: Extracted medicine data (name, expiry, batch, etc.)
    """
    # Check if image was uploaded
    if 'image' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No image file provided. Send an image with key "image".'
        }), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Empty filename.'}), 400

    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'error': f'Invalid file type. Allowed: {", ".join(Config.ALLOWED_EXTENSIONS)}'
        }), 400

    try:
        # Save uploaded file
        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Run OCR pipeline
        result = ocr.scan_medicine(filepath)

        # Clean up uploaded file
        try:
            os.remove(filepath)
        except OSError:
            pass

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Scan failed: {str(e)}'
        }), 500


@app.route('/api/scan/demo', methods=['GET'])
def scan_demo():
    """Return demo scan result for testing without a real image."""
    result = ocr.scan_medicine('demo')
    return jsonify(result), 200


# ═══════════════════════════════════════
# 📋 TRACK/INVENTORY API ROUTES
# ═══════════════════════════════════════

@app.route('/api/medicines', methods=['GET'])
def get_all_medicines():
    """Get all medicines in inventory."""
    family_id = request.args.get('family_id')
    medicines = db.get_all_medicines(family_id)
    return jsonify({
        'success': True,
        'count': len(medicines),
        'medicines': medicines
    }), 200


@app.route('/api/medicines', methods=['POST'])
def add_medicine():
    """Add a medicine to inventory (from scan result or manual entry)."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided.'}), 400

    record = db.add_medicine(data)
    return jsonify({
        'success': True,
        'message': f"{record['name']} added to inventory.",
        'medicine': record
    }), 201


@app.route('/api/medicines/<med_id>', methods=['GET'])
def get_medicine(med_id):
    """Get a single medicine by ID."""
    med = db.get_medicine(med_id)
    if not med:
        return jsonify({'success': False, 'error': 'Medicine not found.'}), 404
    return jsonify({'success': True, 'medicine': med}), 200


@app.route('/api/medicines/<med_id>', methods=['PUT'])
def update_medicine(med_id):
    """Update a medicine record."""
    data = request.get_json()
    med = db.update_medicine(med_id, data)
    if not med:
        return jsonify({'success': False, 'error': 'Medicine not found.'}), 404
    return jsonify({'success': True, 'medicine': med}), 200


@app.route('/api/medicines/<med_id>', methods=['DELETE'])
def delete_medicine(med_id):
    """Delete a medicine from inventory."""
    success = db.delete_medicine(med_id)
    if not success:
        return jsonify({'success': False, 'error': 'Medicine not found.'}), 404
    return jsonify({'success': True, 'message': 'Medicine deleted.'}), 200


@app.route('/api/medicines/<med_id>/consume', methods=['POST'])
def consume_medicine(med_id):
    """Log medicine consumption."""
    data = request.get_json() or {}
    qty = data.get('quantity', 1)
    med = db.log_consumption(med_id, qty)
    if not med:
        return jsonify({'success': False, 'error': 'Medicine not found.'}), 404
    return jsonify({
        'success': True,
        'message': f"Logged {qty} dose(s) of {med['name']}.",
        'medicine': med
    }), 200


# ═══════════════════════════════════════
# 📊 DASHBOARD API ROUTES
# ═══════════════════════════════════════

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """Get dashboard summary statistics."""
    stats = db.get_dashboard_stats()
    return jsonify({'success': True, 'stats': stats}), 200


@app.route('/api/dashboard/calendar', methods=['GET'])
def get_calendar():
    """Get medicines grouped by expiry month."""
    calendar = db.get_expiry_calendar()
    return jsonify({'success': True, 'calendar': calendar}), 200


@app.route('/api/dashboard/alerts', methods=['GET'])
def get_alerts():
    """Get smart alerts for expiring/low-stock medicines."""
    medicines = db.get_all_medicines()
    alerts = predictor.get_smart_alerts(medicines)
    return jsonify({
        'success': True,
        'count': len(alerts),
        'alerts': alerts
    }), 200


# ═══════════════════════════════════════
# 🤝 DONATE API ROUTES
# ═══════════════════════════════════════

@app.route('/api/ngos', methods=['GET'])
def get_ngos():
    """Get all NGO drop-off locations."""
    city = request.args.get('city')
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)

    if lat and lng:
        ngos = donation_service.get_nearby_ngos(lat, lng)
    elif city:
        ngos = donation_service.get_ngos_by_city(city)
    else:
        ngos = donation_service.get_all_ngos()

    return jsonify({
        'success': True,
        'count': len(ngos),
        'ngos': ngos
    }), 200


@app.route('/api/ngos/<ngo_id>', methods=['GET'])
def get_ngo(ngo_id):
    """Get a single NGO by ID."""
    ngo = donation_service.get_ngo_by_id(ngo_id)
    if not ngo:
        return jsonify({'success': False, 'error': 'NGO not found.'}), 404
    return jsonify({'success': True, 'ngo': ngo}), 200


@app.route('/api/donate', methods=['POST'])
def donate_medicine():
    """Mark a medicine for donation to an NGO."""
    data = request.get_json()
    if not data or 'medicine_id' not in data or 'ngo_id' not in data:
        return jsonify({
            'success': False,
            'error': 'Provide medicine_id and ngo_id.'
        }), 400

    med = db.mark_for_donation(data['medicine_id'], data['ngo_id'])
    if not med:
        return jsonify({
            'success': False,
            'error': 'Medicine not found, already donated, or expired.'
        }), 400

    ngo = donation_service.get_ngo_by_id(data['ngo_id'])
    return jsonify({
        'success': True,
        'message': f"{med['name']} marked for donation to {ngo['name'] if ngo else 'NGO'}.",
        'medicine': med
    }), 200


@app.route('/api/donate/eligible', methods=['GET'])
def get_donatable():
    """Get all medicines eligible for donation."""
    meds = db.get_donatable_medicines()
    return jsonify({
        'success': True,
        'count': len(meds),
        'medicines': meds
    }), 200


# ═══════════════════════════════════════
# 🤖 AI PREDICTIONS API ROUTES
# ═══════════════════════════════════════

@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    """Get AI consumption predictions for all medicines."""
    medicines = db.get_all_medicines()
    predictions = predictor.get_all_predictions(medicines)
    return jsonify({
        'success': True,
        'count': len(predictions),
        'predictions': predictions
    }), 200


@app.route('/api/predictions/<med_id>', methods=['GET'])
def get_prediction(med_id):
    """Get AI prediction for a specific medicine."""
    med = db.get_medicine(med_id)
    if not med:
        return jsonify({'success': False, 'error': 'Medicine not found.'}), 404
    prediction = predictor.predict_refill(med)
    return jsonify({'success': True, 'prediction': prediction}), 200


# ═══════════════════════════════════════
# 👨‍👩‍👧‍👦 FAMILY SHARING API ROUTES
# ═══════════════════════════════════════

@app.route('/api/family', methods=['POST'])
def create_family():
    """Create a new family group."""
    data = request.get_json()
    name = data.get('name', 'My Family')
    creator = data.get('creator', 'User')
    family = db.create_family(name, creator)
    return jsonify({
        'success': True,
        'message': f'Family "{name}" created! Share code: {family["invite_code"]}',
        'family': family
    }), 201


@app.route('/api/family/join', methods=['POST'])
def join_family():
    """Join a family using invite code."""
    data = request.get_json()
    code = data.get('invite_code', '')
    member = data.get('member', 'User')
    family = db.join_family(code, member)
    if not family:
        return jsonify({'success': False, 'error': 'Invalid invite code.'}), 404
    return jsonify({
        'success': True,
        'message': f'Joined family: {family["name"]}',
        'family': family
    }), 200


# ─────────────────────────────────────
# Run Server
# ─────────────────────────────────────

if __name__ == '__main__':
    print("\n" + "=" * 55)
    print("  💊 MedExpiry Server Running")
    print("  🌐 http://localhost:5000")
    print("  📡 API Base: http://localhost:5000/api")
    print("=" * 55 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
