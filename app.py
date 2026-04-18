import os
import re
import random
import io
from datetime import datetime

from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from PIL import Image
from supabase import create_client, Client

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ofm_codes = {
    "AA":"Congo, Democratic Republic of the","AC":"Ivory Coast","AF":"Japan",
    "AH":"Madagascar","AJ":"Panama","AK":"Cape Verde","AQ":"Syria","AU":"Uganda",
    "AV":"Israel","AW":"Organization of African Unity","AX":"Marshall Islands",
    "BL":"South Africa","BW":"World Bank","BY":"Solomon Islands","BZ":"Iraq",
    "CB":"Cambodia","CC":"Ethiopia","CG":"Marshall Islands","CM":"Micronesia",
    "CN":"International Organization Staff","CS":"Afghanistan","CT":"Bhutan",
    "CU":"Botswana","CV":"Myanmar","CW":"Cameroon","CX":"Burundi","CY":"China",
    "DA":"Colombia","DB":"Costa Rica","DC":"Cuba","DD":"Cyprus",
    "DF":"Dominican Republic","DG":"Ecuador","DH":"French Caribbean","DI":"Israel",
    "DJ":"France","DK":"Greece","DL":"India","DM":"Iran","DN":"Denmark",
    "DP":"Bangladesh","DR":"Slovakia","DZ":"Palau",
    "FC":"U.S.S.R. (Discontinued)","FF":"Antigua and Barbuda",
    "FG":"Central African Republic","FH":"Ireland","FI":"Israel","FJ":"Lebanon",
    "FK":"Kenya","FL":"Liberia","FM":"Libya","FN":"Malta","FP":"Morocco",
    "FR":"Philippines","FS":"Netherlands","FT":"Qatar","FV":"Sri Lanka",
    "FW":"Holy See (Vatican)","FX":"Sierra Leone",
    "FY":"South Africa (Discontinued)","FZ":"Suriname",
    "GC":"Sweden","GD":"Ukraine","GG":"Zambia","GM":"Turkey","GN":"Turkey",
    "GP":"Albania","GQ":"North Korea","GX":"Vanuatu",
    "HB":"Tonga","HL":"St. Lucia","HN":"Mongolia","HV":"Belgium",
    "HW":"Guatemala","HX":"Benin","HY":"Guinea-Bissau","HZ":"Haiti",
    "JB":"Honduras","JC":"Kuwait","JD":"Mauritius","JF":"Nigeria","JG":"Portugal",
    "JH":"Somalia","JJ":"Chad","JK":"Turkey","JM":"Serbia","JP":"Tunisia",
    "JQ":"Togo","JS":"Slovenia",
    "KB":"Monaco","KD":"Eritrea","KG":"Equatorial Guinea","KH":"Hungary",
    "KJ":"Lithuania","KK":"Fiji","KL":"Jordan","KM":"Jamaica","KN":"Gabon",
    "KP":"Luxembourg","KR":"Malaysia","KS":"Mexico","KT":"Namibia",
    "KU":"Sao Tome et Principe","KV":"Saudi Arabia","KW":"Seychelles","KX":"Sudan",
    "LC":"Venezuela","LD":"Vietnam","LG":"Turkey","LH":"Israel",
    "LK":"European Union","LM":"Macedonia","LR":"Bosnia and Herzegovina","LW":"Germany",
    "MF":"International Monetary Fund","MK":"Djibouti","ML":"Diego Garcia",
    "MN":"Comoros","MP":"Bahamas","MQ":"Monaco","MW":"Maledives",
    "NA":"Oman","NB":"Papua New Guinea","NC":"Paraguay","ND":"Romania","NQ":"Angola",
    "PA":"Austria","PB":"Barbados","PC":"Belize","PD":"Bermuda","PF":"Bolivia",
    "PG":"Belarus","PH":"Czech Republic","PI":"Israel","PK":"Norway","PL":"Chile",
    "PM":"Brunei","PR":"Argentina","PS":"Zimbabwe","PV":"Congo, Republic of",
    "QA":"Yemen","QD":"Burkina Faso","QL":"St. Kitts and Nevis","QM":"Bulgaria",
    "QN":"Laos","QP":"Latvia","QQ":"Lesotho","QR":"Malawi","QS":"Mozambique",
    "QT":"New Zealand","QU":"Nicaragua","QV":"Niger","QW":"Poland","QX":"Pakistan",
    "QY":"South Yemen (Discontinued)","QZ":"Indonesia",
    "RB":"Rwanda","RC":"St. Vincent and the Grenadines","RD":"Senegal","RL":"Uruguay",
    "SG":"Israel","ST":"Dominica","SX":"U.S.S.R. (Discontinued)",
    "TC":"Mali","TF":"Algeria","TG":"Canada","TH":"Egypt",
    "TJ":"East Germany (Discontinued)","TK":"Netherlands Antilles","TL":"El Salvador",
    "TM":"Iceland","TN":"Nepal","TP":"Mauritania","TQ":"Mali","TR":"Italy",
    "TS":"Iraq","TT":"Guyana","TU":"Guinea","TV":"Ghana",
    "TW":"Gambia","TX":"Finland","TY":"Grenada","TZ":"Peru",
    "UA":"Bahrain","UF":"Estonia","UH":"Spain","UX":"Trinidad and Tobago",
    "VF":"Thailand","VG":"Tanzania","VH":"Switzerland","VJ":"Brazil",
    "VK":"Singapore","VL":"Swaziland","VM":"Nauru",
    "WB":"United Arab Emirates","WD":"South Korea","WM":"Western Samoa","WZ":"United Kingdom",
    "XF":"Turkey","XY":"Ireland","XZ":"Australia",
    "YA":"Armenia","YG":"Georgia","YJ":"Tajikistan","YK":"Kazakhstan",
    "YM":"Hong Kong / Moldova","YR":"Russia","YT":"Turkmenistan",
    "YU":"Uzbekistan","YY":"Kyrgyzstan","YZ":"Azerbaijan",
    # Added from DiploPlates / pl8s.com cross-reference
    "AE":"Uzbekistan","BV":"Solomon Islands","CK":"Namibia",
    "GY":"Chile","HD":"Argentina","HM":"Andorra",
    "GK":"Montenegro","JT":"Croatia","JY":"Cyprus","LJ":"Israel","CQ":"South Sudan","CR":"Timor-Leste",
    "MG":"United Kingdom","MM":"United Kingdom","NX":"Malaysia","RJ":"Palau","RV":"San Marino",
    "SF":"Czech Republic","XA":"Bangladesh","XC":"Fiji"
}

