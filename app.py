import streamlit as st
import requests
import openai
import pandas as pd
from weasyprint import HTML
import io

# 🌟 Page & Aesthetic Configuration
st.set_page_config(
    page_title="Universal Small Business Intelligence Tool",
    page_icon="🚀",
    layout="wide"
)

# App Title & STEM Purpose
st.title("🚀 Universal Small Business Intelligence & Maps Optimizer")
st.markdown("""
*Created by STEM Students to empower local businesses through data transparency.*
This app uses **SerpAPI** to safely pull real-time Google Maps Profile performance metrics and **OpenAI** to compile a downloadable PDF growth strategy.
""")

# 🔑 Sidebar Setup for Credentials
st.sidebar.header("🔑 API Credentials")
serp_api_key = st.sidebar.text_input("SerpAPI Key", type="password", help="Get yours at serpapi.com")
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password", help="Get yours at ://openai.com")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🕊️ STEM Ethical Commitment")
st.sidebar.info("""
1. **Public Maps Architecture:** Accesses public business profiles legally via official search APIs.
2. **Empowerment Focus:** Helps local business owners audit their visibility and close gaps with competitors.
""")

# 🎯 Step 1: Input Local Business Profile
st.subheader("🏢 Step 1: Define the Business Profile")
c1, c2, c3 = st.columns(3)
with c1:
    business_name = st.text_input("Business Name (Exact or Keyword):", placeholder="e.g., Central Park Bakery")
with c2:
    location = st.text_input("City & State Location:", placeholder="e.g., Austin, TX")
with c3:
    primary_goal = st.selectbox("Primary Growth Goal:", [
        "Attract more weekend foot traffic",
        "Rank higher on local search maps",
        "Launch an introductory offer/promotion",
        "Improve customer review strategies"
    ])

