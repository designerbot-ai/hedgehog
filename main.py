from flask import Flask, request, jsonify
import requests
import xml.etree.ElementTree as ET
import logging
import io

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Health check route
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "OK",
        "message": "XML Streamer API is running. Send POST to /parse-xml"
    })

# Multi-URL parser
@app.route("/", methods=["POST"])
def extract_info_tables():
    try:
        data = request.get_json()

        # Accept both {"urls": [...]} and raw array []
        if isinstance(data, list):
            urls = data
        else:
            urls = data.get("urls", [])

        if not urls:
            return jsonify({"error": "Missing or empty 'urls' list"}), 400

        headers = {
            "User-Agent": "haha@gmail.com"
        }

        results = []
        for url in urls:
            logging.info(f"Fetching URL: {url}")
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            xml_data = io.BytesIO(response.content)

            context = ET.iterparse(xml_data, events=("start", "end"))
            _, root = next(context)
            current_item = {}

            for event, elem in context:
                tag = elem.tag.split('}')[-1].lower()

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
                        current_item.setdefault("shrsOrPrnAmt", {})["sshPrnamt"] = elem.text
                    elif tag == "sshprnamttype":
                        current_item.setdefault("shrsOrPrnAmt", {})["sshPrnamtType"] = elem.text
                    elif tag == "investmentdiscretion":
                        current_item["investmentDiscretion"] = elem.text
                    elif tag == "othermanager":
                        current_item["otherManager"] = elem.text
                    elif tag in ["sole", "shared", "none"]:
                        current_item.setdefault("votingAuthority", {})[tag.capitalize()] = elem.text
                    elif tag == "infotable":
                        results.append(current_item)
                        current_item = {}

                    elem.clear()
                    root.clear()

        logging.info(f"Parsed total of {len(results)} items across {len(urls)} files.")
        return jsonify(results)

    except Exception as e:
        logging.exception("Error while parsing XMLs")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
