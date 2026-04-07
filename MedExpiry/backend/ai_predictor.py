# backend/ai_predictor.py
"""
AI-powered consumption prediction and refill reminders.
Uses simple statistical analysis for hackathon; upgradeable to ML models.
"""

from datetime import datetime, timedelta
from typing import Optional
import math


class ConsumptionPredictor:
    """
    Predicts medicine consumption patterns and suggests refill timing.
    """

    def predict_refill(self, medicine: dict) -> Optional[dict]:
        """
        Analyze consumption log and predict when medicine will run out.
        """
        logs = medicine.get('consumption_log', [])
        quantity = medicine.get('quantity', 0)
        name = medicine.get('name', 'Unknown')

        if len(logs) < 2:
            # Not enough data — use heuristic based on medicine type
            return self._heuristic_prediction(medicine)

        # Calculate average daily consumption
        sorted_logs = sorted(logs, key=lambda x: x['date'])
        first_date = datetime.fromisoformat(sorted_logs[0]['date'])
        last_date = datetime.fromisoformat(sorted_logs[-1]['date'])
        total_consumed = sum(l['quantity'] for l in sorted_logs)

        days_span = max((last_date - first_date).days, 1)
        daily_rate = total_consumed / days_span

        if daily_rate <= 0:
            return None

        # Predict days until stock runs out
        days_remaining = math.ceil(quantity / daily_rate) if quantity > 0 else 0
        run_out_date = datetime.now() + timedelta(days=days_remaining)

        # Suggest refill date (7 days before running out)
        refill_date = run_out_date - timedelta(days=7)

        return {
            'medicine_name': name,
            'current_quantity': quantity,
            'daily_consumption_rate': round(daily_rate, 2),
            'estimated_days_remaining': days_remaining,
            'estimated_run_out_date': run_out_date.strftime('%Y-%m-%d'),
            'suggested_refill_date': refill_date.strftime('%Y-%m-%d'),
            'refill_urgent': days_remaining <= 7,
            'consumption_trend': self._analyze_trend(sorted_logs),
            'prediction_confidence': min(len(logs) / 10, 1.0),
        }

    def _heuristic_prediction(self, medicine: dict) -> dict:
        """Fallback prediction using common medicine usage patterns."""
        name = medicine.get('name', '').lower()
        quantity = medicine.get('quantity', 0)
        category = medicine.get('category', 'Other')

        # Average daily doses by category
        daily_rates = {
            'Pain Relief': 1.5,       # 1-2 tablets/day
            'Antibiotics': 2.0,       # Course-based, 2/day
            'Antacids & GI': 1.0,     # 1/day usually
            'Vitamins & Supplements': 1.0,  # 1/day
            'Allergy & Cold': 1.0,    # 1/day
            'Cardiac': 1.0,           # 1/day chronic
            'Diabetes': 2.0,          # 2/day chronic
            'Other': 1.0,
        }

        daily_rate = daily_rates.get(category, 1.0)
        days_remaining = math.ceil(quantity / daily_rate) if quantity > 0 else 0
        run_out_date = datetime.now() + timedelta(days=days_remaining)
        refill_date = run_out_date - timedelta(days=7)

        return {
            'medicine_name': medicine.get('name', 'Unknown'),
            'current_quantity': quantity,
            'daily_consumption_rate': daily_rate,
            'estimated_days_remaining': days_remaining,
            'estimated_run_out_date': run_out_date.strftime('%Y-%m-%d'),
            'suggested_refill_date': refill_date.strftime('%Y-%m-%d'),
            'refill_urgent': days_remaining <= 7,
            'consumption_trend': 'estimated',
            'prediction_confidence': 0.3,
            'note': 'Based on average usage patterns. Log consumption for better predictions.'
        }

    def _analyze_trend(self, sorted_logs: list) -> str:
        """Determine if consumption is increasing, decreasing, or stable."""
        if len(sorted_logs) < 4:
            return 'insufficient_data'

        mid = len(sorted_logs) // 2
        first_half = sum(l['quantity'] for l in sorted_logs[:mid])
        second_half = sum(l['quantity'] for l in sorted_logs[mid:])

        ratio = second_half / max(first_half, 1)
        if ratio > 1.2:
            return 'increasing'
        elif ratio < 0.8:
            return 'decreasing'
        return 'stable'

    def get_all_predictions(self, medicines: list) -> list:
        """Get refill predictions for all medicines."""
        predictions = []
        for med in medicines:
            if med.get('status') not in ('expired',) and med.get('quantity', 0) > 0:
                pred = self.predict_refill(med)
                if pred:
                    predictions.append(pred)
        return sorted(predictions, key=lambda x: x.get('estimated_days_remaining', 9999))

    def get_smart_alerts(self, medicines: list) -> list:
        """Generate intelligent alerts based on all data."""
        alerts = []

        for med in medicines:
            # Expiry alerts
            days = med.get('days_until_expiry', 9999)
            if med.get('status') == 'expired':
                alerts.append({
                    'type': 'expired',
                    'severity': 'danger',
                    'icon': '🚫',
                    'title': f"{med['name']} has EXPIRED",
                    'message': f"Expired {abs(days)} days ago. Dispose safely or check donation eligibility.",
                    'medicine_id': med['id'],
                    'action': 'dispose'
                })
            elif med.get('status') == 'critical':
                alerts.append({
                    'type': 'expiring_soon',
                    'severity': 'danger',
                    'icon': '🔴',
                    'title': f"{med['name']} expires in {days} days!",
                    'message': f"Use before it expires or donate to a nearby NGO.",
                    'medicine_id': med['id'],
                    'action': 'use_or_donate'
                })
            elif med.get('status') == 'warning':
                alerts.append({
                    'type': 'expiring_month',
                    'severity': 'warning',
                    'icon': '🟡',
                    'title': f"{med['name']} expires in {days} days",
                    'message': f"Consider using or donating within this month.",
                    'medicine_id': med['id'],
                    'action': 'plan'
                })

            # Low stock alerts
            if med.get('quantity', 0) <= 3 and med.get('status') not in ('expired',):
                alerts.append({
                    'type': 'low_stock',
                    'severity': 'info',
                    'icon': '💊',
                    'title': f"Low stock: {med['name']}",
                    'message': f"Only {med['quantity']} left. Consider refilling.",
                    'medicine_id': med['id'],
                    'action': 'refill'
                })

        return sorted(alerts, key=lambda x: {'danger': 0, 'warning': 1, 'info': 2}.get(x['severity'], 3))
