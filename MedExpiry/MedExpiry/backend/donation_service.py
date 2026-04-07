# backend/donation_service.py
"""
Donation service with hardcoded NGO data and Google Maps integration.
"""


# Dummy NGO / Drop-off location data (Indian cities)
NGO_DATABASE = [
    {
        'id': 'ngo_001',
        'name': 'Goonj Foundation',
        'type': 'NGO',
        'address': 'J-93, Sarita Vihar, New Delhi - 110076',
        'lat': 28.5310,
        'lng': 77.2900,
        'city': 'New Delhi',
        'phone': '+91-11-2694-8731',
        'email': 'info@goonj.org',
        'website': 'https://goonj.org',
        'accepts': ['Tablets', 'Capsules', 'Syrups', 'Supplements'],
        'timing': 'Mon–Sat: 10:00 AM – 5:00 PM',
        'description': 'Largest urban-rural redistribution charity. Accepts valid medicines for rural healthcare camps.',
        'verified': True,
        'rating': 4.8,
        'image': 'goonj.jpg'
    },
    {
        'id': 'ngo_002',
        'name': 'Mercy Foundation Hospital',
        'type': 'Hospital',
        'address': '12, MG Road, Camp, Pune - 411001',
        'lat': 18.5196,
        'lng': 73.8744,
        'city': 'Pune',
        'phone': '+91-20-2633-5000',
        'email': 'donate@mercyfoundation.in',
        'website': '#',
        'accepts': ['Tablets', 'Capsules', 'Injectables', 'Surgical'],
        'timing': 'Mon–Fri: 9:00 AM – 6:00 PM',
        'description': 'Free hospital for underprivileged. Distributes donated medicines to patients.',
        'verified': True,
        'rating': 4.6,
        'image': 'mercy.jpg'
    },
    {
        'id': 'ngo_003',
        'name': 'Share Medical Supplies',
        'type': 'Collection Center',
        'address': '45, Residency Road, Bangalore - 560025',
        'lat': 12.9731,
        'lng': 77.6018,
        'city': 'Bangalore',
        'phone': '+91-80-2558-1234',
        'email': 'share@sms.org.in',
        'website': '#',
        'accepts': ['All valid medicines', 'First Aid', 'OTC'],
        'timing': 'All days: 8:00 AM – 8:00 PM',
        'description': 'Community medicine bank. Collects, verifies, and redistributes unused medicines.',
        'verified': True,
        'rating': 4.5,
        'image': 'share.jpg'
    },
    {
        'id': 'ngo_004',
        'name': 'MERCY Mission India',
        'type': 'NGO',
        'address': '78, Anna Salai, Chennai - 600002',
        'lat': 13.0604,
        'lng': 80.2496,
        'city': 'Chennai',
        'phone': '+91-44-2852-9000',
        'email': 'contact@mercymission.in',
        'website': '#',
        'accepts': ['Tablets', 'Capsules', 'Supplements', 'OTC'],
        'timing': 'Mon–Sat: 9:30 AM – 5:30 PM',
        'description': 'Collects unused medicines and distributes in free medical camps across Tamil Nadu.',
        'verified': True,
        'rating': 4.7,
        'image': 'mercy_mission.jpg'
    },
    {
        'id': 'ngo_005',
        'name': 'Red Cross Medicine Bank',
        'type': 'Government',
        'address': '1, Red Cross Road, Bandra, Mumbai - 400050',
        'lat': 19.0596,
        'lng': 72.8295,
        'city': 'Mumbai',
        'phone': '+91-22-2642-1234',
        'email': 'mumbai@redcross.org',
        'website': 'https://indianredcross.org',
        'accepts': ['All categories'],
        'timing': 'Mon–Fri: 10:00 AM – 4:00 PM',
        'description': 'Indian Red Cross medicine collection drive. Government-verified drop-off center.',
        'verified': True,
        'rating': 4.9,
        'image': 'redcross.jpg'
    },
    {
        'id': 'ngo_006',
        'name': 'Jan Aushadhi Kendra - Donation Center',
        'type': 'Government',
        'address': 'Sector 21, Noida - 201301',
        'lat': 28.5812,
        'lng': 77.3181,
        'city': 'Noida',
        'phone': '+91-120-234-5678',
        'email': 'donate@janaushadhi.gov.in',
        'website': '#',
        'accepts': ['Generic medicines', 'OTC', 'Supplements'],
        'timing': 'Mon–Sat: 8:00 AM – 9:00 PM',
        'description': 'Government affordable medicine scheme. Accepts valid donated medicines for redistribution.',
        'verified': True,
        'rating': 4.4,
        'image': 'janaushadhi.jpg'
    },
]


class DonationService:

    def get_all_ngos(self) -> list:
        return NGO_DATABASE

    def get_ngos_by_city(self, city: str) -> list:
        return [n for n in NGO_DATABASE if n['city'].lower() == city.lower()]

    def get_nearby_ngos(self, lat: float, lng: float, radius_km: float = 50) -> list:
        """Find NGOs within radius using Haversine distance."""
        import math
        nearby = []
        for ngo in NGO_DATABASE:
            d = self._haversine(lat, lng, ngo['lat'], ngo['lng'])
            if d <= radius_km:
                ngo_copy = dict(ngo)
                ngo_copy['distance_km'] = round(d, 1)
                nearby.append(ngo_copy)
        return sorted(nearby, key=lambda x: x['distance_km'])

    def get_ngo_by_id(self, ngo_id: str) -> dict:
        for ngo in NGO_DATABASE:
            if ngo['id'] == ngo_id:
                return ngo
        return None

    def _haversine(self, lat1, lon1, lat2, lon2):
        import math
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        return R * c