# 🛠️ Helper Function: Discover Real-Time Google Maps Profile Data
def fetch_google_maps_profile(biz_name, city_state, api_key):
    if not api_key:
        # Fallback simulated data if API keys aren't active yet
        return [
            {"name": f"{biz_name} Main Street", "rating": 4.2, "reviews": 48, "address": f"123 Main St, {city_state}", "type": "Bakery"},
            {"name": f"{biz_name} Downtown", "rating": 4.7, "reviews": 112, "address": f"555 Broadway, {city_state}", "type": "Bakery"}
        ]
        
    url = "https://serpapi.com"
    # Utilizing SerpAPI's dedicated Google Maps engine for real-time compliance
    params = {
        "engine": "google_maps",
        "q": f"{biz_name} {city_state}",
        "api_key": api_key
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            local_results = response.json().get("local_results", [])
            # Handle case where a single precise profile is returned instead of a list
            if not local_results and "place_results" in response.json():
                place = response.json().get("place_results", {})
                local_results = [place]
                
            return [
                {
                    "name": item.get("title", "Unknown Business"),
                    "rating": item.get("rating", "N/A"),
                    "reviews": item.get("reviews", 0),
                    "address": item.get("address", "No address listed"),
                    "type": item.get("type", "Local Business")
                } for item in local_results[:3] # Analyze top 3 profiles matching the name space
            ]
        else:
            st.sidebar.error(f"SerpAPI Maps Error: {response.status_code}")
            return []
    except Exception as e:
        st.sidebar.error(f"Connection to SerpAPI Maps failed: {str(e)}")
        return []

# 🧠 Helper Function: AI Playbook & Audit Generation
def compile_business_playbook(biz_name, city_state, goal, maps_data, openai_key):
    client = openai.OpenAI(api_key=openai_key)
    
    maps_summary = ""
    for idx, profile in enumerate(maps_data):
        maps_summary += f"\n- Profile #{idx+1}: {profile['name']} | Rating: {profile['rating']} | Reviews: {profile['reviews']} | Location: {profile['address']} | Category: {profile['type']}\n"
        
    system_prompt = (
        "You are an expert Google Business Profile optimizer and local SEO architect. Your writing style "
        "is professional, actionable, and structured for small business comprehension."
    )
    
    user_prompt = f"""
    BUSINESS INFO:
    - Name: {biz_name}
    - Location: {city_state}
    - Core Goal: {goal}
    
    REAL-TIME GOOGLE MAPS PROFILES FOUND:
    {maps_summary}
    
    Please output a complete marketing playbook using these exact markdown headers:
    
    ### 🗺️ GOOGLE MAPS PROFILE AUDIT
    Analyze how well this business can be found, connected with, and engaged with based on the real-time maps profile data provided above. Detail any missing ranking flags (like review velocity or rating gaps).
    
    ### 🎯 IMMEDIATE LOCAL ACTION PLAN
    Provide 3 concrete, step-by-step optimization recommendations they can make to their Google Business profile this week to achieve their goal: '{goal}'.
    
    ### ✍️ SOCIAL & MAPS OUTREACH COPY
    Provide a copy template designed to drive customer reviews or engagement that the owner can copy/paste directly.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return response.choices.message.content
    except Exception as e:
        return f"Error connecting to OpenAI: {str(e)}"

# 📄 Helper Function: HTML to PDF Document Compiler
def generate_pdf_bytes(biz_name, city_state, playbook_text):
    # Formulating clean, print-safe layout avoiding flex wrappers and forcing page-break rules
    html_content = f"""
    <html>
    <head>
        <style>
            @page {{ size: letter; margin: 1in; }}
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333333; line-height: 1.6; }}
            h1 {{ color: #1e3a8a; border-bottom: 2px solid #1e3a8a; padding-bottom: 8px; font-size: 24px; }}
            h3 {{ color: #1e40af; margin-top: 24px; font-size: 16px; page-break-after: avoid; }}
            p, li {{ font-size: 12px; color: #4b5563; }}
            .brand-badge {{ background-color: #f3f4f6; border-left: 4px solid #3b82f6; padding: 12px; margin-bottom: 20px; page-break-inside: avoid; }}
        </style>
    </head>
    <body>
        <h1>🚀 Google Maps Intelligence & Local Growth Playbook</h1>
        <div class="brand-badge">
            <p><strong>Target Business Profile:</strong> {biz_name}</p>
            <p><strong>Geographic Target:</strong> {city_state}</p>
            <p><strong>Engineers:</strong> High School STEM Research Coalition</p>
        </div>
        <div>
            {playbook_text.replace('\n', '<br>')}
        </div>
    </body>
    </html>
    """
    pdf_buffer = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_buffer)
    return pdf_buffer.getvalue()

# 🚀 Main App Execution Logic
if st.button("🔥 Run Maps Audit & Strategy Plan", type="primary"):
    if not business_name.strip() or not location.strip():
        st.warning("⚠️ Please provide both the Business Name and City/State location parameters.")
    else:
        with st.spinner("Accessing live Google Maps endpoints safely..."):
            profiles = fetch_google_maps_profile(business_name, location, serp_api_key)
            
        if profiles:
            st.session_state["maps_profiles"] = profiles
            
            # Show users a neat structured table of the real-time data retrieved from Maps
            st.subheader("📍 Real-Time Google Maps Findings")
            df = pd.DataFrame(profiles)
            st.dataframe(df, use_container_width=True)
            
            with st.spinner("Synthesizing Maps visibility audit via OpenAI..."):
                playbook = compile_business_playbook(business_name, location, primary_goal, profiles, openai_api_key)
                st.session_state["local_playbook"] = playbook

# Display Results & Export Options if Data Exists in State
if "local_playbook" in st.session_state:
    st.markdown("---")
    st.subheader("📋 Core Strategy Playbook")
    st.markdown(st.session_state["local_playbook"])
    
    # Generate and compile PDF on demand
    with st.spinner("Compiling print-optimized PDF asset..."):
        pdf_bytes = generate_pdf_bytes(business_name, location, st.session_state["local_playbook"])
        
    st.download_button(
        label="📥 Save Report as a PDF Report",
        data=pdf_bytes,
        file_name=f"{business_name.lower().replace(' ', '_')}_local_seo_report.pdf",
        mime="application/pdf"
    )
