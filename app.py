import os
import re
import random
import base64
from io import BytesIO
from datetime import datetime, timedelta

from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from PIL import Image
from supabase import create_client, Client

app = Flask(__name__)

# --- CONFIG (env vars for Cloud Run, fallback to .env) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- OFM CODES ---
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
    "JH":"Somalia","JJ":"Chad","JK":"Turkey","JM":"Yugoslavia","JP":"Tunisia",
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
    "TS":"Iraq (Discontinued)","TT":"Guyana","TU":"Guinea","TV":"Ghana",
    "TW":"Gambia","TX":"Finland","TY":"Grenada","TZ":"Peru",
    "UA":"Bahrain","UF":"Estonia","UH":"Spain","UX":"Trinidad and Tobago",
    "VF":"Thailand","VG":"Tanzania","VH":"Switzerland","VJ":"Brazil",
    "VK":"Singapore","VL":"Swaziland","VM":"Nauru",
    "WB":"United Arab Emirates","WD":"South Korea","WM":"Western Samoa","WZ":"United Kingdom",
    "XF":"Turkey","XY":"Unknown","XZ":"Australia",
    "YA":"Unknown","YG":"Georgia","YJ":"Tajikistan","YK":"Kazakhstan",
    "YM":"Hong Kong / Moldova","YR":"Russia","YT":"Turkmenistan",
    "YU":"Uzbekistan","YY":"Kyrgyzstan","YZ":"Azerbaijan"
}

plate_types = {"D":"Diplomat","C":"Consular","S":"Embassy Staff","A":"UN Secretariat"}

ORGANIZATIONS = {
    "Organization of African Unity","World Bank","International Organization Staff",
    "International Monetary Fund","European Union","U.S.S.R. (Discontinued)",
    "South Africa (Discontinued)","South Yemen (Discontinued)",
    "East Germany (Discontinued)","Iraq (Discontinued)",
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
}

ORG_ICONS = {
    "World Bank":"🏦","International Monetary Fund":"💰",
    "European Union":"🇪🇺","Organization of African Unity":"🌍",
    "International Organization Staff":"🏛️",
}


def get_iso(country_name):
    if country_name in ORGANIZATIONS or country_name in ("Unknown Code","Unknown"):
        return None, None
    if country_name in COUNTRY_ISO:
        a2 = COUNTRY_ISO[country_name]
        return a2.lower(), a2.lower()
    return None, None


def parse_plate(text):
    clean = text.replace(" ","").upper()
    m1 = re.search(r'^([ADCS])([A-Z]{2})(\d+)$', clean)
    m2 = re.search(r'^(\d+)([A-Z]{2})([ADCS])$', clean)
    if m1: tc, cc, d = m1.group(1), m1.group(2), m1.group(3)
    elif m2: d, cc, tc = m2.group(1), m2.group(2), m2.group(3)
    else: return None
    vt = plate_types.get(tc, "Unknown")
    country = ofm_codes.get(cc, "Unknown Code")
    amb = d in ("0001","1")
    if amb: vt = "Ambassador (" + vt + ")"
    iso2, _ = get_iso(country)
    is_org = country in ORGANIZATIONS
    return {
        "plate": clean,
        "type": vt,
        "code": cc,
        "country": country,
        "ambassador": amb,
        "iso2": iso2,
        "is_org": is_org,
        "org_icon": ORG_ICONS.get(country, "🏛️") if is_org else None,
    }


def record_scan(code, country):
    try: supabase.table("scans").insert({"code":code,"country":country}).execute()
    except: pass


def get_trivia(name, is_org=False):
    seed = random.randint(1, 10000)
    kind = "organization" if is_org else "country"
    prompt = f"Give me one surprising and fun trivia fact about the {kind} '{name}'. Keep it to 1-2 sentences. Random seed: {seed}. Respond with ONLY the fact."
    try: return model.generate_content(prompt).text.strip()
    except: return None


# --- ROUTES ---
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

    record_scan(result["code"], result["country"])
    trivia = get_trivia(result["country"], result["is_org"])
    result["trivia"] = trivia
    return jsonify(result)


@app.route("/api/scan-image", methods=["POST"])
def scan_image():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]
    image = Image.open(file.stream)

    prompt = """Look at this image of a vehicle or license plate. Find the US diplomatic license plate.
    It will either be in the format "[Letter][Two Letters] [Numbers]" (like DAF 1234)
    OR reversed "[Numbers] [Two Letters][Letter]" (like 1234 AFD).
    Respond ONLY with the exact text written on the license plate (letters and numbers).
    If you cannot read it clearly, respond with the exact word: NONE."""

    try:
        response = model.generate_content([prompt, image])
        ai_result = response.text.strip().upper()

        if ai_result == "NONE":
            return jsonify({"error": "Could not read a diplomatic plate from this image."}), 404

        result = parse_plate(ai_result)
        if not result or result["country"] == "Unknown Code":
            return jsonify({"error": f"AI read '{ai_result}' but it doesn't match a known format.", "ai_read": ai_result}), 404

        record_scan(result["code"], result["country"])
        trivia = get_trivia(result["country"], result["is_org"])
        result["trivia"] = trivia
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/leaderboard")
def leaderboard():
    period = request.args.get("period", "all")

    try:
        resp = supabase.table("scans").select("*").execute()
        data = resp.data
        if not data:
            return jsonify({"entries": [], "total_scans": 0, "total_countries": 0, "top_country": None})

        from collections import Counter
        now = datetime.utcnow()

        filtered = data
        if period == "today":
            filtered = [r for r in data if "created_at" in r and r["created_at"][:10] == now.strftime("%Y-%m-%d")]
        elif period == "month":
            prefix = now.strftime("%Y-%m")
            filtered = [r for r in data if "created_at" in r and r["created_at"][:7] == prefix]

        counts = Counter(r["country"] for r in filtered)
        entries = [{"country": c, "scans": s, "iso2": get_iso(c)[0]} for c, s in counts.most_common()]

        # Add org icons
        for e in entries:
            if e["country"] in ORGANIZATIONS:
                e["org_icon"] = ORG_ICONS.get(e["country"], "🏛️")

        top = entries[0]["country"] if entries else None
        return jsonify({
            "entries": entries,
            "total_scans": sum(e["scans"] for e in entries),
            "total_countries": len(entries),
            "top_country": top,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
