from flask import Flask, request, jsonify
import requests
import xml.etree.ElementTree as ET
import io
import logging
import json
from google.cloud import storage
from urllib.parse import urlparse
import re
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

storage_client = storage.Client()
BUCKET_NAME = "xml-parsed"

def extract_accession_from_url(url):
    match = re.search(r"edgar/data/\d+/(\d{18})", url)
    return match.group(1) if match else "unknownaccession"

@app.route("/", methods=["POST"])
def parse_single_xml():
    data = request.get_json()
    logging.info(f"Payload received: {data}")
    url = data.get("url")
    cik = data.get("cik") or "unknown"
    
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    try:
        accession = extract_accession_from_url(url)
        filename = f"{cik}_{accession}.json"

        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)

        if blob.exists():
            logging.info(f"File {filename} already exists. Skipping.")
            return jsonify({"status": "exists", "filename": filename})

        headers = {"User-Agent": "haha@gmail.com"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        context = ET.iterparse(io.BytesIO(response.content), events=("start", "end"))
        _, root = next(context)

        parsed_data = []
        current_item = {}

        for event, elem in context:
            tag = elem.tag.split('}')[-1]
            if event == 'end':
                if tag == "infoTable":
                    parsed_data.append(current_item)
                    current_item = {}
                elif tag in ["nameOfIssuer", "titleOfClass", "cusip", "value", "investmentDiscretion", "otherManager"]:
                    current_item[tag] = elem.text.strip() if elem.text else None
                elif tag in ["sshPrnamt", "sshPrnamtType"]:
                    current_item.setdefault("shrsOrPrnAmt", {})[tag] = elem.text.strip() if elem.text else None
                elif tag in ["Sole", "Shared", "None"]:
                    current_item.setdefault("votingAuthority", {})[tag] = elem.text.strip() if elem.text else None
                elem.clear()

        blob.upload_from_string(json.dumps(parsed_data), content_type="application/json")
        logging.info(f"Saved {len(parsed_data)} records to GCS as {filename}")
        return jsonify({"status": "saved", "filename": filename})

    except Exception as e:
        logging.exception("Parsing failed")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
