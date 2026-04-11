import streamlit as st
import google.generativeai as genai
from PIL import Image
import re
from datetime import datetime
from supabase import create_client, Client
import pandas as pd
import plotly.graph_objects as go
import pycountry
import random

# --- PAGE CONFIG ---
st.set_page_config(page_title="DiploCheck", page_icon="🌐", layout="centered")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    div[data-testid="stDecoration"] {display: none;}

    .stApp {
        background: #d6e6f0 !important;
    }

    /* ── PLATE FRAME ── */
    .plate-frame {
        border: 4px solid #a0afc0;
        border-radius: 14px;
        padding: 5px;
        background: #7a8a9c;
        box-shadow: 0 6px 24px rgba(0,0,0,0.18);
    }
    .plate-inner {
        background: #f0f2f5;
        border-radius: 10px;
        overflow: hidden;
        position: relative;
    }
    .plate-stripe {
        background: linear-gradient(90deg, #c42b2b 0%, #c42b2b 35%, #2b5ea7 65%, #2b5ea7 100%);
        padding: 10px 24px;
        text-align: center;
        position: relative;
    }
    .plate-stripe .plate-title {
        font-size: 15px;
        font-weight: 800;
        color: white;
        letter-spacing: 0.3em;
        text-transform: uppercase;
        display: block;
    }
    .plate-stripe .plate-subtitle {
        font-size: 9px;
        font-weight: 600;
        color: rgba(255,255,255,0.85);
        letter-spacing: 0.18em;
        text-transform: uppercase;
        display: block;
        margin-top: 2px;
    }
    .plate-bolt {
        width: 11px; height: 11px; border-radius: 50%;
        background: radial-gradient(circle at 35% 35%, #d0d8e4, #8a9bb4);
        border: 1px solid #6b7a8d;
        position: absolute; z-index: 2;
    }
    .plate-body {
        padding: 24px;
        position: relative;
    }

    /* ── RESULT PLATE ── */
    .result-plate .plate-body {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 20px 24px;
    }
    .result-country {
        display: flex; align-items: center; gap: 14px;
    }
    .result-country img {
        width: 44px; border-radius: 4px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    }
    .result-country .name {
        font-size: 20px; font-weight: 700;
        color: #0a1628 !important; margin: 0;
    }
    .result-country .type {
        font-size: 11px; color: #5a6a7e !important;
        text-transform: uppercase; letter-spacing: 0.06em;
        font-weight: 600; margin: 2px 0 0;
    }
    .result-plate-code {
        font-family: monospace; font-size: 26px; font-weight: 700;
        color: #0a1628 !important; letter-spacing: 0.15em;
    }

    /* ── CARDS ON LIGHT BG ── */
    .light-card {
        background: white;
        border: 1px solid #c0cdd8;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 14px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .light-card h3 {
        margin: 0 0 4px; font-size: 16px; color: #0a1628;
    }
    .light-card .subtitle {
        margin: 0 0 12px; font-size: 13px; color: #5a6a7e;
    }

    /* ── TRIVIA ── */
    .trivia-box {
        background: white;
        border-left: 4px solid #2b5ea7;
        border-radius: 0 10px 10px 0;
        padding: 16px 20px;
        margin-top: 16px;
        font-size: 14px;
        color: #1a2a3a;
        line-height: 1.6;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .trivia-box .trivia-label {
        font-size: 11px; text-transform: uppercase;
        letter-spacing: 0.06em; font-weight: 600;
        color: #2b5ea7; margin-bottom: 6px;
    }

    /* ── OR DIVIDER ── */
    .or-divider {
        display: flex; align-items: center; gap: 16px;
        color: #5a6a7e; font-size: 13px; font-weight: 500; margin: 8px 0;
    }
    .or-divider .line { flex: 1; height: 1px; background: #b0c0d0; }

    /* ── LEADERBOARD ── */
    .leader-row {
        display: flex; align-items: center; gap: 14px;
        padding: 12px 0; border-bottom: 1px solid #c0cdd8;
    }
    .leader-row:last-child { border-bottom: none; }
    .rank-badge {
        width: 28px; height: 28px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 12px; font-weight: 700; color: white; flex-shrink: 0;
    }
    .rank-1 { background: #d4a843; }
    .rank-2 { background: #8a9bb4; }
    .rank-3 { background: #c4956a; }
    .rank-other { background: #c0cdd8; color: #5a6a7e; }
    .leader-bar-bg {
        width: 120px; height: 6px;
        background: #c0cdd8; border-radius: 3px; overflow: hidden;
    }
    .leader-bar-fill {
        height: 100%; border-radius: 3px;
        background: linear-gradient(90deg, #c42b2b, #2b5ea7);
    }

    /* ── METRICS ── */
    div[data-testid="stMetric"] {
        background: white !important;
        border: 1px solid #c0cdd8;
        border-radius: 12px;
        padding: 14px 16px;
    }
    div[data-testid="stMetric"] label { color: #5a6a7e !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #0a1628 !important; }

    /* ── BUTTONS ── */
    .stButton > button {
        background: white !important; color: #0a1628 !important;
        border: 1px solid #b0c0d0 !important; border-radius: 8px !important;
    }
    .stButton > button:hover {
        background: #e8f0f6 !important; border-color: #2b5ea7 !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #c42b2b, #2b5ea7) !important;
        color: white !important; border: none !important;
    }

    /* ── INPUTS ── */
    .stTextInput input {
        background: white !important; color: #0a1628 !important;
        border: 1.5px solid #b0c0d0 !important; border-radius: 8px !important;
        font-family: monospace !important; letter-spacing: 0.12em !important;
        text-transform: uppercase !important;
    }
    .stTextInput input:focus { border-color: #2b5ea7 !important; }
    .stTextInput input::placeholder { color: #8a9bb4 !important; }

    /* ── LANDING CARDS ── */
    .landing-option {
        background: white;
        border: 1px solid #c0cdd8;
        border-radius: 12px;
        padding: 28px 16px;
        text-align: center;
        cursor: pointer;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    .landing-option:hover {
        border-color: #2b5ea7;
        box-shadow: 0 4px 12px rgba(43,94,167,0.12);
    }
    .landing-option h3 {
        margin: 0 0 4px; font-size: 17px; color: #0a1628; font-weight: 700;
    }
    .landing-option p {
        margin: 0; font-size: 12px; color: #5a6a7e;
    }

    /* success/error */
    .stSuccess, .stError, .stWarning, .stInfo { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# --- APIS ---
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')
supabase_url = st.secrets["supabase"]["URL"]
supabase_key = st.secrets["supabase"]["KEY"]
supabase: Client = create_client(supabase_url, supabase_key)

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

COUNTRY_NAME_OVERRIDES = {
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
}

ORG_ICONS = {
    "World Bank":"🏦","International Monetary Fund":"💰",
    "European Union":"🇪🇺","Organization of African Unity":"🌍",
    "International Organization Staff":"🏛️",
    "U.S.S.R. (Discontinued)":"☭","South Africa (Discontinued)":"🇿🇦",
    "South Yemen (Discontinued)":"🇾🇪","East Germany (Discontinued)":"🇩🇪",
    "Iraq (Discontinued)":"🇮🇶",
}


# --- HELPERS ---
def get_iso_codes(country_name):
    if country_name in ORGANIZATIONS or country_name in ("Unknown Code","Unknown"):
        return None, None
    if country_name in COUNTRY_NAME_OVERRIDES:
        a2 = COUNTRY_NAME_OVERRIDES[country_name]
        try:
            c = pycountry.countries.get(alpha_2=a2)
            return c.alpha_2, c.alpha_3
        except: return a2, None
    try:
        results = pycountry.countries.search_fuzzy(country_name)
        if results: return results[0].alpha_2, results[0].alpha_3
    except: pass
    return None, None

def get_flag_url(iso2):
    return f"https://flagcdn.com/w320/{iso2.lower()}.png" if iso2 else None

def render_world_map(iso3, country_name):
    fig = go.Figure(go.Choropleth(
        locations=[iso3], z=[1],
        colorscale=[[0,"#2b5ea7"],[1,"#2b5ea7"]],
        showscale=False, marker_line_color="#b0c0d0", marker_line_width=0.5,
        hovertext=[country_name], hoverinfo="text",
    ))
    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True, coastlinecolor="#b0c0d0",
                 projection_type="natural earth", landcolor="#e8f0f6",
                 oceancolor="#d6e6f0", showocean=True, showcountries=True,
                 countrycolor="#b0c0d0"),
        margin=dict(l=0,r=0,t=0,b=0), height=280,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

def get_trivia(name, is_org=False):
    seed = random.randint(1, 10000)
    kind = "organization" if is_org else "country"
    prompt = f"Give me one surprising and fun trivia fact about the {kind} '{name}'. Keep it to 1-2 sentences. Be specific and interesting. Random seed: {seed}. Respond with ONLY the fact, no preamble."
    try:
        return model.generate_content(prompt).text.strip()
    except: return None

def record_scan(code, country):
    try: supabase.table("scans").insert({"code":code,"country":country}).execute()
    except: pass

def get_diplomat_info(plate_text):
    clean = plate_text.replace(" ","").upper()
    m1 = re.search(r'^([ADCS])([A-Z]{2})(\d+)$', clean)
    m2 = re.search(r'^(\d+)([A-Z]{2})([ADCS])$', clean)
    if m1: tc, cc, d = m1.group(1), m1.group(2), m1.group(3)
    elif m2: d, cc, tc = m2.group(1), m2.group(2), m2.group(3)
    else: return None, None, "Format not recognized.", False
    vt = plate_types.get(tc, "Unknown")
    country = ofm_codes.get(cc, "Unknown Code")
    amb = d in ("0001","1")
    if amb: vt = "Ambassador (" + vt + ")"
    return vt, cc, country, amb


def render_plate_stripe():
    return """
    <div class="plate-stripe">
        <div class="plate-bolt" style="top:5px;left:10px;"></div>
        <div class="plate-bolt" style="top:5px;right:10px;"></div>
        <span class="plate-title">DIPLOCHECK</span>
        <span class="plate-subtitle">Identify diplomatic license plates in the U.S.</span>
    </div>
    """


def display_result(vehicle_type, code, country, is_ambassador, plate_text=""):
    if is_ambassador:
        st.balloons()
        st.success("🌟 You spotted an Ambassador's official vehicle!")
    else:
        st.success("✅ Match found!")

    is_org = country in ORGANIZATIONS
    iso2, iso3 = get_iso_codes(country)
    flag_url = get_flag_url(iso2)
    display_plate = plate_text.upper().replace(" ","") if plate_text else code

    flag_html = ""
    if flag_url:
        flag_html = f'<img src="{flag_url}" style="width:44px;border-radius:4px;box-shadow:0 2px 6px rgba(0,0,0,0.15);"/>'
    elif is_org:
        flag_html = f'<span style="font-size:32px;">{ORG_ICONS.get(country,"🏛️")}</span>'

    type_label = ("👑 " + vehicle_type) if is_ambassador else vehicle_type

    st.markdown(f"""
    <div class="plate-frame result-plate" style="margin-top:16px;">
        <div class="plate-inner">
            {render_plate_stripe()}
            <div class="plate-body">
                <div class="result-country">
                    {flag_html}
                    <div>
                        <p class="name">{country}</p>
                        <p class="type">{type_label}</p>
                    </div>
                </div>
                <div class="result-plate-code">{display_plate}</div>
            </div>
            <div class="plate-bolt" style="bottom:6px;left:10px;"></div>
            <div class="plate-bolt" style="bottom:6px;right:10px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if iso3:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        render_world_map(iso3, country)

    with st.spinner("Loading a fun fact..."):
        trivia = get_trivia(country, is_org=is_org)
    if trivia:
        st.markdown(f"""
        <div class="trivia-box">
            <div class="trivia-label">💡 Did you know?</div>
            {trivia}
        </div>
        """, unsafe_allow_html=True)


# --- NAVIGATION ---
if "page" not in st.session_state:
    st.session_state.page = "home"

def go_home(): st.session_state.page = "home"
def go_scan(): st.session_state.page = "scan"
def go_leaderboard(): st.session_state.page = "leaderboard"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#                  LANDING PAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if st.session_state.page == "home":

    st.markdown("<div style='height:50px'></div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="plate-frame" style="max-width:520px; margin:0 auto;">
        <div class="plate-inner">
            {render_plate_stripe()}
            <div class="plate-body" style="padding:28px 24px 24px;">
                <div class="plate-bolt" style="bottom:8px;left:10px;"></div>
                <div class="plate-bolt" style="bottom:8px;right:10px;"></div>
                <div style="display:flex; gap:16px;">
                    <div class="landing-option" style="flex:1;">
                        <div style="font-size:32px; margin-bottom:10px;">🔍</div>
                        <h3>Check a plate</h3>
                        <p>Type or snap a diplomatic plate</p>
                    </div>
                    <div class="landing-option" style="flex:1;">
                        <div style="font-size:32px; margin-bottom:10px;">🏆</div>
                        <h3>Leaderboard</h3>
                        <p>See the most spotted nations</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Buttons need to be outside the HTML — Streamlit can't nest buttons in markdown
    st.markdown("<div style='max-width:520px; margin:8px auto 0;'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        st.button("Check a Plate →", on_click=go_scan, use_container_width=True, type="primary")
    with col2:
        st.button("Leaderboard →", on_click=go_leaderboard, use_container_width=True, type="primary")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#                  SCAN PAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif st.session_state.page == "scan":

    col_back, col_rest = st.columns([0.1, 0.9])
    with col_back:
        st.button("←", on_click=go_home, help="Back to home")

    st.markdown(f"""
    <div class="plate-frame" style="margin-bottom:4px;">
        <div class="plate-inner">
            {render_plate_stripe()}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    st.markdown('<div class="light-card"><h3>⌨️ Type a plate number</h3><p class="subtitle">Letters and numbers — we\'ll figure out the format</p></div>', unsafe_allow_html=True)
    manual_input = st.text_input("Plate", placeholder="e.g. DAF 1234, AXX 0001, or 1234 AFD", label_visibility="collapsed")

    if manual_input:
        vt, code, country, amb = get_diplomat_info(manual_input)
        if code and country != "Unknown Code":
            record_scan(code, country)
            display_result(vt, code, country, amb, manual_input)
        else:
            st.error("Could not recognize a valid diplomatic plate format.")

    st.markdown('<div class="or-divider"><div class="line"></div>or<div class="line"></div></div>', unsafe_allow_html=True)

    st.markdown('<div class="light-card"><h3>📷 Upload or take a photo</h3><p class="subtitle">Snap a plate and let AI read it for you</p></div>', unsafe_allow_html=True)

    up_col, cam_col = st.columns(2)
    with up_col:
        uploaded_file = st.file_uploader("Upload", type=["jpg","jpeg","png"], label_visibility="collapsed")
    with cam_col:
        camera_file = st.camera_input("Camera", label_visibility="collapsed")

    image_to_process = uploaded_file or camera_file
    if image_to_process:
        image = Image.open(image_to_process)
        st.image(image, caption="Captured Plate", use_container_width=True)
        with st.spinner("🔍 Analyzing with Google AI..."):
            prompt = """Look at this image of a vehicle or license plate. Find the US diplomatic license plate.
            It will either be in the format "[Letter][Two Letters] [Numbers]" (like DAF 1234)
            OR reversed "[Numbers] [Two Letters][Letter]" (like 1234 AFD).
            Respond ONLY with the exact text written on the license plate (letters and numbers).
            If you cannot read it clearly, respond with the exact word: NONE."""
            try:
                resp = model.generate_content([prompt, image])
                ai_result = resp.text.strip().upper()
                if ai_result == "NONE":
                    st.error("The AI couldn't clearly see a diplomatic plate. Try typing it above!")
                else:
                    vt, code, country, amb = get_diplomat_info(ai_result)
                    if code and country != "Unknown Code":
                        record_scan(code, country)
                        display_result(vt, code, country, amb, ai_result)
                    elif code and country == "Unknown Code":
                        st.warning(f"Plate read as '{ai_result}', but the code is not in the database.")
                    else:
                        st.error(f"AI read '{ai_result}', but it doesn't match a diplomatic format.")
            except Exception as e:
                st.error(f"An error occurred: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#               LEADERBOARD PAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif st.session_state.page == "leaderboard":

    col_back, col_rest = st.columns([0.1, 0.9])
    with col_back:
        st.button("←", on_click=go_home, help="Back to home")

    st.markdown(f"""
    <div class="plate-frame" style="margin-bottom:4px;">
        <div class="plate-inner">
            {render_plate_stripe()}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    time_filter = st.segmented_control("Period", options=["Today","This Month","All Time"], default="All Time", label_visibility="collapsed")

    try:
        resp = supabase.table("scans").select("*").execute()
        data = resp.data
        if data:
            df = pd.DataFrame(data)
            if "created_at" in df.columns:
                df["created_at"] = pd.to_datetime(df["created_at"])
                now = datetime.utcnow()
                if time_filter == "Today":
                    df = df[df["created_at"].dt.date == now.date()]
                elif time_filter == "This Month":
                    df = df[(df["created_at"].dt.year==now.year)&(df["created_at"].dt.month==now.month)]

            if len(df) == 0:
                st.info(f"No scans recorded for '{time_filter}' yet.")
            else:
                lb = df["country"].value_counts().reset_index()
                lb.columns = ["Country","Scans"]
                ts = int(lb["Scans"].sum())
                tc = len(lb)
                top = lb.iloc[0]["Country"]

                m1,m2,m3 = st.columns(3)
                m1.metric("Total Scans", ts)
                m2.metric("Countries Spotted", tc)
                m3.metric("Most Spotted", top)

                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                mx = int(lb["Scans"].max())

                for i, row in lb.iterrows():
                    rank = i+1
                    pct = int((row["Scans"]/mx)*100)
                    badge = "rank-1" if rank==1 else "rank-2" if rank==2 else "rank-3" if rank==3 else "rank-other"
                    ri2, _ = get_iso_codes(row["Country"])
                    fh = ""
                    if ri2: fh = f'<img src="https://flagcdn.com/w40/{ri2.lower()}.png" width="24" style="border-radius:2px;vertical-align:middle;margin-right:4px;">'
                    elif row["Country"] in ORG_ICONS: fh = f'<span style="margin-right:4px;">{ORG_ICONS[row["Country"]]}</span>'

                    st.markdown(f"""
                    <div class="leader-row">
                        <div class="rank-badge {badge}">{rank}</div>
                        {fh}
                        <span style="font-size:14px;font-weight:600;color:#0a1628;flex:1;">{row['Country']}</span>
                        <div class="leader-bar-bg"><div class="leader-bar-fill" style="width:{pct}%;"></div></div>
                        <span style="font-size:14px;font-weight:700;color:#0a1628;min-width:28px;text-align:right;">{int(row['Scans'])}</span>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
                if st.button("🔄 Refresh"): st.rerun()
        else:
            st.info("No plates have been scanned yet. Be the first!")
    except Exception as e:
        st.error(f"Could not load leaderboard: {e}")
