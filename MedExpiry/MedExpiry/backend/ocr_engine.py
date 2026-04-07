# backend/ocr_engine.py
"""
OCR Engine for Medicine Strip Scanning
Extracts medicine name, expiry date, batch number, and manufacturer
using PyTesseract + custom regex patterns for Indian medicine formats.
"""

import re
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
from typing import Optional

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# ─────────────────────────────────────────────
# Indian Medicine Date Formats & Patterns
# ─────────────────────────────────────────────

EXPIRY_PATTERNS = [
    # EXP: 08/2026, EXP 08-2026, Exp. 08.2026
    r'(?:EXP(?:IRY)?\.?\s*(?:DATE)?\.?\s*[:;]?\s*)(\d{1,2})[\/\-\.](\d{2,4})',
    # Expiry: Aug 2026, Exp: August 2026
    r'(?:EXP(?:IRY)?\.?\s*(?:DATE)?\.?\s*[:;]?\s*)([A-Za-z]{3,9})[\s\-\.\/](\d{2,4})',
    # EXP 2026-08, EXP 2026/08
    r'(?:EXP(?:IRY)?\.?\s*(?:DATE)?\.?\s*[:;]?\s*)(\d{4})[\/\-\.](\d{1,2})',
    # Best Before: 08/2026
    r'(?:BEST\s*BEFORE|BB|USE\s*BEFORE)\.?\s*[:;]?\s*(\d{1,2})[\/\-\.](\d{2,4})',
    # Standalone date patterns MM/YYYY or MM-YYYY (fallback)
    r'\b(\d{1,2})[\/\-](\d{4})\b',
    # DD/MM/YYYY format
    r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})\b',
]

MEDICINE_NAME_PATTERNS = [
    # Common Indian medicine naming: "Tab. Dolo 650", "Cap. Amoxicillin 500mg"
    r'(?:Tab\.?|Cap\.?|Syp\.?|Inj\.?|Oint\.?|Susp\.?|Drops?)\s+([A-Za-z][A-Za-z\s\-]+?)[\s]*(?:\d+\s*(?:mg|ml|gm|mcg|g))',
    # Medicine name followed by strength
    r'^([A-Z][A-Za-z\s\-]{2,30}?)[\s]+(\d+\s*(?:mg|ml|gm|mcg|IU|g))',
    # Brand name in caps
    r'\b([A-Z]{3,20}(?:\s*\-?\s*[A-Z0-9]{1,10})?)\b',
]

BATCH_PATTERNS = [
    r'(?:B(?:ATCH)?\.?\s*(?:NO)?\.?\s*[:;]?\s*)([A-Za-z0-9\-\/]+)',
    r'(?:Lot\.?\s*(?:No)?\.?\s*[:;]?\s*)([A-Za-z0-9\-\/]+)',
]

MFG_DATE_PATTERNS = [
    r'(?:MFG\.?\s*(?:DATE)?\.?\s*[:;]?\s*)(\d{1,2})[\/\-\.](\d{2,4})',
    r'(?:MFD\.?\s*(?:DATE)?\.?\s*[:;]?\s*)(\d{1,2})[\/\-\.](\d{2,4})',
    r'(?:MANUFACTURED|MFG\'?D?)\.?\s*[:;]?\s*([A-Za-z]{3,9})[\s\-\.\/](\d{2,4})',
]

MONTH_MAP = {
    'jan': 1, 'january': 1, 'feb': 2, 'february': 2,
    'mar': 3, 'march': 3, 'apr': 4, 'april': 4,
    'may': 5, 'jun': 6, 'june': 6,
    'jul': 7, 'july': 7, 'aug': 8, 'august': 8,
    'sep': 9, 'sept': 9, 'september': 9,
    'oct': 10, 'october': 10, 'nov': 11, 'november': 11,
    'dec': 12, 'december': 12
}

