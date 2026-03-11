import re
from urllib.parse import urlparse
import whois
from datetime import datetime


def extract_features(url):
    hostname = urlparse(url).netloc
    path = urlparse(url).path

    # 1. Structural Features
    features = [
        len(url),
        url.count('.'),
        url.count('-'),
        1 if hostname.replace('.', '').isdigit() else 0,  # IP in URL
        url.count('@'),
        url.count('//'),
    ]

    # 2. Domain Age Feature (Critical for New Scams)
    try:
        domain_info = whois.whois(hostname)
        creation_date = domain_info.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]

        if creation_date:
            age_days = (datetime.now() - creation_date).days
            # Feature: 1 if domain is very new (< 30 days), else 0
            features.append(1 if age_days < 30 else 0)
        else:
            features.append(1)  # Treat unknown as suspicious
    except:
        features.append(1)  # Treat errors as suspicious

    return features