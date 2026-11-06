import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import markdown
from openai import OpenAI
import io
import time

# Safe WeasyPrint import
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except OSError:
    WEASYPRINT_AVAILABLE = False
    HTML = None  # type: ignore

st.set_page_config(
    page_title="Universal Small Business Intelligence Tool",
    page_icon="🚀",
    layout="wide"
)

# Flashing warning CSS (30-second duration)
st.markdown("""
<style>
@keyframes flashRed {
    0%, 100% { opacity: 1; color: #ff0000; }
    50% { opacity: 0.3; color: #ff4444; }
}
.nap-warning {
    position: fixed;
    top: 70px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(255, 0, 0, 0.15);
    border: 3px solid #ff0000;
    padding: 12px 30px;
    border-radius: 8px;
    font-size: 22px;
    font-weight: bold;
    z-index: 9999;
    animation: flashRed 1s infinite;
    animation-duration: 30s;
    animation-fill-mode: forwards;
}
.nap-warning.hidden {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🚀 Universal Small Business Intelligence & Maps Optimizer")
st.markdown("""
*Created by STEM Students to empower local businesses through data transparency.*  
This app uses **SerpAPI** to safely pull real-time Google Maps Profile performance metrics and **OpenAI** to compile a downloadable growth strategy.
""")

# Load secrets (TOML)
try:
    serp_api_key = st.secrets["SERP_API_KEY"]
    openai_api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    st.error("""
    **Missing secrets.**  
    Please add `SERP_API_KEY` and `OPENAI_API_KEY` in Streamlit secrets (TOML format).

    On Streamlit Cloud: App settings → Secrets.  
    Locally: create `.streamlit/secrets.toml`.
    """)
    st.stop()

# Sidebar (ethical note only)
st.sidebar.markdown("### 🕊️ STEM Ethical Commitment")
st.sidebar.info("""
1. **Public Maps Architecture:** Accesses public business profiles legally via official search APIs.
2. **Empowerment Focus:** Helps local business owners audit their visibility and close gaps with competitors.
3. **No scraping bots** — only official SerpAPI endpoints.
4. **Secrets:** API keys are loaded securely from encrypted Streamlit secrets (TOML).
""")

if not WEASYPRINT_AVAILABLE:
    st.sidebar.warning(
        "⚠️ PDF generation disabled: WeasyPrint system libraries missing. "
        "Add a packages.txt file with the required system packages, or use the HTML download instead."
    )

# Inputs
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
        "Improve customer review strategies",
        "Increase emergency / same-day calls"
    ])

def is_nap_verified(profile):
    """NAP = Name + Address + Phone all present and non-empty."""
    name = str(profile.get("name", "")).strip()
    address = str(profile.get("address", "")).strip()
    phone = str(profile.get("phone", "")).strip()
    return bool(name and address and phone and name.lower() != "unknown business" and address.lower() not in ["no address listed", ""])

def fetch_google_maps_profile(biz_name, city_state, api_key):
    if not api_key:
        return [
            {"name": f"{biz_name} Main Location", "rating": 4.2, "reviews": 48, "address": f"123 Main St, {city_state}", "type": "Local Business", "phone": "(555) 123-4567"},
            {"name": f"{biz_name} Downtown", "rating": 4.7, "reviews": 112, "address": f"555 Broadway, {city_state}", "type": "Local Business", "phone": ""},
            {"name": f"Competitor Near {biz_name}", "rating": 4.0, "reviews": 65, "address": f"Near {city_state}", "type": "Competitor", "phone": "(555) 987-6543"}
        ]

    url = "https://serpapi.com/search"
    params = {
        "engine": "google_maps",
        "q": f"{biz_name} {city_state}",
        "api_key": api_key,
        "type": "search",
        "hl": "en"
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        local_results = data.get("local_results", [])
        if not local_results and "place_results" in data:
            place = data.get("place_results", {})
            local_results = [place] if place else []

        profiles = []
        for item in local_results[:8]:
            profiles.append({
                "name": item.get("title") or item.get("name", "Unknown Business"),
                "rating": item.get("rating", "N/A"),
                "reviews": item.get("reviews", 0),
                "address": item.get("address", "No address listed"),
                "type": item.get("type") or item.get("category", "Local Business"),
                "phone": item.get("phone", "") or item.get("phone_number", "") or ""
            })
        return profiles

    except requests.exceptions.RequestException as e:
        st.sidebar.error(f"SerpAPI connection error: {str(e)}")
        return []
    except Exception as e:
        st.sidebar.error(f"Unexpected SerpAPI error: {str(e)}")
        return []

def compile_business_playbook(biz_name, city_state, goal, maps_data, openai_key):
    if not openai_key:
        return "⚠️ OpenAI API key required to generate the playbook."

    client = OpenAI(api_key=openai_key)

    maps_summary = ""
    for idx, profile in enumerate(maps_data):
        maps_summary += (
            f"\n- Profile #{idx+1}: {profile['name']} | Rating: {profile['rating']} | "
            f"Reviews: {profile['reviews']} | Location: {profile['address']} | "
            f"Phone: {profile.get('phone', 'N/A')} | Category: {profile['type']}\n"
        )

    system_prompt = (
        "You are an expert Google Business Profile optimizer and local SEO architect. "
        "Your writing style is professional, actionable, structured, and easy for small-business owners to follow. "
        "Use clear markdown headers and bullet points."
    )

    user_prompt = f"""
BUSINESS INFO:
- Name: {biz_name}
- Location: {city_state}
- Core Goal: {goal}

REAL-TIME GOOGLE MAPS PROFILES FOUND (NAP VERIFIED ONLY):
{maps_summary}

Please output a complete marketing playbook using these exact markdown headers:

### 🗺️ GOOGLE MAPS PROFILE AUDIT
Analyze how well this business can be found, connected with, and engaged with based on the real-time maps profile data. Detail rating gaps, review velocity, category accuracy, and visibility issues.

### 🎯 IMMEDIATE LOCAL ACTION PLAN
Provide 3 concrete, step-by-step optimization recommendations they can make to their Google Business profile this week to achieve their goal: '{goal}'.

### ✍️ SOCIAL & MAPS OUTREACH COPY
Provide a ready-to-use copy template (email, SMS, or social post) designed to drive customer reviews or engagement that the owner can copy/paste directly.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error connecting to OpenAI: {str(e)}"

def generate_pdf_bytes(biz_name, city_state, playbook_text):
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError("WeasyPrint is not available")

    html_body = markdown.markdown(playbook_text, extensions=["extra", "nl2br"])

    html_content = f"""
    <html>
    <head>
        <style>
            @page {{ size: letter; margin: 0.75in; }}
            body {{
                font-family: 'Noto Color Emoji', 'Helvetica Neue', Helvetica, Arial, sans-serif;
                color: #333333;
                line-height: 1.55;
            }}
            h1 {{
                color: #1e3a8a;
                border-bottom: 2px solid #1e3a8a;
                padding-bottom: 8px;
                font-size: 22px;
                font-family: 'Noto Color Emoji', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            }}
            h3 {{
                color: #1e40af;
                margin-top: 22px;
                font-size: 15px;
                page-break-after: avoid;
                font-family: 'Noto Color Emoji', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            }}
            p, li {{
                font-size: 11.5px;
                color: #4b5563;
                font-family: 'Noto Color Emoji', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            }}
            ul {{ margin-top: 4px; }}
            .brand-badge {{
                background-color: #f3f4f6;
                border-left: 4px solid #3b82f6;
                padding: 12px;
                margin-bottom: 18px;
                page-break-inside: avoid;
            }}
        </style>
    </head>
    <body>
        <h1>🚀 Google Maps Intelligence & Local Growth Playbook</h1>
        <div class="brand-badge">
            <p><strong>Target Business Profile:</strong> {biz_name}</p>
            <p><strong>Geographic Target:</strong> {city_state}</p>
            <p><strong>Engineers:</strong> High School STEM Research Coalition</p>
        </div>
        <div>{html_body}</div>
    </body>
    </html>
    """
    pdf_buffer = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_buffer)
    return pdf_buffer.getvalue()

