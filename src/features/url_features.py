import re
import math
import tldextract
from urllib.parse import urlparse

def get_entropy(text):
    if not text:
        return 0
    probs = [text.count(c) / len(text) for c in set(text)]
    return -sum(p * math.log2(p) for p in probs)

def extract_url_features(url):
    """
    Extracts numerical features from a URL string.
    Returns a dictionary of features.
    """
    if not url:
        return None
    
    # Ensure protocol exists for parsing
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
        
    parsed = urlparse(url)
    ext = tldextract.extract(url)
    
    domain = ext.domain + '.' + ext.suffix
    path = parsed.path
    query = parsed.query
    
    features = {
        'url_length': len(url),
        'domain_length': len(domain),
        'num_dots': url.count('.'),
        'num_hyphens': url.count('-'),
        'num_at_symbols': url.count('@'),
        'num_slashes': url.count('/'),
        'num_subdomains': len(ext.subdomain.split('.')) if ext.subdomain else 0,
        'has_ip_address': 1 if re.match(r'\d+\.\d+\.\d+\.\d+', ext.domain) else 0,
        'is_https': 1 if parsed.scheme == 'https' else 0,
        'num_digits': sum(c.isdigit() for c in url),
        'domain_digit_count': sum(c.isdigit() for c in ext.domain), # NEW: Specifically for typosquatting
        'digit_ratio': sum(c.isdigit() for c in url) / len(url) if len(url) > 0 else 0,
        'url_entropy': get_entropy(url),
        'domain_entropy': get_entropy(domain),
        'has_port': 1 if parsed.port else 0,
        'num_params': len(query.split('&')) if query else 0,
        'path_length': len(path),
        'special_char_count': len(re.findall(r'[%=?&]', url)),
        'is_suspicious_tld': 1 if ext.suffix in ['xyz', 'top', 'online', 'co', 'biz'] else 0, # NEW: TLD Reputation
        'lookalike_count': len(re.findall(r'[10|!@$]', url)), # NEW: Potential character substitutions
        'has_homoglyphs': 1 if re.search(r'[1!|][a-z]|[a-z][1!|]', url) else 0 # NEW: Patterns like 'pa1' or 'g00gle'
    }
    
    return features

if __name__ == "__main__":
    test_url = "https://secure.paypal.com-login.cgi?ref=123"
    print(f"Features for {test_url}:")
    import json
    print(json.dumps(extract_url_features(test_url), indent=4))