plate_types = {"D":"Diplomat","C":"Consular","S":"Embassy Staff","A":"UN Secretariat"}

ORGANIZATIONS = {
    "Organization of African Unity","World Bank","International Organization Staff",
    "International Monetary Fund","European Union","U.S.S.R. (Discontinued)",
    "South Africa (Discontinued)","South Yemen (Discontinued)",
    "East Germany (Discontinued)",
}

COUNTRY_ISO = {
    "Ivory Coast":"CI","Congo, Democratic Republic of the":"CD",
    "Congo, Republic of":"CG","North Korea":"KP","South Korea":"KR",
    "Syria":"SY","Myanmar":"MM","Bolivia":"BO","Iran":"IR",
    "Venezuela":"VE","Vietnam":"VN","Tanzania":"TZ","Laos":"LA",
    "Moldova":"MD","Hong Kong / Moldova":"MD","Holy See (Vatican)":"VA",
    "Macedonia":"MK","French Caribbean":"GP","Swaziland":"SZ",
    "Western Samoa":"WS","Maledives":"MV","Diego Garcia":"IO",
    "Netherlands Antilles":"AN","Bermuda":"BM","Sao Tome et Principe":"ST",
    "Cape Verde":"CV","Micronesia":"FM","Guinea-Bissau":"GW",
    "Bosnia and Herzegovina":"BA","Trinidad and Tobago":"TT",
    "St. Lucia":"LC","St. Kitts and Nevis":"KN",
    "St. Vincent and the Grenadines":"VC","Antigua and Barbuda":"AG",
    "Central African Republic":"CF","Equatorial Guinea":"GQ",
    "United Arab Emirates":"AE","Papua New Guinea":"PG",
    "Dominican Republic":"DO","El Salvador":"SV","Czech Republic":"CZ",
    "Burkina Faso":"BF","Sierra Leone":"SL","South Africa":"ZA",
    "Sri Lanka":"LK","Saudi Arabia":"SA","New Zealand":"NZ",
    "Marshall Islands":"MH","Solomon Islands":"SB","Costa Rica":"CR",
    "Japan":"JP","Madagascar":"MG","Panama":"PA","Uganda":"UG",
    "Israel":"IL","Cambodia":"KH","Ethiopia":"ET","Afghanistan":"AF",
    "Bhutan":"BT","Botswana":"BW","Cameroon":"CM","Burundi":"BI",
    "China":"CN","Colombia":"CO","Cuba":"CU","Cyprus":"CY",
    "Ecuador":"EC","France":"FR","Greece":"GR","India":"IN",
    "Denmark":"DK","Bangladesh":"BD","Slovakia":"SK","Palau":"PW",
    "Ireland":"IE","Lebanon":"LB","Kenya":"KE","Liberia":"LR",
    "Libya":"LY","Malta":"MT","Morocco":"MA","Philippines":"PH",
    "Netherlands":"NL","Qatar":"QA","Sweden":"SE","Ukraine":"UA",
    "Zambia":"ZM","Turkey":"TR","Albania":"AL","Vanuatu":"VU",
    "Tonga":"TO","Mongolia":"MN","Belgium":"BE","Guatemala":"GT",
    "Benin":"BJ","Haiti":"HT","Honduras":"HN","Kuwait":"KW",
    "Mauritius":"MU","Nigeria":"NG","Portugal":"PT","Somalia":"SO",
    "Chad":"TD","Tunisia":"TN","Togo":"TG","Slovenia":"SI",
    "Monaco":"MC","Eritrea":"ER","Hungary":"HU","Lithuania":"LT",
    "Fiji":"FJ","Jordan":"JO","Jamaica":"JM","Gabon":"GA",
    "Luxembourg":"LU","Malaysia":"MY","Mexico":"MX","Namibia":"NA",
    "Seychelles":"SC","Sudan":"SD","Germany":"DE","Djibouti":"DJ",
    "Comoros":"KM","Bahamas":"BS","Oman":"OM","Paraguay":"PY",
    "Romania":"RO","Angola":"AO","Austria":"AT","Barbados":"BB",
    "Belize":"BZ","Belarus":"BY","Norway":"NO","Chile":"CL",
    "Brunei":"BN","Argentina":"AR","Zimbabwe":"ZW","Yemen":"YE",
    "Bulgaria":"BG","Latvia":"LV","Lesotho":"LS","Malawi":"MW",
    "Mozambique":"MZ","Nicaragua":"NI","Niger":"NE","Poland":"PL",
    "Pakistan":"PK","Indonesia":"ID","Rwanda":"RW","Senegal":"SN",
    "Uruguay":"UY","Dominica":"DM","Mali":"ML","Algeria":"DZ",
    "Canada":"CA","Egypt":"EG","Iceland":"IS","Nepal":"NP",
    "Mauritania":"MR","Italy":"IT","Guyana":"GY","Guinea":"GN",
    "Ghana":"GH","Gambia":"GM","Finland":"FI","Grenada":"GD",
    "Peru":"PE","Bahrain":"BH","Estonia":"EE","Spain":"ES",
    "Thailand":"TH","Switzerland":"CH","Brazil":"BR","Singapore":"SG",
    "Nauru":"NR","Iraq":"IQ","Australia":"AU","Georgia":"GE",
    "Tajikistan":"TJ","Kazakhstan":"KZ","Russia":"RU",
    "Turkmenistan":"TM","Uzbekistan":"UZ","Kyrgyzstan":"KG",
    "Azerbaijan":"AZ","United Kingdom":"GB","Suriname":"SR",
    "Andorra":"AD","Croatia":"HR","San Marino":"SM",
    "South Sudan":"SS","Timor-Leste":"TL","Serbia":"RS","Montenegro":"ME","Armenia":"AM",
}

