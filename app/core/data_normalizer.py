import re
from typing import Optional
from datetime import datetime
import phonenumbers
import unicodedata

# Phone number normalization (international format)
def normalize_phone(phone: str, default_region: str = "IN") -> str:
    if not phone or not phone.strip():
        return ""
    phone = phone.strip()
    # 1. If starts with '+', parse as international
    if phone.startswith('+'):
        try:
            parsed = phonenumbers.parse(phone, None)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            pass
    # 2. If 10 digits and no '+', use default_region to determine country code
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        try:
            parsed = phonenumbers.parse(digits, default_region)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            pass
    # 3. Otherwise, try parsing with default region and accept any valid number
    try:
        parsed = phonenumbers.parse(phone, default_region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        pass
    # 4. Try parsing just the digits with default region
    try:
        parsed = phonenumbers.parse(digits, default_region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        pass
    return ""

# Email normalization (lowercase, strip spaces)
def normalize_email(email: str) -> str:
    email = email.strip().lower()
    # Simple regex for email validation
    if not email:
        return ""
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        return ""
    return email

# Business name normalization (strip, title case, remove special chars)
def normalize_business_name(name: str) -> str:
    name = name.strip()
    name = unicodedata.normalize('NFKD', name)
    name = re.sub(r'[^\w\s\-&]', '', name)
    return name.title()

# Address normalization (strip, collapse whitespace)
def normalize_address(address: str) -> str:
    address = address.strip()
    address = re.sub(r'\s+', ' ', address)
    return address

# Currency normalization (extract value and currency, convert to float)
def normalize_currency(text: str) -> float:
    if not text or not text.strip():
        return 0.0
    match = re.search(r'(\$|USD|EUR|GBP|INR|CAD|AUD)?\s?([\d,.]+)', text)
    if match:
        value = match.group(2).replace(',', '')
        try:
            return float(value)
        except Exception:
            return 0.0
    return 0.0

# Date/time normalization (parse to ISO format)
def normalize_date(text: str) -> Optional[str]:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%b %d, %Y", "%B %d, %Y"):
        try:
            dt = datetime.strptime(text.strip(), fmt)
            return dt.isoformat()
        except Exception:
            continue
    return None 