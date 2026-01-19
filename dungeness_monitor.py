import streamlit as st
import requests
import datetime

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Dungeness River Monitor", page_icon="🌊", layout="centered")

# --- CONSTANTS ---
GAUGE_ID = "12048000"
# Using the most stable Legacy IV Service
URL = f"https://waterservices.usgs.gov/nwis/iv/?format=json&sites={GAUGE_ID}&parameterCd=00060&siteStatus=all"

def get_flow_status(flow):
    """Logic to map CFS to environmental status."""
    if flow <= 62.5: return {"bg_color": "#FF0000", "text": "Extremely Low- Salmon Endangered", "blink": True, "range_min": 0, "range_max": 62.5}
    if flow <= 120:  return {"bg_color": "#FFBF00", "text": "Critically Low- Withdrawals Reduced", "blink": False, "range_min": 62.5, "range_max": 120}
    if flow <= 238:  return {"bg_color": "#FFFF00", "text": "Low Flow - Conserve", "blink": False, "range_min": 120, "range_max": 238}
    if flow <= 582:  return {"bg_color": "#0099FF", "text": "Adequate Flow", "blink": False, "range_min": 238, "range_max": 582}
    if flow <= 2700: return {"bg_color": "#800080", "text": "High Flow", "blink": False, "range_min": 582, "range_max": 2700}
    if flow <= 4275: return {"bg_color": "#FFBF00", "text": "Flood Alert", "blink": False, "range_min": 2700, "range_max": 4275}
    if flow <= 6200: return {"bg_color": "#FF0000", "text": "Minor to Moderate Flood", "blink": False, "range_min": 4275, "range_max": 6200}
    return {"bg_color": "#8B0000", "text": "Extreme Flooding", "blink": True, "range_min": 6200, "range_max": 15000}

def fetch_data():
    """Robust data fetch using legacy IV service with modern headers."""
    try:
        # USGS now requires a User-Agent header to identify the request source
        headers = {
            "User-Agent": "DungenessMonitorApp/1.0 (contact: user@example.com)",
            "Accept-Encoding": "gzip"
        }
        response = requests.get(URL, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return None, f"USGS Server Error: {response.status_code}"

        data = response.json()
        
        # Deeply nested parsing with safety checks
        ts_data = data['value']['timeSeries'][0]['values'][0]['value']
        if not ts_data:
            return None, "Gauge reporting null values."
            
        latest_entry = ts_data[-1] # Get the most recent reading
        flow_val = float(latest_entry['value'])
        
        # Parse timestamp (e.g., 2026-01-19T08:15:00.000-08:00)
        raw_time = latest_entry['dateTime']
        dt = datetime.datetime.fromisoformat(raw_time)
        formatted_time = dt.strftime('%Y-%m-%d %I:%M %p')

        return flow_val, formatted_time

    except (KeyError, IndexError):
        return None, "USGS JSON structure changed or gauge is offline."
    except Exception as e:
        return None, f"Connection error: {str(e)}"

def generate_html(flow, reading_time_str, gauge_id):
    """Builds the visual dashboard."""
    status = get_flow_status(flow)
    blink_css = "@keyframes blink { 50% { opacity: 0.6; } } .app-container { animation: blink 2s infinite; }" if status.get('blink') else ""
    
    return f"""
    <style>
        .app-wrapper {{ display: flex; justify-content: center; color: white; text-shadow: 1px 1px 2px black; font-family: sans-serif; }}
        .app-container {{ width: 100%; max-width: 500px; background-color: {status['bg_color']}; padding: 30px; border-radius: 15px; text-align: center; }}
        {blink_css}
    </style>
    <div class="app-wrapper">
        <div class="app-container">
            <h2 style="margin-bottom:0;">{status['text']}</h2>
            <h1 style="font-size: 3rem; margin: 10px 0;">{flow} CFS</h1>
            <p>Last Updated: {reading_time_str}</p>
            <p style="font-size: 0.8rem; opacity: 0.8;">Gauge: {gauge_id}</p>
        </div>
    </div>
    """

# --- MAIN APP ---
st.title("🌊 Dungeness River Monitor")

@st.fragment(run_every=60)
def show_river_data():
    flow, reading_str = fetch_data()
    if flow is not None:
        st.markdown(generate_html(flow, reading_str, GAUGE_ID), unsafe_allow_html=True)
        st.caption(f"Checked at: {datetime.datetime.now().strftime('%H:%M:%S')}")
    else:
        st.error(f"Error: {reading_str}")
        if st.button("Force Reconnect"):
            st.rerun()

show_river_data()
