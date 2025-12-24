import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from fuzzywuzzy import process, fuzz
import google.generativeai as genai
import json
import os

# --- 1. Safety & Initialization ---
# Initialize variables to prevent NameErrors
lat = 34.05
long = -118.25
diagnosis = None
severity = None
est_cost = None
top_hospitals = pd.DataFrame()

# Set page config
st.set_page_config(page_title="Pathfinder Health Agent", layout="wide")

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I'm your Pathfinder Health Agent. Describe your symptoms, and I'll help you find the right care."}]
if "diagnosis" not in st.session_state:
    st.session_state.diagnosis = None

# --- 2. Sidebar & Setup ---
with st.sidebar:
    st.title("⚙️ Settings")
    api_key = st.text_input("Google API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)
    
    st.markdown("---")
    st.subheader("Location")
    city_input = st.text_input("City or Zip Code", value="Los Angeles")
    
    # Load Data
    @st.cache_data
    def load_data():
        healthcare_df = pd.read_csv("optimized_healthcare_data.csv")
        hospital_info_df = pd.read_csv("optimized_hospital_info.csv")
        hospital_locations_df = pd.read_csv("optimized_hospital_locations.csv")
        insurance_df = pd.read_csv("optimized_insurance_data.csv")
        return healthcare_df, hospital_info_df, hospital_locations_df, insurance_df

    try:
        healthcare_df, hospital_info_df, hospital_locations_df, insurance_df = load_data()
        plans = insurance_df['plan_type'].unique()
        selected_plan = st.selectbox("Insurance Plan", plans)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

# --- 3. Logic Functions ---

def analyze_symptoms_with_gemini(history):
    if not api_key:
        return {"error": "Please enter your Google API Key in the sidebar."}
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        You are a medical triage assistant. Analyze the conversation history and the latest user input.
        
        Your goal is to identify the user's 'Medical Condition' from this list: {list(healthcare_df['Medical Condition'].unique())}.
        
        Output ONLY a JSON object with this structure:
        {{
            "condition": "closest_match_string_or_null",
            "severity": "Mild", "Moderate", "Severe", or "Emergency",
            "is_emergency": boolean,
            "follow_up_question": "string_if_more_info_needed_else_null",
            "reasoning": "brief_explanation"
        }}
        
        Rules:
        1. If the symptoms are vague, ask a relevant follow-up question. Set "condition" to null.
        2. If you have enough info, set "follow_up_question" to null and fill in "condition" and "severity".
        3. Be conservative. If it sounds serious, mark as Emergency.
        
        Conversation History:
        {history}
        """
        
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)}

@st.cache_data
def get_location_center(city_str, locations_df):
    city_str = city_str.strip()
    if city_str.isdigit():
        matches = locations_df[locations_df['ZIP'].astype(str) == city_str]
    else:
        matches = locations_df[locations_df['CITY'].str.lower() == city_str.lower()]
    
    if not matches.empty:
        return matches['LATITUDE'].mean(), matches['LONGITUDE'].mean(), matches
    else:
        return None, None, pd.DataFrame()

@st.cache_data
def process_hospital_data(info_df, loc_df, target_plan, center_lat, center_long):
    # Standardize ZIP
    info_df['ZIP Code'] = info_df['ZIP Code'].astype(str).str.zfill(5)
    loc_df['ZIP'] = loc_df['ZIP'].astype(str).str.zfill(5)
    
    # Join
    merged = pd.merge(info_df, loc_df, left_on='ZIP Code', right_on='ZIP', how='inner')
    
    # Fuzzy Match Address
    def get_address_score(row):
        return fuzz.token_set_ratio(str(row['Location']).lower(), str(row['ADDRESS']).lower())
    
    merged['Match Score'] = merged.apply(get_address_score, axis=1)
    final_hospitals = merged[merged['Match Score'] > 70].copy()
    
    # Scoring
    def parse_rating(rating):
        try: return float(rating)
        except: return 3.0
    
    final_hospitals['numeric_rating'] = final_hospitals['Hospital overall rating'].apply(parse_rating)
    
    # Network Logic
    def is_in_network(pid, plan):
        if plan in ['Gold', 'Platinum']: return True
        return (int(pid) % 2) == 0
        
    final_hospitals['In Network'] = final_hospitals['Provider ID'].apply(lambda x: is_in_network(x, target_plan))
    
    # Distance
    final_hospitals['distance'] = ((final_hospitals['LATITUDE'] - center_lat)**2 + (final_hospitals['LONGITUDE'] - center_long)**2)**0.5
    
    # Final Score
    def adjust_score(row):
        score = row['numeric_rating']
        if not row['In Network']: score -= 2.0
        score -= row['distance'] * 10
        return score
        
    final_hospitals['Final Score'] = final_hospitals.apply(adjust_score, axis=1)
    return final_hospitals.sort_values('Final Score', ascending=False).head(5)

# --- 4. Main UI ---
st.title("Pathfinder Health Agent 🏥")

# Chat Interface
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Describe your symptoms..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
        
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            history_str = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
            analysis = analyze_symptoms_with_gemini(history_str)
            
            if "error" in analysis:
                response_text = f"Error: {analysis['error']}"
            elif analysis.get("follow_up_question"):
                response_text = analysis["follow_up_question"]
            else:
                condition = analysis.get("condition")
                severity = analysis.get("severity")
                response_text = f"Based on your symptoms, this looks like **{condition}** ({severity}).\n\n{analysis.get('reasoning')}"
                st.session_state.diagnosis = analysis
                
            st.write(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
    if st.session_state.diagnosis:
        st.rerun()

# --- 5. Results Section ---
if st.session_state.diagnosis:
    st.markdown("---")
    st.header("Triage Results")
    
    diag = st.session_state.diagnosis
    condition = diag['condition']
    severity = diag['severity']
    
    # Calculate Cost
    condition_data = healthcare_df[healthcare_df['Medical Condition'] == condition]
    if not condition_data.empty:
        base_avg_cost = condition_data['Billing Amount'].mean()
        
        if severity == "Mild":
            est_cost = base_avg_cost / 20
            visit_type = "Urgent Care Visit"
        elif severity == "Moderate":
            est_cost = base_avg_cost / 5
            visit_type = "Specialist Visit"
        else:
            est_cost = base_avg_cost
            visit_type = "Hospital Admission"
    else:
        est_cost = 0
        visit_type = "Unknown"

    # Determine Location
    found_lat, found_long, city_hospitals = get_location_center(city_input, hospital_locations_df)
    if found_lat:
        lat, long = found_lat, found_long
    else:
        # Fallback to LA if city not found, but don't crash
        _, _, city_hospitals = get_location_center("Los Angeles", hospital_locations_df)
    
    # Get Hospitals
    if not city_hospitals.empty:
        target_locs = city_hospitals
    else:
        target_locs = hospital_locations_df
        
    top_hospitals = process_hospital_data(hospital_info_df, target_locs, selected_plan, lat, long)

    # Display Columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Map")
        m = folium.Map(location=[lat, long], zoom_start=12)
        folium.Marker([lat, long], popup="You", icon=folium.Icon(color="blue", icon="user")).add_to(m)
        
        if not top_hospitals.empty:
            for _, row in top_hospitals.iterrows():
                color = "green"
                if row['numeric_rating'] < 3: color = "red"
                elif not row['In Network']: color = "orange"
                
                folium.Marker(
                    [row['LATITUDE'], row['LONGITUDE']],
                    popup=f"<b>{row['NAME']}</b><br>Rating: {row['numeric_rating']}",
                    tooltip=row['NAME'],
                    icon=folium.Icon(color=color, icon="hospital-o", prefix="fa")
                ).add_to(m)
        st_folium(m, width=None, height=500)
        
    with col2:
        st.subheader("Details")
        st.metric("Condition", condition)
        st.metric("Severity", severity)
        st.metric("Est. Cost", f"${est_cost:,.0f}", help=visit_type)
        
        st.subheader("Top Hospitals")
        if not top_hospitals.empty:
            for _, row in top_hospitals.iterrows():
                st.markdown(f"**{row['NAME']}**")
                st.caption(f"⭐ {row['numeric_rating']} | {'✅ Network' if row['In Network'] else '⚠️ Out-of-Network'}")
                st.caption(f"{row['distance']:.1f} miles away")
                st.divider()