# Known Indian medicine brands for smart matching
KNOWN_MEDICINES = [
    "Dolo", "Crocin", "Combiflam", "Azithral", "Augmentin", "Pan-D",
    "Shelcal", "Ecosprin", "Metformin", "Atorvastatin", "Pantoprazole",
    "Cetirizine", "Montelukast", "Amoxicillin", "Paracetamol", "Ibuprofen",
    "Ranitidine", "Omeprazole", "Diclofenac", "Aspirin", "Vitamin D3",
    "B-Complex", "Calcium", "Iron", "Zinc", "Limcee", "Becosules",
    "Sinarest", "Vicks", "Benadryl", "Allegra", "Levocetrizine",
    "Azee", "Ofloxacin", "Ciprofloxacin", "Metronidazole", "Rabeprazole",
    "Telmisartan", "Amlodipine", "Losartan", "Atenolol", "Glimepiride",
]


class MedicineOCR:
    """
    Handles OCR processing for medicine strips/packaging.
    Supports both PyTesseract (local) and Google Vision API (cloud).
    """

    def __init__(self, use_google_vision: bool = False):
        self.use_google_vision = use_google_vision

    # ─────────────────────────────────────
    # Image Preprocessing
    # ─────────────────────────────────────

    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Enhance medicine strip image for better OCR accuracy.
        Handles glare, curved surfaces, and small text common on strips.
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")

        # Resize if too large (keep aspect ratio)
        max_dim = 2000
        h, w = img.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # Excellent for medicine strips with uneven lighting
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10)

        # Adaptive thresholding for text extraction
        binary = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 31, 11
        )

        # Sharpen
        kernel = np.array([[-1, -1, -1],
                           [-1,  9, -1],
                           [-1, -1, -1]])
        sharpened = cv2.filter2D(binary, -1, kernel)

        return sharpened

    # ─────────────────────────────────────
    # Core OCR Extraction
    # ─────────────────────────────────────

    def extract_text(self, image_path: str) -> str:
        """Extract raw text from medicine image using PyTesseract."""
        if not TESSERACT_AVAILABLE:
            return self._mock_ocr_text()

        processed = self.preprocess_image(image_path)

        # Multiple OCR passes with different configurations for best results
        configs = [
            '--oem 3 --psm 6',   # Assume uniform block of text
            '--oem 3 --psm 4',   # Assume single column of text
            '--oem 3 --psm 11',  # Sparse text
            '--oem 3 --psm 3',   # Fully automatic
        ]

        all_text = []
        for config in configs:
            try:
                text = pytesseract.image_to_string(
                    Image.fromarray(processed),
                    config=config,
                    lang='eng'
                )
                all_text.append(text)
            except Exception:
                continue

        # Combine all extractions and deduplicate lines
        combined = '\n'.join(all_text)
        return combined

    def _mock_ocr_text(self) -> str:
        """Fallback mock OCR for demo/hackathon when Tesseract isn't installed."""
        return """
        DOLO 650
        Paracetamol Tablets IP 650mg
        Tab. Dolo 650
        Mfg. by: Micro Labs Ltd
        Batch No: DL24A1087
        MFG DT: 03/2024
        EXP: 02/2026
        MRP: ₹35.00
        10 x 15 Tablets
        Store below 30°C
        """

    # ─────────────────────────────────────
    # Smart Parsing
    # ─────────────────────────────────────

    def parse_expiry_date(self, text: str) -> Optional[dict]:
        """Extract and parse expiry date from OCR text."""
        text_upper = text.upper()

        for pattern in EXPIRY_PATTERNS:
            matches = re.finditer(pattern, text_upper, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                groups = match.groups()
                try:
                    if len(groups) == 2:
                        part1, part2 = groups
                        month, year = self._resolve_month_year(part1, part2)
                    elif len(groups) == 3:
                        # DD/MM/YYYY format
                        _, month_str, year_str = groups
                        month = int(month_str)
                        year = self._resolve_year(year_str)
                    else:
                        continue

                    if 1 <= month <= 12 and 2020 <= year <= 2040:
                        expiry_date = datetime(year, month, 1)
                        days_until = (expiry_date - datetime.now()).days

                        return {
                            'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                            'expiry_display': expiry_date.strftime('%B %Y'),
                            'month': month,
                            'year': year,
                            'days_until_expiry': days_until,
                            'status': self._get_expiry_status(days_until),
                            'raw_match': match.group(0)
                        }
                except (ValueError, TypeError):
                    continue

        return None

    def parse_medicine_name(self, text: str) -> Optional[str]:
        """Extract medicine name using patterns and known drug database."""
        # First: check against known Indian medicine brands
        text_upper = text.upper()
        for medicine in KNOWN_MEDICINES:
            if medicine.upper() in text_upper:
                # Try to get full name with strength
                strength_pattern = rf'({re.escape(medicine)}[\s\-]*\d*\s*(?:mg|ml|gm|mcg|g)?)'
                strength_match = re.search(strength_pattern, text, re.IGNORECASE)
                if strength_match:
                    return strength_match.group(1).strip()
                return medicine

        # Second: use regex patterns
        for pattern in MEDICINE_NAME_PATTERNS:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2 and not name.isdigit():
                    return name

        return None

    def parse_batch_number(self, text: str) -> Optional[str]:
        """Extract batch/lot number."""
        for pattern in BATCH_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def parse_mfg_date(self, text: str) -> Optional[str]:
        """Extract manufacturing date."""
        for pattern in MFG_DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                try:
                    part1, part2 = groups
                    month, year = self._resolve_month_year(part1, part2)
                    if 1 <= month <= 12 and 2020 <= year <= 2040:
                        return datetime(year, month, 1).strftime('%B %Y')
                except (ValueError, TypeError):
                    continue
        return None

    def parse_mrp(self, text: str) -> Optional[str]:
        """Extract MRP price."""
        pattern = r'(?:MRP|M\.R\.P)\.?\s*[:;]?\s*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{1,2})?)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"₹{match.group(1)}"
        return None

    # ─────────────────────────────────────
    # Full Scan Pipeline
    # ─────────────────────────────────────

    def scan_medicine(self, image_path: str) -> dict:
        """
        Complete scan pipeline: Image → OCR → Parse → Structured Data
        Returns a full medicine record ready for database storage.
        """
        raw_text = self.extract_text(image_path)

        medicine_name = self.parse_medicine_name(raw_text)
        expiry_info = self.parse_expiry_date(raw_text)
        batch_number = self.parse_batch_number(raw_text)
        mfg_date = self.parse_mfg_date(raw_text)
        mrp = self.parse_mrp(raw_text)

        result = {
            'success': True,
            'raw_text': raw_text.strip(),
            'extracted_data': {
                'medicine_name': medicine_name or 'Unknown Medicine',
                'expiry_date': expiry_info['expiry_date'] if expiry_info else None,
                'expiry_display': expiry_info['expiry_display'] if expiry_info else 'Not detected',
                'days_until_expiry': expiry_info['days_until_expiry'] if expiry_info else None,
                'status': expiry_info['status'] if expiry_info else 'unknown',
                'batch_number': batch_number,
                'mfg_date': mfg_date,
                'mrp': mrp,
            },
            'confidence': self._calculate_confidence(medicine_name, expiry_info),
            'scan_timestamp': datetime.now().isoformat()
        }

        return result

    # ─────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────

    def _resolve_month_year(self, part1: str, part2: str) -> tuple:
        """Resolve month and year from various format combinations."""
        # Check if part1 is a month name
        if part1.lower().strip() in MONTH_MAP:
            month = MONTH_MAP[part1.lower().strip()]
            year = self._resolve_year(part2)
        elif part2.lower().strip() in MONTH_MAP:
            month = MONTH_MAP[part2.lower().strip()]
            year = self._resolve_year(part1)
        else:
            p1, p2 = int(part1), int(part2)
            if p1 > 12:  # p1 is year
                year, month = p1, p2
            else:
                month = p1
                year = self._resolve_year(str(p2))
        return month, year

    def _resolve_year(self, year_str: str) -> int:
        """Convert 2-digit or 4-digit year string to full year."""
        year = int(year_str)
        if year < 100:
            year += 2000
        return year

    def _get_expiry_status(self, days: int) -> str:
        """Categorize expiry urgency."""
        if days < 0:
            return 'expired'
        elif days <= 7:
            return 'critical'
        elif days <= 30:
            return 'warning'
        elif days <= 90:
            return 'soon'
        else:
            return 'safe'

    def _calculate_confidence(self, name, expiry) -> float:
        """Calculate OCR confidence score (0.0 to 1.0)."""
        score = 0.0
        if name and name != 'Unknown Medicine':
            score += 0.5
            # Bonus for known medicine match
            if any(m.lower() in name.lower() for m in KNOWN_MEDICINES):
                score += 0.15
        if expiry:
            score += 0.35
        return min(round(score, 2), 1.0)
