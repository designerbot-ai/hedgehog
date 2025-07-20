from flask import Flask, request, jsonify
import requests
import xml.etree.ElementTree as ET
import io
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["POST"])
def parse_single_xml():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    try:
        headers = {
            "User-Agent": "haha@gmail.com"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        context = ET.iterparse(io.BytesIO(response.content), events=("start", "end"))
        _, root = next(context)

        parsed_data = []
        current_item = {}

        for event, elem in context:
            tag = elem.tag.split('}')[-1]  # Remove namespace
            if event == 'end':
                if tag == "infoTable":
                    parsed_data.append(current_item)
                    current_item = {}
                elif tag in [
                    "nameOfIssuer", "titleOfClass", "cusip", "value",
                    "investmentDiscretion", "otherManager"
                ]:
                    current_item[tag] = elem.text.strip() if elem.text else None
                elif tag in ["sshPrnamt", "sshPrnamtType"]:
                    current_item.setdefault("shrsOrPrnAmt", {})[tag] = elem.text.strip() if elem.text else None
                elif tag in ["Sole", "Shared", "None"]:
                    current_item.setdefault("votingAuthority", {})[tag] = elem.text.strip() if elem.text else None

                elem.clear()
                root.clear()

        logging.info(f"Extracted {len(parsed_data)} entries from {url}")
        return jsonify(parsed_data)

    except Exception as e:
        logging.exception("Parsing failed")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