# Country coordinates for map centering
COUNTRY_COORDS = {
    "CI":[7.5,-5.5],"CD":[-4.0,21.8],"JP":[36.2,138.3],"MG":[-18.8,46.9],
    "PA":[8.5,-80.8],"CV":[16.0,-24.0],"SY":[34.8,38.9],"UG":[1.4,32.3],
    "IL":[31.0,34.8],"MH":[7.1,171.2],"ZA":[-30.6,22.9],"SB":[-9.6,160.2],
    "IQ":[33.2,43.7],"KH":[12.6,105.0],"ET":[9.1,40.5],"FM":[7.4,150.6],
    "AF":[33.9,67.7],"BT":[27.5,90.4],"BW":[-22.3,24.7],"CM":[7.4,12.4],
    "BI":[-3.4,29.9],"CN":[35.9,104.2],"CO":[4.6,-74.3],"CR":[10.0,-84.2],
    "CU":[21.5,-77.8],"CY":[35.1,33.4],"DO":[18.7,-70.2],"EC":[-1.8,-78.2],
    "GP":[16.3,-61.6],"FR":[46.2,2.2],"GR":[39.1,21.8],"IN":[20.6,79.0],
    "DK":[56.3,9.5],"BD":[23.7,90.4],"SK":[48.7,19.7],"PW":[7.5,134.6],
    "IE":[53.1,-8.2],"LB":[33.9,35.9],"KE":[-0.0,37.9],"LR":[6.4,-9.4],
    "LY":[26.3,17.2],"MT":[35.9,14.4],"MA":[31.8,-7.1],"PH":[12.9,121.8],
    "NL":[52.1,5.3],"QA":[25.4,51.2],"LK":[7.9,80.8],"VA":[41.9,12.5],
    "SL":[8.5,-11.8],"SR":[4.0,-56.0],"SE":[60.1,18.6],"UA":[48.4,31.2],
    "ZM":[-13.1,27.8],"TR":[38.9,35.2],"AL":[41.2,20.2],"KP":[40.3,127.5],
    "VU":[-15.4,166.9],"TO":[-21.2,-175.2],"MN":[46.9,103.8],"BE":[50.5,4.5],
    "GT":[15.8,-90.2],"BJ":[9.3,2.3],"GW":[12.0,-15.2],"HT":[19.1,-72.3],
    "HN":[15.2,-86.2],"KW":[29.3,47.5],"MU":[-20.3,57.6],"NG":[9.1,8.7],
    "PT":[39.4,-8.2],"SO":[5.2,46.2],"TD":[15.5,18.7],"TN":[34.0,9.6],
    "TG":[8.6,1.2],"SI":[46.2,14.9],"MC":[43.7,7.4],"ER":[15.2,39.8],
    "GQ":[1.6,10.3],"HU":[47.2,19.5],"LT":[55.2,23.9],"FJ":[-18.0,179.0],
    "JO":[30.6,36.2],"JM":[18.1,-77.3],"GA":[-0.8,11.6],"LU":[49.8,6.1],
    "MY":[4.2,101.9],"MX":[23.6,-102.6],"NA":[-22.9,18.5],"ST":[0.2,6.6],
    "SA":[23.9,45.1],"SC":[-4.7,55.5],"SD":[12.9,30.2],"VE":[6.4,-66.6],
    "VN":[14.1,108.3],"DE":[51.2,10.5],"DJ":[11.6,43.1],"KM":[-12.2,44.3],
    "BS":[25.0,-77.4],"MV":[3.2,73.2],"OM":[21.5,55.9],"PG":[-6.3,143.9],
    "PY":[-23.4,-58.4],"RO":[45.9,24.9],"AO":[-11.2,17.9],"AT":[47.5,13.3],
    "BB":[13.2,-59.5],"BZ":[17.2,-88.5],"BM":[32.3,-64.8],"BO":[-16.3,-63.6],
    "BY":[53.7,27.9],"CZ":[49.8,15.5],"NO":[60.5,8.5],"CL":[-35.7,-71.5],
    "BN":[4.9,114.9],"AR":[-38.4,-63.6],"ZW":[-20.0,30.0],"YE":[15.6,48.5],
    "BF":[12.3,-1.6],"BG":[42.7,25.5],"LA":[19.9,102.5],"LV":[56.9,24.1],
    "LS":[-29.6,28.2],"MW":[-13.3,34.3],"MZ":[-18.7,35.5],"NZ":[-40.9,174.9],
    "NI":[12.9,-85.2],"NE":[17.6,8.1],"PL":[51.9,19.1],"PK":[30.4,69.3],
    "ID":[-0.8,113.9],"RW":[-1.9,29.9],"KN":[17.3,-62.7],"VC":[12.9,-61.3],
    "SN":[14.5,-14.5],"UY":[-32.5,-55.8],"DM":[15.4,-61.4],"ML":[17.6,-4.0],
    "DZ":[28.0,1.7],"CA":[56.1,-106.3],"EG":[26.8,30.8],"AN":[12.2,-68.9],
    "SV":[13.8,-88.9],"IS":[64.9,-19.0],"NP":[28.4,84.1],"MR":[21.0,-10.9],
    "IT":[41.9,12.6],"GY":[4.9,-58.9],"GN":[9.9,-13.7],"GH":[7.9,-1.0],
    "GM":[13.4,-16.6],"FI":[61.9,25.7],"GD":[12.3,-61.7],"PE":[-9.2,-75.0],
    "BH":[26.0,50.6],"EE":[58.6,25.0],"ES":[40.5,-3.7],"TT":[10.7,-61.2],
    "TH":[15.9,100.9],"TZ":[-6.4,34.9],"CH":[46.8,8.2],"BR":[-14.2,-51.9],
    "SG":[1.4,103.8],"NR":[-0.5,166.9],"AE":[23.4,53.8],"KR":[35.9,127.8],
    "WS":[-13.8,-172.1],"GB":[55.4,-3.4],"AU":[-25.3,133.8],"GE":[42.3,43.4],
    "TJ":[38.9,71.3],"KZ":[48.0,68.0],"MD":[47.4,28.4],"RU":[61.5,105.3],
    "UZ":[41.4,64.6],"KG":[41.2,74.8],"AZ":[40.1,47.6],"IO":[-6.3,71.9],
    "SZ":[-26.5,31.5],"AG":[17.1,-61.8],"CF":[6.6,20.9],"LC":[13.9,-61.0],
    "BA":[43.9,17.7],"CG":[-4.3,15.3],"AM":[40.1,45.0],
    "AD":[42.5,1.5],"HR":[45.1,15.2],"SM":[43.9,12.4],
    "SS":[6.9,31.3],"TL":[-8.9,125.7],"RS":[44.0,21.0],"ME":[42.7,19.4],"PW":[7.5,134.6],
}

