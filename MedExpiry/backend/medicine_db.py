# backend/medicine_db.py
"""
Database layer for MedExpiry.
Uses an in-memory store for hackathon speed, easily swappable to Firebase/MongoDB.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional


class MedicineDB:
    """
    In-memory medicine database with full CRUD.
    Replace with Firebase/MongoDB for production.
    """

    def __init__(self):
        self.medicines = {}
        self.families = {}
        self.donation_history = []
        self._seed_demo_data()

    # ─────────────────────────────────────
    # CRUD Operations
    # ─────────────────────────────────────

    def add_medicine(self, data: dict) -> dict:
        """Add a scanned medicine to inventory."""
        med_id = str(uuid.uuid4())[:8]
        record = {
            'id': med_id,
            'name': data.get('medicine_name', 'Unknown'),
            'expiry_date': data.get('expiry_date'),
            'expiry_display': data.get('expiry_display', ''),
            'days_until_expiry': data.get('days_until_expiry'),
            'status': data.get('status', 'unknown'),
            'batch_number': data.get('batch_number'),
            'mfg_date': data.get('mfg_date'),
            'mrp': data.get('mrp'),
            'quantity': data.get('quantity', 1),
            'category': self._categorize_medicine(data.get('medicine_name', '')),
            'added_date': datetime.now().isoformat(),
            'added_by': data.get('added_by', 'default_user'),
            'family_id': data.get('family_id', 'family_default'),
            'notes': data.get('notes', ''),
            'donated': False,
            'consumption_log': [],
        }

        self.medicines[med_id] = record
        return record

    def get_medicine(self, med_id: str) -> Optional[dict]:
        return self.medicines.get(med_id)

    def get_all_medicines(self, family_id: str = None) -> list:
        """Get all medicines, optionally filtered by family."""
        meds = list(self.medicines.values())
        if family_id:
            meds = [m for m in meds if m.get('family_id') == family_id]

        # Recalculate days_until_expiry dynamically
        for med in meds:
            if med.get('expiry_date'):
                try:
                    exp = datetime.strptime(med['expiry_date'], '%Y-%m-%d')
                    med['days_until_expiry'] = (exp - datetime.now()).days
                    med['status'] = self._get_status(med['days_until_expiry'])
                except (ValueError, TypeError):
                    pass

        return sorted(meds, key=lambda x: x.get('days_until_expiry') or 9999)

    def update_medicine(self, med_id: str, updates: dict) -> Optional[dict]:
        if med_id in self.medicines:
            self.medicines[med_id].update(updates)
            return self.medicines[med_id]
        return None

    def delete_medicine(self, med_id: str) -> bool:
        if med_id in self.medicines:
            del self.medicines[med_id]
            return True
        return False

    def log_consumption(self, med_id: str, quantity: int = 1) -> Optional[dict]:
        """Log medicine consumption for AI prediction."""
        if med_id in self.medicines:
            med = self.medicines[med_id]
            med['consumption_log'].append({
                'date': datetime.now().isoformat(),
                'quantity': quantity
            })
            med['quantity'] = max(0, med['quantity'] - quantity)
            return med
        return None

    # ─────────────────────────────────────
    # Dashboard Analytics
    # ─────────────────────────────────────

    def get_dashboard_stats(self) -> dict:
        """Get summary statistics for the dashboard."""
        meds = self.get_all_medicines()
        total = len(meds)

        expired = [m for m in meds if m.get('status') == 'expired']
        critical = [m for m in meds if m.get('status') == 'critical']
        warning = [m for m in meds if m.get('status') == 'warning']
        safe = [m for m in meds if m.get('status') == 'safe']
        donated = [m for m in meds if m.get('donated')]

        # Calculate waste value
        waste_value = sum(
            self._parse_price(m.get('mrp', '₹0'))
            for m in expired
        )

        return {
            'total_medicines': total,
            'expired_count': len(expired),
            'critical_count': len(critical),
            'warning_count': len(warning),
            'safe_count': len(safe),
            'donated_count': len(donated),
            'estimated_waste_value': f"₹{waste_value:,.0f}",
            'expiring_this_week': len(critical),
            'expiring_this_month': len(warning) + len(critical),
            'categories': self._get_category_breakdown(meds),
        }

    def get_expiry_calendar(self) -> list:
        """Get medicines organized by expiry month for calendar view."""
        meds = self.get_all_medicines()
        calendar = {}
        for med in meds:
            if med.get('expiry_date'):
                month_key = med['expiry_date'][:7]  # YYYY-MM
                if month_key not in calendar:
                    calendar[month_key] = []
                calendar[month_key].append(med)
        return [{'month': k, 'medicines': v} for k, v in sorted(calendar.items())]

    # ─────────────────────────────────────
    # Donation Operations
    # ─────────────────────────────────────

    def mark_for_donation(self, med_id: str, ngo_id: str) -> Optional[dict]:
        """Mark a medicine for donation to an NGO."""
        if med_id in self.medicines:
            med = self.medicines[med_id]
            if med.get('status') in ('safe', 'soon', 'warning') and not med.get('donated'):
                med['donated'] = True
                med['donation_ngo'] = ngo_id
                med['donation_date'] = datetime.now().isoformat()
                self.donation_history.append({
                    'medicine_id': med_id,
                    'medicine_name': med['name'],
                    'ngo_id': ngo_id,
                    'date': datetime.now().isoformat()
                })
                return med
        return None

    def get_donatable_medicines(self) -> list:
        """Get medicines eligible for donation (valid, not expired)."""
        meds = self.get_all_medicines()
        return [
            m for m in meds
            if m.get('status') in ('safe', 'soon', 'warning')
            and not m.get('donated')
            and m.get('days_until_expiry', 0) > 30
        ]

    # ─────────────────────────────────────
    # Family Sharing
    # ─────────────────────────────────────

    def create_family(self, family_name: str, creator: str) -> dict:
        family_id = f"fam_{str(uuid.uuid4())[:6]}"
        family = {
            'id': family_id,
            'name': family_name,
            'members': [creator],
            'created_date': datetime.now().isoformat(),
            'invite_code': str(uuid.uuid4())[:6].upper()
        }
        self.families[family_id] = family
        return family

    def join_family(self, invite_code: str, member: str) -> Optional[dict]:
        for fam in self.families.values():
            if fam['invite_code'] == invite_code:
                if member not in fam['members']:
                    fam['members'].append(member)
                return fam
        return None

    # ─────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────

    def _get_status(self, days: int) -> str:
        if days < 0:
            return 'expired'
        elif days <= 7:
            return 'critical'
        elif days <= 30:
            return 'warning'
        elif days <= 90:
            return 'soon'
        return 'safe'

    def _categorize_medicine(self, name: str) -> str:
        name_lower = name.lower() if name else ''
        categories = {
            'Pain Relief': ['dolo', 'paracetamol', 'ibuprofen', 'combiflam', 'diclofenac', 'aspirin'],
            'Antibiotics': ['azithral', 'amoxicillin', 'augmentin', 'azee', 'ofloxacin', 'ciprofloxacin', 'metronidazole'],
            'Antacids & GI': ['pan-d', 'pantoprazole', 'omeprazole', 'ranitidine', 'rabeprazole'],
            'Vitamins & Supplements': ['shelcal', 'vitamin', 'b-complex', 'calcium', 'iron', 'zinc', 'limcee', 'becosules'],
            'Allergy & Cold': ['cetirizine', 'montelukast', 'sinarest', 'benadryl', 'allegra', 'levocetrizine'],
            'Cardiac': ['ecosprin', 'atorvastatin', 'telmisartan', 'amlodipine', 'losartan', 'atenolol'],
            'Diabetes': ['metformin', 'glimepiride'],
        }
        for category, keywords in categories.items():
            if any(kw in name_lower for kw in keywords):
                return category
        return 'Other'

    def _parse_price(self, price_str: str) -> float:
        try:
            cleaned = price_str.replace('₹', '').replace(',', '').strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return 0.0

    def _get_category_breakdown(self, meds: list) -> dict:
        cats = {}
        for m in meds:
            cat = m.get('category', 'Other')
            cats[cat] = cats.get(cat, 0) + 1
        return cats

    # ─────────────────────────────────────
    # Demo Data
    # ─────────────────────────────────────

    def _seed_demo_data(self):
        """Pre-populate with realistic Indian household medicine data."""
        demo_medicines = [
            {
                'medicine_name': 'Dolo 650',
                'expiry_date': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
                'expiry_display': 'April 2026',
                'days_until_expiry': 5,
                'status': 'critical',
                'batch_number': 'DL24A1087',
                'mfg_date': 'March 2024',
                'mrp': '₹35',
                'quantity': 8,
            },
            {
                'medicine_name': 'Azithral 500',
                'expiry_date': (datetime.now() + timedelta(days=22)).strftime('%Y-%m-%d'),
                'expiry_display': 'April 2026',
                'days_until_expiry': 22,
                'status': 'warning',
                'batch_number': 'AZ23B0492',
                'mfg_date': 'June 2023',
                'mrp': '₹120',
                'quantity': 3,
            },
            {
                'medicine_name': 'Pan-D',
                'expiry_date': (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d'),
                'expiry_display': 'October 2026',
                'days_until_expiry': 180,
                'status': 'safe',
                'batch_number': 'PD24C3321',
                'mfg_date': 'January 2024',
                'mrp': '₹95',
                'quantity': 15,
            },
            {
                'medicine_name': 'Shelcal 500',
                'expiry_date': (datetime.now() + timedelta(days=400)).strftime('%Y-%m-%d'),
                'expiry_display': 'May 2027',
                'days_until_expiry': 400,
                'status': 'safe',
                'batch_number': 'SH24D1100',
                'mfg_date': 'May 2024',
                'mrp': '₹165',
                'quantity': 30,
            },
            {
                'medicine_name': 'Ecosprin 75',
                'expiry_date': (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d'),
                'expiry_display': 'March 2026',
                'days_until_expiry': -15,
                'status': 'expired',
                'batch_number': 'EC23A0876',
                'mfg_date': 'September 2023',
                'mrp': '₹12',
                'quantity': 20,
            },
            {
                'medicine_name': 'Combiflam',
                'expiry_date': (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d'),
                'expiry_display': 'June 2026',
                'days_until_expiry': 60,
                'status': 'soon',
                'batch_number': 'CF24B2233',
                'mfg_date': 'February 2024',
                'mrp': '₹42',
                'quantity': 6,
            },
            {
                'medicine_name': 'Crocin Advance',
                'expiry_date': (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d'),
                'expiry_display': 'February 2026',
                'days_until_expiry': -45,
                'status': 'expired',
                'batch_number': 'CR23C1190',
                'mfg_date': 'August 2023',
                'mrp': '₹28',
                'quantity': 12,
            },
            {
                'medicine_name': 'Becosules Z',
                'expiry_date': (datetime.now() + timedelta(days=300)).strftime('%Y-%m-%d'),
                'expiry_display': 'January 2027',
                'days_until_expiry': 300,
                'status': 'safe',
                'batch_number': 'BZ24A0550',
                'mfg_date': 'April 2024',
                'mrp': '₹52',
                'quantity': 20,
            },
        ]

        for med in demo_medicines:
            self.add_medicine(med)
