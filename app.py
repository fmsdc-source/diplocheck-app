import streamlit as st
import google.generativeai as genai
from PIL import Image
import re
from supabase import create_client, Client

# --- 1. SETUP APIS & DATABASE ---
# Gemini
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Supabase
supabase_url = st.secrets["supabase"]["URL"]
supabase_key = st.secrets["supabase"]["KEY"]
supabase: Client = create_client(supabase_url, supabase_key)

# The Database
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

# --- 3. HELPER FUNCTIONS ---
def record_scan(code, country):
    """Sends the successful scan to our Supabase database."""
    try:
        # Insert a new row into the 'scans' table
        supabase.table("scans").insert({"code": code, "country": country}).execute()
    except Exception as e:
        st.write("*(Note: Could not connect to scoreboard database.)*")

def get_diplomat_country(plate_text):
    clean_text = plate_text.replace(" ", "").upper()
    match = re.search(r'^[DCS]([A-Z]{2})\d+$', clean_text)
    
    if match:
        country_code = match.group(1)
        country = ofm_codes.get(country_code, "Unknown Code")
        return country_code, country
    return None, "Format not recognized."

# --- 4. APP UI & LAYOUT ---
st.title("US Diplomatic Plate Identifier 🚗🌍")

# Add your logo (Make sure logo.png is in your folder!)
# col1, col2, col3 = st.columns([1, 2, 1])
# with col2:
#     st.image("logo.png", use_container_width=True)

# Create two tabs at the top of the app
tab1, tab2 = st.tabs(["🔍 Scan a Plate", "🏆 Leaderboard"])

# --- TAB 1: THE SCANNER ---
with tab1:
    st.write("Enter a plate number or upload a photo to find out the diplomat's country!")

    # Text Input Mode
    st.subheader("Type the License Plate")
    manual_input = st.text_input("Example: DAF 1234")
    
    if manual_input:
        code, country = get_diplomat_country(manual_input)
        if code and country != "Unknown Code":
            record_scan(code, country) # Save to database!
            
            st.write("### Match Found!")
            col1, col2 = st.columns(2)
            col1.metric(label="Plate Code", value=code)
            col2.metric(label="Accredited Country", value=country)
        else:
            st.error("Could not recognize a valid diplomatic plate format.")

    st.divider()

    # Camera / Photo Upload Mode
    st.subheader("Or Upload/Take a Photo")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    camera_file = st.camera_input("Take a picture")

    image_to_process = uploaded_file or camera_file

    if image_to_process:
        image = Image.open(image_to_process)
        st.image(image, caption='Captured Plate', use_container_width=True)
        st.write("Analyzing image with Google AI...")
        
        prompt = """
        Look at this image of a vehicle or license plate. Find the US diplomatic license plate. 
        It will start with D, C, or S, followed by two letters, followed by numbers.
        Respond ONLY with the two uppercase letters that represent the country code. 
        If you cannot read it clearly, respond with the exact word: NONE.
        """
        try:
            response = model.generate_content([prompt, image])
            ai_result = response.text.strip().upper()
            
            if ai_result == "NONE":
                st.error("The AI couldn't clearly see a diplomatic plate. Try typing it above!")
            elif len(ai_result) == 2:
                country = ofm_codes.get(ai_result, "Unknown Code")
                if country != "Unknown Code":
                    record_scan(ai_result, country) # Save to database!
                    
                    st.write("### Match Found!")
                    col1, col2 = st.columns(2)
                    col1.metric(label="Plate Code", value=ai_result)
                    col2.metric(label="Accredited Country", value=country)
                else:
                    st.warning("Found code but it is not in the database.")
        except Exception as e:
            st.error("An error occurred with the AI.")

# --- TAB 2: THE LEADERBOARD ---
with tab2:
    st.header("Most Looked-Up Countries")
    st.write("See which nations are being spotted the most!")
    
    if st.button("Refresh Scoreboard"):
        try:
            # Pull all the data from Supabase
            response = supabase.table("scans").select("*").execute()
            data = response.data
            
            if data:
                import pandas as pd
                # Convert database data into a pandas dataframe
                df = pd.DataFrame(data)
                
                # Count how many times each country appears
                leaderboard = df['country'].value_counts().reset_index()
                leaderboard.columns = ['Country', 'Scans']
                
                # Display the data nicely
                st.dataframe(
                    leaderboard, 
                    use_container_width=True, 
                    hide_index=True,
                )
                
                # Create a simple bar chart
                st.bar_chart(leaderboard, x='Country', y='Scans')
            else:
                st.info("No plates have been scanned yet. Be the first!")
                
        except Exception as e:
            st.error(f"Could not load leaderboard: {e}")