ORG_ICONS = {
    "World Bank":"WB","International Monetary Fund":"IMF",
    "European Union":"EU","Organization of African Unity":"OAU",
    "International Organization Staff":"IO",
}


def get_iso(country_name):
    if country_name in ORGANIZATIONS or country_name in ("Unknown Code","Unknown"):
        return None
    if country_name in COUNTRY_ISO:
        return COUNTRY_ISO[country_name].lower()
    return None


def get_coords(iso2):
    if iso2:
        c = COUNTRY_COORDS.get(iso2.upper())
        if c: return c
    return None


def parse_plate(text):
    clean = text.replace(" ","").replace("-","").replace(".","").upper()
    clean = re.sub(r'[^A-Z0-9]', '', clean)
    m1 = re.search(r'^([ADCS])([A-Z]{2})(\d+)$', clean)
    m2 = re.search(r'^(\d+)([A-Z]{2})([ADCS])$', clean)
    if m1: tc, cc, d = m1.group(1), m1.group(2), m1.group(3)
    elif m2: d, cc, tc = m2.group(1), m2.group(2), m2.group(3)
    else: return None
    vt = plate_types.get(tc, "Unknown")
    country = ofm_codes.get(cc, "Unknown Code")
    amb = d in ("0001","1")
    scan_type = "Ambassador" if amb else vt
    if amb: vt = "Ambassador (" + vt + ")"
    iso2 = get_iso(country)
    is_org = country in ORGANIZATIONS
    coords = get_coords(iso2) if iso2 else None
    return {
        "plate": clean,
        "type": vt,
        "scan_type": scan_type,
        "code": cc,
        "country": country,
        "ambassador": amb,
        "iso2": iso2,
        "is_org": is_org,
        "org_icon": ORG_ICONS.get(country, "ORG") if is_org else None,
        "lat": coords[0] if coords else None,
        "lng": coords[1] if coords else None,
    }


