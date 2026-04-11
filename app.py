import streamlit as st
import google.generativeai as genai
from PIL import Image
import re
from supabase import create_client, Client

# --- PAGE CONFIG (must be first Streamlit command) ---
st.set_page_config(
    page_title="DiploCheck",
    page_icon="🌐",
    layout="centered"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Hide Streamlit chrome */
    #MainMenu, footer, header {visibility: hidden;}
    div[data-testid="stDecoration"] {display: none;}

    /* Custom header bar */
    .diplo-header {
        background: linear-gradient(135deg, #0f2b4c 0%, #163a64 100%);
        padding: 20px 28px 14px;
        border-radius: 0 0 16px 16px;
        margin: -1rem -1rem 1.5rem -1rem;
    }
    .diplo-header-row {/Users/frieder/Desktop/DiploApp/.streamlit
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .diplo-header img {
        width: 42px;
        border-radius: 4px;
    }
    .diplo-header h1 {
        margin: 0;
        font-size: 26px;
        color: white;
        font-weight: 700;
        letter-spacing: 0.02em;
    }
    .diplo-header .tagline {
        margin: 4px 0 0 0;
        font-size: 13px;
        color: #b8c4d4;
        letter-spacing: 0.01em;
    }
    .diplo-badge {
        margin-left: auto;
        font-size: 11px;
        color: #b8c4d4;
        background: rgba(255,255,255,0.08);
        padding: 4px 12px;
        border-radius: 20px;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        font-weight: 600;
    }

    /* Card styling */
    .diplo-card {
        background: white;
        border-radius: 14px;
        padding: 24px 28px;
        box-shadow: 0 1px 4px rgba(15,43,76,0.07);
        border: 1px solid #dce3ed;
        margin-bottom: 16px;
    }
    .diplo-card h3 {
        margin: 0 0 4px 0;
        font-size: 16px;
        color: #1a1a2e;
    }
    .diplo-card .subtitle {
        margin: 0 0 14px 0;
        font-size: 13px;
        color: #6b7a8d;
    }

    /* Divider with "or" */
    .or-divider {
        display: flex;
        align-items: center;
        gap: 16px;
        color: #6b7a8d;
        font-size: 13px;
        font-weight: 500;
        margin: 4px 0 4px 0;
    }
    .or-divider .line {
        flex: 1;
        height: 1px;
        background: #dce3ed;
    }

    /* Leaderboard row styling */
    .leader-row {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 12px 0;
        border-bottom: 1px solid #eef1f6;
    }
    .leader-row:last-child {
        border-bottom: none;
    }
    .rank-badge {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 700;
        color: white;
        flex-shrink: 0;
    }
    .rank-1 { background: #d4a843; }
    .rank-2 { background: #a8b4c0; }
    .rank-3 { background: #c4956a; }
    .rank-other { background: #eef1f6; color: #6b7a8d; }
    .leader-bar-bg {
        width: 120px;
        height: 6px;
        background: #e8f0fa;
        border-radius: 3px;
        overflow: hidden;
    }
    .leader-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #4a90d9, #0f2b4c);
        border-radius: 3px;
    }

    /* Tighter tab styling */
    div[data-baseweb="tab-list"] {
        gap: 0px;
    }
    
    /* Metric cards */
    div[data-testid="stMetric"] {
        background: #f5f7fb;
        border: 1px solid #dce3ed;
        border-radius: 12px;
        padding: 14px 16px;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. SETUP APIS & DATABASE ---
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

supabase_url = st.secrets["supabase"]["URL"]
supabase_key = st.secrets["supabase"]["KEY"]
supabase: Client = create_client(supabase_url, supabase_key)

# --- 2. THE DATABASE ---
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


def record_scan(code, country):
    """Sends the successful scan to our Supabase database."""
    try:
        supabase.table("scans").insert({"code": code, "country": country}).execute()
    except Exception as e:
        pass  # Silently fail — no ugly error text


def get_diplomat_info(plate_text):
    """Parses text to extract Type, Country, and check for Ambassador status."""
    clean_text = plate_text.replace(" ", "").upper()
    
    match_standard = re.search(r'^([ADCS])([A-Z]{2})(\d+)$', clean_text)
    match_reversed = re.search(r'^(\d+)([A-Z]{2})([ADCS])$', clean_text)
    
    if match_standard:
        type_code = match_standard.group(1)
        country_code = match_standard.group(2)
        digits = match_standard.group(3)
    elif match_reversed:
        digits = match_reversed.group(1)
        country_code = match_reversed.group(2)
        type_code = match_reversed.group(3)
    else:
        return None, None, "Format not recognized.", False
        
    vehicle_type = plate_types.get(type_code, "Unknown")
    country = ofm_codes.get(country_code, "Unknown Code")
    
    is_ambassador = False
    if digits == "0001" or digits == "1":
        is_ambassador = True
        vehicle_type = "👑 Ambassador (" + vehicle_type + ")"
        
    return vehicle_type, country_code, country, is_ambassador


# --- 3. BRANDED HEADER ---
col_logo, col_title = st.columns([0.08, 0.92])
with col_logo:
    st.image("logo.png", width=42)
with col_title:
    st.markdown("""
    <div>
        <h1 style="margin:0; font-size:26px; color:#0f2b4c; letter-spacing:0.02em;">DiploCheck</h1>
        <p style="margin:2px 0 0; font-size:13px; color:#6b7a8d;">Identify diplomatic license plates in the U.S.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# --- 4. TABS ---
tab1, tab2 = st.tabs(["🔍 Scan a Plate", "🏆 Leaderboard"])

# --- TAB 1: THE SCANNER ---
with tab1:

    # ── Text input card ──
    st.markdown('<div class="diplo-card"><h3>⌨️ Type a Plate Number</h3><p class="subtitle">Letters and numbers only — we\'ll figure out the format</p></div>', unsafe_allow_html=True)
    manual_input = st.text_input(
        "Plate number",
        placeholder="e.g. DAF 1234, AXX 0001, or 1234 AFD",
        label_visibility="collapsed"
    )
    
    if manual_input:
        vehicle_type, code, country, is_ambassador = get_diplomat_info(manual_input)
        if code and country != "Unknown Code":
            record_scan(code, country) 
            
            if is_ambassador:
                st.balloons()
                st.success("🌟 You spotted an Ambassador's official vehicle!")
            else:
                st.success("✅ Match found!")
                
            col1, col2, col3 = st.columns(3)
            col1.metric(label="Type", value=vehicle_type)
            col2.metric(label="Code", value=code)
            col3.metric(label="Country", value=country)
        else:
            st.error("Could not recognize a valid diplomatic plate format.") 

    # ── Or divider ──
    st.markdown('<div class="or-divider"><div class="line"></div>or<div class="line"></div></div>', unsafe_allow_html=True)

    # ── Upload card ──
    st.markdown('<div class="diplo-card"><h3>📷 Upload or Take a Photo</h3><p class="subtitle">Snap a plate and let AI read it for you</p></div>', unsafe_allow_html=True)
    
    upload_col, camera_col = st.columns(2)
    with upload_col:
        uploaded_file = st.file_uploader("Upload", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    with camera_col:
        camera_file = st.camera_input("Camera", label_visibility="collapsed")

    image_to_process = uploaded_file or camera_file

    if image_to_process:
        image = Image.open(image_to_process)
        st.image(image, caption='Captured Plate', use_container_width=True)
        
        with st.spinner("🔍 Analyzing image with Google AI..."):
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
                        
                        if is_ambassador:
                            st.balloons() 
                            st.success("🌟 You spotted an Ambassador's official vehicle!")
                        else:
                            st.success("✅ Match found!")
                            
                        col1, col2, col3 = st.columns(3)
                        col1.metric(label="Type", value=vehicle_type)
                        col2.metric(label="Code", value=code)
                        col3.metric(label="Country", value=country)
                    elif code and country == "Unknown Code":
                        st.warning(f"Plate read as '{ai_result}', but the code is not in the database.")
                    else:
                        st.error(f"AI read the text as '{ai_result}', but it doesn't match a diplomatic format.")
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")

# --- TAB 2: THE LEADERBOARD ---
with tab2:
    
    # Auto-load leaderboard (no button needed)
    try:
        response = supabase.table("scans").select("*").execute()
        data = response.data
        
        if data:
            import pandas as pd
            df = pd.DataFrame(data)
            leaderboard = df['country'].value_counts().reset_index()
            leaderboard.columns = ['Country', 'Scans']
            
            total_scans = int(leaderboard['Scans'].sum())
            total_countries = len(leaderboard)
            top_country = leaderboard.iloc[0]['Country'] if len(leaderboard) > 0 else "—"
            
            # ── Summary metrics ──
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Scans", total_scans)
            m2.metric("Countries Spotted", total_countries)
            m3.metric("Most Spotted", top_country)
            
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            
            # ── Ranked list with bars ──
            max_scans = int(leaderboard['Scans'].max())
            
            for i, row in leaderboard.iterrows():
                rank = i + 1
                pct = int((row['Scans'] / max_scans) * 100)
                
                if rank == 1:
                    badge_class = "rank-1"
                elif rank == 2:
                    badge_class = "rank-2"
                elif rank == 3:
                    badge_class = "rank-3"
                else:
                    badge_class = "rank-other"
                
                st.markdown(f"""
                <div class="leader-row">
                    <div class="rank-badge {badge_class}">{rank}</div>
                    <span style="font-size:14px; font-weight:600; color:#1a1a2e; flex:1;">{row['Country']}</span>
                    <div class="leader-bar-bg">
                        <div class="leader-bar-fill" style="width:{pct}%;"></div>
                    </div>
                    <span style="font-size:14px; font-weight:700; color:#0f2b4c; min-width:28px; text-align:right;">{int(row['Scans'])}</span>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            
            if st.button("🔄 Refresh", type="secondary"):
                st.rerun()
        else:
            st.info("No plates have been scanned yet. Be the first!")
            
    except Exception as e:
        st.error(f"Could not load leaderboard: {e}")