# Main logic
if st.button("🔥 Run Maps Audit & Strategy Plan", type="primary"):
    if not business_name.strip() or not location.strip():
        st.warning("⚠️ Please provide both the Business Name and City/State location parameters.")
    else:
        with st.spinner("Accessing live Google Maps endpoints safely via SerpAPI..."):
            all_profiles = fetch_google_maps_profile(business_name, location, serp_api_key)

        if all_profiles:
            verified = [p for p in all_profiles if is_nap_verified(p)]
            non_verified = [p for p in all_profiles if not is_nap_verified(p)]

            st.session_state["maps_profiles"] = verified
            st.session_state["biz_name"] = business_name
            st.session_state["location"] = location
            st.session_state["goal"] = primary_goal
            st.session_state["show_nap_warning"] = len(non_verified) > 0
            st.session_state["nap_warning_start"] = time.time()

            if verified:
                st.subheader("📍 Real-Time Google Maps Findings (NAP Verified Only)")
                df = pd.DataFrame(verified)
                display_cols = ["name", "rating", "reviews", "address", "phone", "type"]
                display_df = df[[c for c in display_cols if c in df.columns]].copy()
                st.dataframe(display_df, use_container_width=True)

                if len(df) > 1 and "rating" in df.columns:
                    chart_df = df[df["rating"] != "N/A"].copy()
                    if not chart_df.empty:
                        chart_df["rating"] = pd.to_numeric(chart_df["rating"], errors="coerce")
                        fig = px.bar(
                            chart_df,
                            x="name",
                            y=["rating", "reviews"],
                            barmode="group",
                            title="Rating & Review Volume Comparison (NAP Verified)",
                            labels={"value": "Score / Count", "variable": "Metric"},
                            height=420
                        )
                        st.plotly_chart(fig, use_container_width=True)

                with st.spinner("Synthesizing Maps visibility audit via OpenAI..."):
                    playbook = compile_business_playbook(
                        business_name, location, primary_goal, verified, openai_api_key
                    )
                    st.session_state["local_playbook"] = playbook
            else:
                st.error("No NAP-verified businesses found. A business must have Name + Address + Phone listed on Google Maps.")
                st.session_state["local_playbook"] = None
        else:
            st.error("No Google Maps profiles returned. Check your SerpAPI key or try a broader query.")