def record_scan(code, country, plate_type):
    try:
        supabase.table("scans").insert({
            "code": code,
            "country": country,
            "plate_type": plate_type
        }).execute()
    except:
        # Fallback if plate_type column doesn't exist yet
        try:
            supabase.table("scans").insert({"code": code, "country": country}).execute()
        except:
            pass


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/lookup", methods=["POST"])
def lookup():
    data = request.json
    plate_text = data.get("plate", "")
    if not plate_text:
        return jsonify({"error": "No plate provided"}), 400
    result = parse_plate(plate_text)
    if not result or result["country"] == "Unknown Code":
        return jsonify({"error": "Could not recognize a valid diplomatic plate format."}), 404
    record_scan(result["code"], result["country"], result["scan_type"])
    return jsonify(result)


@app.route("/api/trivia")
def trivia():
    name = request.args.get("name", "")
    is_org = request.args.get("org", "false") == "true"
    if not name:
        return jsonify({"trivia": None})
    seed = random.randint(1, 10000)
    kind = "organization" if is_org else "country"
    prompt = f"Give me one surprising and fun trivia fact about the {kind} '{name}'. Keep it to 1-2 sentences. Random seed: {seed}. Respond with ONLY the fact."
    try:
        resp = model.generate_content(prompt)
        return jsonify({"trivia": resp.text.strip()})
    except:
        return jsonify({"trivia": None})


