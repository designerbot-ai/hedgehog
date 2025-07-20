from flask import Flask, request, jsonify
import requests
import xml.etree.ElementTree as ET
import io
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

USER_AGENT = "haha@gmail.com"  # SEC requires email in user-agent

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "OK",
        "message": "XML Parser service is running. POST to /parse-xml with {'urls': [...]}"
    })

@app.route("/parse-xml", methods=["POST"])
def parse_xml_files():
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"error": "Invalid JSON payload, expected object with 'urls' key"}), 400

        urls = data.get("urls")
        if not isinstance(urls, list):
            return jsonify({"error": "'urls' must be a list of XML URLs"}), 400

        headers = {
            "User-Agent": USER_AGENT
        }

        all_results = []

        for url in urls:
            try:
                logging.info(f"Fetching: {url}")
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                xml_data = io.BytesIO(response.content)

                context = ET.iterparse(xml_data, events=("start", "end"))
                _, root = next(context)

                current_item = {}
                parsed_items = []

                for event, elem in context:
                    tag = elem.tag.split("}")[-1].lower()

                    if event == "end":
                        if tag == "nameOfIssuer".lower():
                            current_item["nameOfIssuer"] = elem.text
                        elif tag == "titleOfClass".lower():
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
                            parsed_items.append(current_item)
                            current_item = {}

                        elem.clear()
                        root.clear()

                all_results.extend(parsed_items)
                logging.info(f"Parsed {len(parsed_items)} items from {url}")

            except requests.exceptions.RequestException as req_err:
                logging.warning(f"Request failed for {url}: {req_err}")
            except ET.ParseError as parse_err:
                logging.warning(f"XML parsing failed for {url}: {parse_err}")
            except Exception as generic_err:
                logging.exception(f"Unexpected error processing {url}: {generic_err}")

        return jsonify(all_results)

    except Exception as e:
        logging.exception("Fatal server error")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
