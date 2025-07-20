from flask import Flask, request, jsonify
import requests
import xml.etree.ElementTree as ET
import io

app = Flask(__name__)

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "OK",
        "message": "XML Streamer API is running. Send POST requests to /parse-xml"
    })

@app.route('/parse-xml', methods=['POST'])
def handle_xml_url():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "Missing URL"}), 400

    try:
        # Proper SEC-compliant User-Agent
        headers = {
            "User-Agent": "haha@gmail.com"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Convert to BytesIO so ElementTree can parse
        xml_data = io.BytesIO(response.content)
        context = ET.iterparse(xml_data, events=("start", "end"))
        _, root = next(context)  # root element

        parsed_data = []
        current_item = {}
        limit = 10
        count = 0

        for event, elem in context:
            tag = elem.tag.split('}')[-1]  # Strip namespace

            if event == 'end':
                if tag == "infoTable":
                    parsed_data.append(current_item)
                    current_item = {}
                    count += 1
                    if count >= limit:
                        break
                elif tag in [
                    "nameOfIssuer", "titleOfClass", "cusip", "value",
                    "investmentDiscretion", "otherManager"
                ]:
                    current_item[tag] = elem.text
                elif tag in ["sshPrnamt", "sshPrnamtType"]:
                    current_item.setdefault("shrsOrPrnAmt", {})[tag] = elem.text
                elif tag in ["Sole", "Shared", "None"]:
                    current_item.setdefault("votingAuthority", {})[tag] = elem.text

                elem.clear()
                root.clear()

        return jsonify(parsed_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)