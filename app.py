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
st.set_page_config(
    page_title="DiploCheck",
    page_icon="🌐",
    layout="centered"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    div[data-testid="stDecoration"] {display: none;}

    .diplo-card {
        background: white;
        border-radius: 14px;
        padding: 24px 28px;
        box-shadow: 0 1px 4px rgba(15,43,76,0.07);
        border: 1px solid #dce3ed;
        margin-bottom: 16px;
    }
    .diplo-card h3 { margin: 0 0 4px 0; font-size: 16px; color: #1a1a2e; }
    .diplo-card .subtitle { margin: 0 0 14px 0; font-size: 13px; color: #6b7a8d; }

    .or-divider {
        display: flex; align-items: center; gap: 16px;
        color: #6b7a8d; font-size: 13px; font-weight: 500; margin: 4px 0;
    }
    .or-divider .line { flex: 1; height: 1px; background: #dce3ed; }

    .leader-row {
        display: flex; align-items: center; gap: 14px;
        padding: 12px 0; border-bottom: 1px solid #eef1f6;
    }
    .leader-row:last-child { border-bottom: none; }
    .rank-badge {
        width: 28px; height: 28px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 12px; font-weight: 700; color: white; flex-shrink: 0;
    }
    .rank-1 { background: #d4a843; }
    .rank-2 { background: #a8b4c0; }
    .rank-3 { background: #c4956a; }
    .rank-other { background: #eef1f6; color: #6b7a8d; }
    .leader-bar-bg {
        width: 120px; height: 6px;
        background: #e8f0fa; border-radius: 3px; overflow: hidden;
    }
    .leader-bar-fill {
        height: 100%; border-radius: 3px;
        background: linear-gradient(90deg, #4a90d9, #0f2b4c);
    }

    div[data-testid="stMetric"] {
        background: #f5f7fb; border: 1px solid #dce3ed;
        border-radius: 12px; padding: 14px 16px;
    }

    .flag-img {
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.12);
    }

    .trivia-box {
        background: #f0f5ff;
        border-left: 4px solid #4a90d9;
        border-radius: 0 10px 10px 0;
        padding: 16px 20px;
        margin-top: 16px;
        font-size: 14px;
        color: #1a1a2e;
        line-height: 1.5;
    }
    .trivia-box .trivia-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600;
        color: #4a90d9;
        margin-bottom: 6px;
    }
</style>
""", unsafe_allow_html=True)

# --- SETUP APIS ---
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

supabase_url = st.secrets["supabase"]["URL"]
supabase_key = st.secrets["supabase"]["KEY"]
supabase: Client = create_client(supabase_url, supabase_key)

# --- OFM CODES ---
ofm_codes = {
    "AA": "Congo, Democratic Republic of the",
    "AC": "Ivory Coast",
    "AF": "Japan",
    "AH": "Madagascar",
    "AJ": "Panama",
    "AK": "Cape Verde",
    "AQ": "Syria",
    "AU": "Uganda",
    "AV": "Israel",
    "AW": "Organization of African Unity",
    "AX": "Marshall Islands",
    "BL": "South Africa",
    "BW": "World Bank",
    "BY": "Solomon Islands",
    "BZ": "Iraq",
    "CB": "Cambodia",
    "CC": "Ethiopia",
    "CG": "Marshall Islands",
    "CM": "Micronesia",
    "CN": "International Organization Staff",
    "CS": "Afghanistan",
    "CT": "Bhutan",
    "CU": "Botswana",
    "CV": "Myanmar",
    "CW": "Cameroon",
    "CX": "Burundi",
    "CY": "China",
    "DA": "Colombia",
    "DB": "Costa Rica",
    "DC": "Cuba",
    "DD": "Cyprus",
    "DF": "Dominican Republic",
    "DG": "Ecuador",
    "DH": "French Caribbean",
    "DI": "Israel",
    "DJ": "France",
    "DK": "Greece",
    "DL": "India",
    "DM": "Iran",
    "DN": "Denmark",
    "DP": "Bangladesh",
    "DR": "Slovakia",
    "DZ": "Palau",
    "FC": "U.S.S.R. (Discontinued)",
    "FF": "Antigua and Barbuda",
    "FG": "Central African Republic",
    "FH": "Ireland",
    "FI": "Israel",
    "FJ": "Lebanon",
    "FK": "Kenya",
    "FL": "Liberia",
    "FM": "Libya",
    "FN": "Malta",
    "FP": "Morocco",
    "FR": "Philippines",
    "FS": "Netherlands",
    "FT": "Qatar",
    "FV": "Sri Lanka",
    "FW": "Holy See (Vatican)",
    "FX": "Sierra Leone",
    "FY": "South Africa (Discontinued)",
    "FZ": "Suriname",
    "GC": "Sweden",
    "GD": "Ukraine",
    "GG": "Zambia",
    "GM": "Turkey",
    "GN": "Turkey",
    "GP": "Albania",
    "GQ": "North Korea",
    "GX": "Vanuatu",
    "HB": "Tonga",
    "HL": "St. Lucia",
    "HN": "Mongolia",
    "HV": "Belgium",
    "HW": "Guatemala",
    "HX": "Benin",
    "HY": "Guinea-Bissau",
    "HZ": "Haiti",
    "JB": "Honduras",
    "JC": "Kuwait",
    "JD": "Mauritius",
    "JF": "Nigeria",
    "JG": "Portugal",
    "JH": "Somalia",
    "JJ": "Chad",
    "JK": "Turkey",
    "JM": "Yugoslavia",
    "JP": "Tunisia",
    "JQ": "Togo",
    "JS": "Slovenia",
    "KB": "Monaco",
    "KD": "Eritrea",
    "KG": "Equatorial Guinea",
    "KH": "Hungary",
    "KJ": "Lithuania",
    "KK": "Fiji",
    "KL": "Jordan",
    "KM": "Jamaica",
    "KN": "Gabon",
    "KP": "Luxembourg",
    "KR": "Malaysia",
    "KS": "Mexico",
    "KT": "Namibia",
    "KU": "Sao Tome et Principe",
    "KV": "Saudi Arabia",
    "KW": "Seychelles",
    "KX": "Sudan",
    "LC": "Venezuela",
    "LD": "Vietnam",
    "LG": "Turkey",
    "LH": "Israel",
    "LK": "European Union",
    "LM": "Macedonia",
    "LR": "Bosnia and Herzegovina",
    "LW": "Germany",
    "MF": "International Monetary Fund",
    "MK": "Djibouti",
    "ML": "Diego Garcia",
    "MN": "Comoros",
    "MP": "Bahamas",
    "MQ": "Monaco",
    "MW": "Maledives",
    "NA": "Oman",
    "NB": "Papua New Guinea",
    "NC": "Paraguay",
    "ND": "Romania",
    "NQ": "Angola",
    "PA": "Austria",
    "PB": "Barbados",
    "PC": "Belize",
    "PD": "Bermuda",
    "PF": "Bolivia",
    "PG": "Belarus",
    "PH": "Czech Republic",
    "PI": "Israel",
    "PK": "Norway",
    "PL": "Chile",
    "PM": "Brunei",
    "PR": "Argentina",
    "PS": "Zimbabwe",
    "PV": "Congo, Republic of",
    "QA": "Yemen",
    "QD": "Burkina Faso",
    "QL": "St. Kitts and Nevis",
    "QM": "Bulgaria",
    "QN": "Laos",
    "QP": "Latvia",
    "QQ": "Lesotho",
    "QR": "Malawi",
    "QS": "Mozambique",
    "QT": "New Zealand",
    "QU": "Nicaragua",
    "QV": "Niger",
    "QW": "Poland",
    "QX": "Pakistan",
    "QY": "South Yemen (Discontinued)",
    "QZ": "Indonesia",
    "RB": "Rwanda",
    "RC": "St. Vincent and the Grenadines",
    "RD": "Senegal",
    "RL": "Uruguay",
    "SG": "Israel",
    "ST": "Dominica",
    "SX": "U.S.S.R. (Discontinued)",
    "TC": "Mali",
    "TF": "Algeria",
    "TG": "Canada",
    "TH": "Egypt",
    "TJ": "East Germany (Discontinued)",
    "TK": "Netherlands Antilles",
    "TL": "El Salvador",
    "TM": "Iceland",
    "TN": "Nepal",
    "TP": "Mauritania",
    "TQ": "Mali",
    "TR": "Italy",
    "TS": "Iraq (Discontinued)",
    "TT": "Guyana",
    "TU": "Guinea",
    "TV": "Ghana",
    "TW": "Gambia",
    "TX": "Finland",
    "TY": "Grenada",
    "TZ": "Peru",
    "UA": "Bahrain",
    "UF": "Estonia",
    "UH": "Spain",
    "UX": "Trinidad and Tobago",
    "VF": "Thailand",
    "VG": "Tanzania",
    "VH": "Switzerland",
    "VJ": "Brazil",
    "VK": "Singapore",
    "VL": "Swaziland",
    "VM": "Nauru",
    "WB": "United Arab Emirates",
    "WD": "South Korea",
    "WM": "Western Samoa",
    "WZ": "United Kingdom",
    "XF": "Turkey",
    "XY": "Unknown",
    "XZ": "Australia",
    "YA": "Unknown",
    "YG": "Georgia",
    "YJ": "Tajikistan",
    "YK": "Kazakhstan",
    "YM": "Hong Kong / Moldova",
    "YR": "Russia",
    "YT": "Turkmenistan",
    "YU": "Uzbekistan",
    "YY": "Kyrgyzstan",
    "YZ": "Azerbaijan"
}

plate_types = {
    "D": "Diplomat",
    "C": "Consular",
    "S": "Embassy Staff",
    "A": "UN Secretariat"
}

# Organizations (not countries — skip map, use org trivia)
ORGANIZATIONS = {
    "Organization of African Unity",
    "World Bank",
    "International Organization Staff",
    "International Monetary Fund",
    "European Union",
    "U.S.S.R. (Discontinued)",
    "South Africa (Discontinued)",
    "South Yemen (Discontinued)",
    "East Germany (Discontinued)",
    "Iraq (Discontinued)",
}

# Manual overrides for country names that pycountry struggles with
COUNTRY_NAME_OVERRIDES = {
    "Ivory Coast": "CI",
    "Congo, Democratic Republic of the": "CD",
    "Congo, Republic of": "CG",
    "North Korea": "KP",
    "South Korea": "KR",
    "Syria": "SY",
    "Myanmar": "MM",
    "Bolivia": "BO",
    "Iran": "IR",
    "Venezuela": "VE",
    "Vietnam": "VN",
    "Tanzania": "TZ",
    "Laos": "LA",
    "Moldova": "MD",
    "Hong Kong / Moldova": "MD",
    "Holy See (Vatican)": "VA",
    "Macedonia": "MK",
    "French Caribbean": "GP",
    "Swaziland": "SZ",
    "Western Samoa": "WS",
    "Maledives": "MV",
    "Diego Garcia": "IO",
    "Netherlands Antilles": "AN",
    "Bermuda": "BM",
    "Sao Tome et Principe": "ST",
    "Cape Verde": "CV",
    "Micronesia": "FM",
    "Guinea-Bissau": "GW",
    "Bosnia and Herzegovina": "BA",
    "Trinidad and Tobago": "TT",
    "St. Lucia": "LC",
    "St. Kitts and Nevis": "KN",
    "St. Vincent and the Grenadines": "VC",
    "Antigua and Barbuda": "AG",
    "Central African Republic": "CF",
    "Equatorial Guinea": "GQ",
    "United Arab Emirates": "AE",
    "Papua New Guinea": "PG",
    "Dominican Republic": "DO",
    "El Salvador": "SV",
    "Czech Republic": "CZ",
    "Burkina Faso": "BF",
    "Sierra Leone": "SL",
    "South Africa": "ZA",
    "Sri Lanka": "LK",
    "Saudi Arabia": "SA",
    "New Zealand": "NZ",
    "Marshall Islands": "MH",
    "Solomon Islands": "SB",
    "Costa Rica": "CR",
}


def get_iso_codes(country_name):
    """Return (iso_alpha2, iso_alpha3) for a country name, or (None, None)."""
    if country_name in ORGANIZATIONS or country_name == "Unknown Code" or country_name == "Unknown":
        return None, None

    # Check manual overrides first
    if country_name in COUNTRY_NAME_OVERRIDES:
        a2 = COUNTRY_NAME_OVERRIDES[country_name]
        try:
            c = pycountry.countries.get(alpha_2=a2)
            return c.alpha_2, c.alpha_3
        except:
            return a2, None

    # Try pycountry lookup
    try:
        results = pycountry.countries.search_fuzzy(country_name)
        if results:
            return results[0].alpha_2, results[0].alpha_3
    except:
        pass

    return None, None


def get_flag_url(iso2):
    """Return a flag image URL from flagcdn."""
    if iso2:
        return f"https://flagcdn.com/w320/{iso2.lower()}.png"
    return None


def render_world_map(iso3, country_name):
    """Render a plotly choropleth highlighting one country."""
    fig = go.Figure(go.Choropleth(
        locations=[iso3],
        z=[1],
        colorscale=[[0, "#4a90d9"], [1, "#4a90d9"]],
        showscale=False,
        marker_line_color="#dce3ed",
        marker_line_width=0.5,
        hovertext=[country_name],
        hoverinfo="text",
    ))
    fig.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#dce3ed",
            projection_type="natural earth",
            landcolor="#f5f7fb",
            oceancolor="#e8f0fa",
            showocean=True,
            showcountries=True,
            countrycolor="#dce3ed",
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


def get_trivia(name, is_org=False):
    """Ask Gemini for a single fun trivia fact."""
    seed = random.randint(1, 10000)
    if is_org:
        prompt = f"Give me one surprising and fun trivia fact about the organization '{name}'. Keep it to 1-2 sentences. Be specific and interesting. Random seed: {seed}. Respond with ONLY the fact, no preamble."
    else:
        prompt = f"Give me one surprising and fun trivia fact about the country '{name}'. Keep it to 1-2 sentences. Be specific and interesting. Random seed: {seed}. Respond with ONLY the fact, no preamble."
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return None


# Org flag/logo emoji fallback
ORG_ICONS = {
    "World Bank": "🏦",
    "International Monetary Fund": "💰",
    "European Union": "🇪🇺",
    "Organization of African Unity": "🌍",
    "International Organization Staff": "🏛️",
    "U.S.S.R. (Discontinued)": "☭",
    "South Africa (Discontinued)": "🇿🇦",
    "South Yemen (Discontinued)": "🇾🇪",
    "East Germany (Discontinued)": "🇩🇪",
    "Iraq (Discontinued)": "🇮🇶",
}


# --- HELPERS ---
def record_scan(code, country):
    try:
        supabase.table("scans").insert({"code": code, "country": country}).execute()
    except Exception:
        pass


def get_diplomat_info(plate_text):
    clean_text = plate_text.replace(" ", "").upper()
    match_standard = re.search(r'^([ADCS])([A-Z]{2})(\d+)$', clean_text)
    match_reversed = re.search(r'^(\d+)([A-Z]{2})([ADCS])$', clean_text)

    if match_standard:
        type_code, country_code, digits = match_standard.group(1), match_standard.group(2), match_standard.group(3)
    elif match_reversed:
        digits, country_code, type_code = match_reversed.group(1), match_reversed.group(2), match_reversed.group(3)
    else:
        return None, None, "Format not recognized.", False

    vehicle_type = plate_types.get(type_code, "Unknown")
    country = ofm_codes.get(country_code, "Unknown Code")

    is_ambassador = False
    if digits in ("0001", "1"):
        is_ambassador = True
        vehicle_type = "👑 Ambassador (" + vehicle_type + ")"

    return vehicle_type, country_code, country, is_ambassador


def display_result(vehicle_type, code, country, is_ambassador):
    """Shared result display: metrics + flag + map + trivia."""
    if is_ambassador:
        st.balloons()
        st.success("🌟 You spotted an Ambassador's official vehicle!")
    else:
        st.success("✅ Match found!")

    # Metrics row
    c1, c2, c3 = st.columns(3)
    c1.metric("Type", vehicle_type)
    c2.metric("Code", code)
    c3.metric("Country", country)

    is_org = country in ORGANIZATIONS
    iso2, iso3 = get_iso_codes(country)

    # Flag + Map row
    flag_url = get_flag_url(iso2)

    if flag_url and iso3:
        # Country: flag on left, map on right
        col_flag, col_map = st.columns([1, 2])
        with col_flag:
            st.markdown(f'<img src="{flag_url}" class="flag-img" width="100%">', unsafe_allow_html=True)
        with col_map:
            render_world_map(iso3, country)
    elif flag_url:
        # Have flag but no map data
        st.markdown(f'<img src="{flag_url}" class="flag-img" width="200">', unsafe_allow_html=True)
    elif is_org:
        # Organization: show icon
        icon = ORG_ICONS.get(country, "🏛️")
        st.markdown(f"<div style='font-size:64px; text-align:center; margin:16px 0;'>{icon}</div>", unsafe_allow_html=True)

    # Trivia
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


def go_home():
    st.session_state.page = "home"

def go_scan():
    st.session_state.page = "scan"

def go_leaderboard():
    st.session_state.page = "leaderboard"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#                  LANDING PAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if st.session_state.page == "home":

    st.markdown("<div style='height:50px'></div>", unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 1, 1])
    with col_c:
        st.image("logo.png", width=130)

    st.markdown("""
    <div style="text-align:center; margin-top:8px;">
        <h1 style="font-size:38px; color:#0f2b4c; margin:0 0 8px; font-weight:800; letter-spacing:0.02em;">
            DiploCheck
        </h1>
        <p style="font-size:16px; color:#6b7a8d; margin:0 0 44px; letter-spacing:0.01em;">
            Identify diplomatic license plates in the U.S.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="medium")
    with col1:
        st.markdown("""
        <div style="background:white; border-radius:14px; padding:32px 20px; text-align:center;
                    box-shadow:0 2px 8px rgba(15,43,76,0.08); border:1px solid #dce3ed;">
            <div style="font-size:36px; margin-bottom:12px;">🔍</div>
            <h3 style="margin:0 0 6px; color:#0f2b4c; font-size:18px;">Check a Plate</h3>
            <p style="margin:0; font-size:13px; color:#6b7a8d;">Type or snap a diplomatic plate</p>
        </div>
        """, unsafe_allow_html=True)
        st.button("Check a Plate →", on_click=go_scan, use_container_width=True, type="primary")

    with col2:
        st.markdown("""
        <div style="background:white; border-radius:14px; padding:32px 20px; text-align:center;
                    box-shadow:0 2px 8px rgba(15,43,76,0.08); border:1px solid #dce3ed;">
            <div style="font-size:36px; margin-bottom:12px;">🏆</div>
            <h3 style="margin:0 0 6px; color:#0f2b4c; font-size:18px;">Leaderboard</h3>
            <p style="margin:0; font-size:13px; color:#6b7a8d;">See the most spotted nations</p>
        </div>
        """, unsafe_allow_html=True)
        st.button("Leaderboard →", on_click=go_leaderboard, use_container_width=True, type="primary")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#                  SCAN PAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif st.session_state.page == "scan":

    col_back, col_logo, col_title = st.columns([0.1, 0.06, 0.84])
    with col_back:
        st.button("←", on_click=go_home, help="Back to home")
    with col_logo:
        st.image("logo.png", width=32)
    with col_title:
        st.markdown("<h1 style='margin:0; font-size:22px; color:#0f2b4c;'>Check a Plate</h1>", unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Text input
    st.markdown('<div class="diplo-card"><h3>⌨️ Type a Plate Number</h3><p class="subtitle">Letters and numbers only — we\'ll figure out the format</p></div>', unsafe_allow_html=True)
    manual_input = st.text_input("Plate number", placeholder="e.g. DAF 1234, AXX 0001, or 1234 AFD", label_visibility="collapsed")

    if manual_input:
        vehicle_type, code, country, is_ambassador = get_diplomat_info(manual_input)
        if code and country != "Unknown Code":
            record_scan(code, country)
            display_result(vehicle_type, code, country, is_ambassador)
        else:
            st.error("Could not recognize a valid diplomatic plate format.")

    st.markdown('<div class="or-divider"><div class="line"></div>or<div class="line"></div></div>', unsafe_allow_html=True)

    # Upload / camera
    st.markdown('<div class="diplo-card"><h3>📷 Upload or Take a Photo</h3><p class="subtitle">Snap a plate and let AI read it for you</p></div>', unsafe_allow_html=True)

    up_col, cam_col = st.columns(2)
    with up_col:
        uploaded_file = st.file_uploader("Upload", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    with cam_col:
        camera_file = st.camera_input("Camera", label_visibility="collapsed")

    image_to_process = uploaded_file or camera_file

    if image_to_process:
        image = Image.open(image_to_process)
        st.image(image, caption="Captured Plate", use_container_width=True)

        with st.spinner("🔍 Analyzing with Google AI..."):
            prompt = """
            Look at this image of a vehicle or license plate. Find the US diplomatic license plate.
            It will either be in the format "[Letter][Two Letters] [Numbers]" (like DAF 1234)
            OR reversed "[Numbers] [Two Letters][Letter]" (like 1234 AFD).
            Respond ONLY with the exact text written on the license plate (letters and numbers).
            If you cannot read it clearly, respond with the exact word: NONE.
            """
            try:
                response = model.generate_content([prompt, image])
                ai_result = response.text.strip().upper()

                if ai_result == "NONE":
                    st.error("The AI couldn't clearly see a diplomatic plate. Try typing it above!")
                else:
                    vehicle_type, code, country, is_ambassador = get_diplomat_info(ai_result)
                    if code and country != "Unknown Code":
                        record_scan(code, country)
                        display_result(vehicle_type, code, country, is_ambassador)
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

    col_back, col_logo, col_title = st.columns([0.1, 0.06, 0.84])
    with col_back:
        st.button("←", on_click=go_home, help="Back to home")
    with col_logo:
        st.image("logo.png", width=32)
    with col_title:
        st.markdown("<h1 style='margin:0; font-size:22px; color:#0f2b4c;'>Leaderboard</h1>", unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    time_filter = st.segmented_control(
        "Period",
        options=["Today", "This Month", "All Time"],
        default="All Time",
        label_visibility="collapsed"
    )

    try:
        response = supabase.table("scans").select("*").execute()
        data = response.data

        if data:
            df = pd.DataFrame(data)

            if "created_at" in df.columns:
                df["created_at"] = pd.to_datetime(df["created_at"])
                now = datetime.utcnow()

                if time_filter == "Today":
                    df = df[df["created_at"].dt.date == now.date()]
                elif time_filter == "This Month":
                    df = df[
                        (df["created_at"].dt.year == now.year) &
                        (df["created_at"].dt.month == now.month)
                    ]

            if len(df) == 0:
                st.info(f"No scans recorded for '{time_filter}' yet.")
            else:
                leaderboard = df["country"].value_counts().reset_index()
                leaderboard.columns = ["Country", "Scans"]

                total_scans = int(leaderboard["Scans"].sum())
                total_countries = len(leaderboard)
                top_country = leaderboard.iloc[0]["Country"]

                m1, m2, m3 = st.columns(3)
                m1.metric("Total Scans", total_scans)
                m2.metric("Countries Spotted", total_countries)
                m3.metric("Most Spotted", top_country)

                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

                max_scans = int(leaderboard["Scans"].max())

                for i, row in leaderboard.iterrows():
                    rank = i + 1
                    pct = int((row["Scans"] / max_scans) * 100)
                    badge = "rank-1" if rank == 1 else "rank-2" if rank == 2 else "rank-3" if rank == 3 else "rank-other"

                    # Get flag for leaderboard row
                    row_iso2, _ = get_iso_codes(row["Country"])
                    flag_html = ""
                    if row_iso2:
                        flag_html = f'<img src="https://flagcdn.com/w40/{row_iso2.lower()}.png" width="24" style="border-radius:2px; vertical-align:middle; margin-right:4px;">'
                    elif row["Country"] in ORG_ICONS:
                        flag_html = f'<span style="margin-right:4px;">{ORG_ICONS[row["Country"]]}</span>'

                    st.markdown(f"""
                    <div class="leader-row">
                        <div class="rank-badge {badge}">{rank}</div>
                        {flag_html}
                        <span style="font-size:14px; font-weight:600; color:#1a1a2e; flex:1;">{row['Country']}</span>
                        <div class="leader-bar-bg">
                            <div class="leader-bar-fill" style="width:{pct}%;"></div>
                        </div>
                        <span style="font-size:14px; font-weight:700; color:#0f2b4c; min-width:28px; text-align:right;">{int(row['Scans'])}</span>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
                if st.button("🔄 Refresh"):
                    st.rerun()
        else:
            st.info("No plates have been scanned yet. Be the first!")

    except Exception as e:
        st.error(f"Could not load leaderboard: {e}")
