from flask import Flask, request, jsonify
import requests
import xml.etree.ElementTree as ET
import logging
import io

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["POST"])
def extract_info_tables():
    try:
        urls = request.get_json().get("urls", [])
        results = []

        for url in urls:
            response = requests.get(url)
            response.raise_for_status()
            xml_data = response.content
            count = 0

            context = ET.iterparse(io.BytesIO(xml_data), events=("start", "end"))
            _, root = next(context)
            current_item = {}
            for event, elem in context:
                tag = elem.tag.lower()
                if event == "end":
                    if tag == "nameofissuer":
                        current_item["nameOfIssuer"] = elem.text
                    elif tag == "titleofclass":
                        current_item["titleOfClass"] = elem.text
                    elif tag == "cusip":
                        current_item["cusip"] = elem.text
                    elif tag == "value":
                        current_item["value"] = elem.text
                    elif tag == "sshprnamt":
                        current_item["sshPrnamt"] = elem.text
                    elif tag == "sshprnamttype":
                        current_item["sshPrnamtType"] = elem.text
                    elif tag == "investmentdiscretion":
                        current_item["investmentDiscretion"] = elem.text
                    elif tag == "othermanager":
                        current_item["otherManager"] = elem.text
                    elif tag == "sole":
                        current_item.setdefault("votingAuthority", {})["Sole"] = elem.text
                    elif tag == "shared":
                        current_item.setdefault("votingAuthority", {})["Shared"] = elem.text
                    elif tag == "none":
                        current_item.setdefault("votingAuthority", {})["None"] = elem.text
                    elif tag == "infotable":
                        results.append(current_item)
                        count += 1
                        current_item = {}

            logging.info(f"Parsed {count} items from {url}")

        return jsonify(results)

    except Exception as e:
        logging.exception("Error occurred while parsing XMLs")
        return jsonify({"error": str(e)}), 500
