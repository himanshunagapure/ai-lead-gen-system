import os
import json
import gzip
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional

BASE_DATA_DIR = "data"
RAW_HTML_DIR = os.path.join(BASE_DATA_DIR, "raw_html")
EXTRACTED_DIR = os.path.join(BASE_DATA_DIR, "extracted")
LOGS_DIR = os.path.join(BASE_DATA_DIR, "logs")
EXPORTS_DIR = os.path.join(BASE_DATA_DIR, "exports")

for d in [RAW_HTML_DIR, EXTRACTED_DIR, LOGS_DIR, EXPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

def timestamped_filename(prefix: str, ext: str = "json") -> str:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.{ext}"

def save_raw_html(url: str, html: str) -> str:
    fname = timestamped_filename("raw", "html")
    path = os.path.join(RAW_HTML_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path

def save_extracted_data(data: Dict[str, Any], prefix: str = "extracted") -> str:
    fname = timestamped_filename(prefix, "json")
    path = os.path.join(EXTRACTED_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path

def compress_file(path: str) -> str:
    gz_path = path + ".gz"
    with open(path, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
        f_out.writelines(f_in)
    return gz_path

def file_checksum(path: str, algo: str = "sha256") -> str:
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest() 