# Flashing NAP Warning (30 seconds)
if st.session_state.get("show_nap_warning", False):
    elapsed = time.time() - st.session_state.get("nap_warning_start", time.time())
    if elapsed < 30:
        st.markdown(
            '<div class="nap-warning">⚠️ NOT NAP VERIFIED — Some results lack Phone number and were excluded</div>',
            unsafe_allow_html=True
        )
    else:
        st.session_state["show_nap_warning"] = False

# Display results
if "local_playbook" in st.session_state and st.session_state["local_playbook"]:
    st.markdown("---")
    st.subheader("📋 Core Strategy Playbook")
    st.markdown(st.session_state["local_playbook"])

    biz_name_safe = st.session_state.get("biz_name", business_name)
    location_safe = st.session_state.get("location", location)
    playbook = st.session_state["local_playbook"]

    if WEASYPRINT_AVAILABLE:
        with st.spinner("Compiling print-optimized PDF asset..."):
            pdf_bytes = generate_pdf_bytes(biz_name_safe, location_safe, playbook)

        st.download_button(
            label="📥 Save Report as a PDF Report",
            data=pdf_bytes,
            file_name=f"{biz_name_safe.lower().replace(' ', '_')}_local_seo_report.pdf",
            mime="application/pdf"
        )
    else:
        st.info("PDF generation unavailable in this environment. Download the report as HTML instead:")
        html_body = markdown.markdown(playbook, extensions=["extra", "nl2br"])
        full_html = f"""
        <html><head><meta charset="utf-8"><title>Growth Playbook</title></head>
        <body style="font-family:Helvetica,Arial,sans-serif;margin:40px;">
        <h1>🚀 Google Maps Intelligence & Local Growth Playbook</h1>
        <p><strong>Business:</strong> {biz_name_safe}<br>
        <strong>Location:</strong> {location_safe}</p>
        <hr>
        {html_body}
        </body></html>
        """
        st.download_button(
            label="📥 Download Report as HTML",
            data=full_html,
            file_name=f"{biz_name_safe.lower().replace(' ', '_')}_local_seo_report.html",
            mime="text/html"
        )

    if "maps_profiles" in st.session_state and st.session_state["maps_profiles"]:
        csv = pd.DataFrame(st.session_state["maps_profiles"]).to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📊 Download Raw Maps Data (CSV)",
            data=csv,
            file_name="maps_profiles.csv",
            mime="text/csv"
        )

# Privacy Mode – LAST BUTTON on the page
st.markdown("---")
if st.button("🧹 Clear generated report from session (privacy)", type="secondary"):
    keys_to_clear = ["local_playbook", "maps_profiles", "biz_name", "location", "goal", "show_nap_warning", "nap_warning_start"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.success("✅ Report and Maps data cleared from this session.")
    st.rerun()
