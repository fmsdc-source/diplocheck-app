import streamlit as st
import google.generativeai as genai
from PIL import Image

# Pull the API key from Streamlit's hidden secrets vault
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# 2. The Database (Keep your massive dictionary here!)
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

# 3. Streamlit App UI
st.title("US Diplomatic Plate Identifier 🚗🌍")
st.write("Upload a photo to find out the diplomat's country!")

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
camera_file = st.camera_input("Take a picture")

image_to_process = uploaded_file or camera_file

if image_to_process:
    # Read the image
    image = Image.open(image_to_process)
    st.image(image, caption='Captured Plate', use_container_width=True)
    
    st.write("Analyzing image with Google AI...")
    
    # 4. Ask Gemini to find the code!
    prompt = """
    Look at this image of a vehicle or license plate. 
    Find the US diplomatic license plate. 
    It will start with D, C, or S, followed by two letters, followed by numbers.
    Respond ONLY with the two uppercase letters that represent the country code. 
    If you cannot read it clearly, respond with the exact word: NONE.
    """
    
    try:
        response = model.generate_content([prompt, image])
        ai_result = response.text.strip().upper()
        
        if ai_result == "NONE":
            st.error("The AI couldn't clearly see a diplomatic plate in this image. Try another angle!")
        elif len(ai_result) == 2: # Make sure it just gave us the two letters
            country = ofm_codes.get(ai_result, "Unknown Code (Not in database)")
            
            # Using the clean Metrics layout we talked about!
            st.write("### Match Found!")
            col1, col2 = st.columns(2)
            col1.metric(label="Plate Code", value=ai_result)
            col2.metric(label="Accredited Country", value=country)
        else:
            st.warning(f"Unexpected AI response: {ai_result}")
            
    except Exception as e:
        st.error(f"An error occurred while talking to the AI: {e}")