@app.route("/api/scan-image", methods=["POST"])
def scan_image():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400
    file = request.files["image"]
    img_bytes = file.read()
    img_buffer = io.BytesIO(img_bytes)
    try:
        image = Image.open(img_buffer)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
    except Exception as e:
        return jsonify({"error": f"Could not process image: {str(e)}"}), 400

    max_dim = 1500
    if max(image.size) > max_dim:
        ratio = max_dim / max(image.size)
        new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
        image = image.resize(new_size, Image.LANCZOS)

    prompt = """You are looking at a photo that may contain a US diplomatic license plate.

US diplomatic plates come in these formats:
- Standard: One letter prefix (D, A, C, or S), then two letters (country code), then numbers. Example: DAF 1234
- Reversed: Numbers first, then two letters (country code), then one letter suffix (D, A, C, or S). Example: 1234 AFD

The prefix/suffix letters mean: D = Diplomat, A = UN Secretariat, C = Consular, S = Embassy Staff

Look carefully at the license plate in the image. Read ALL characters on the plate.
Respond with ONLY the letters and numbers from the plate, nothing else.
If you cannot find or read a diplomatic plate, respond with exactly: NONE"""

    try:
        response = model.generate_content([prompt, image])
        ai_result = response.text.strip().upper()
        ai_result = re.sub(r'[^A-Z0-9\s]', '', ai_result).strip()
        if ai_result == "NONE" or not ai_result:
            return jsonify({"error": "Could not read a diplomatic plate from this image. Try typing it manually."}), 404
        result = parse_plate(ai_result)
        if not result or result["country"] == "Unknown Code":
            return jsonify({"error": f"AI read '{ai_result}' but it doesn't match a known format.", "ai_read": ai_result}), 404
        record_scan(result["code"], result["country"], result["scan_type"])
        result["ai_read"] = ai_result
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"AI processing error: {str(e)}"}), 500


@app.route("/api/leaderboard")
def leaderboard():
    period = request.args.get("period", "all")
    try:
        resp = supabase.table("scans").select("*").execute()
        data = resp.data
        if not data:
            return jsonify({"entries": [], "total_scans": 0, "total_countries": 0, "top_country": None, "type_counts": {}})

        from collections import Counter
        now = datetime.utcnow()

        filtered = data
        if period == "today":
            filtered = [r for r in data if "created_at" in r and r["created_at"][:10] == now.strftime("%Y-%m-%d")]
        elif period == "month":
            prefix = now.strftime("%Y-%m")
            filtered = [r for r in data if "created_at" in r and r["created_at"][:7] == prefix]

        counts = Counter(r["country"] for r in filtered)
        entries = [{"country": c, "scans": s, "iso2": get_iso(c)} for c, s in counts.most_common()]
        for e in entries:
            if e["country"] in ORGANIZATIONS:
                e["org_icon"] = ORG_ICONS.get(e["country"], "ORG")

        # Type breakdown
        type_counts = Counter(r.get("plate_type", "Unknown") for r in filtered)

        top = entries[0]["country"] if entries else None
        return jsonify({
            "entries": entries,
            "total_scans": sum(e["scans"] for e in entries),
            "total_countries": len(entries),
            "top_country": top,
            "type_counts": dict(type_counts),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)