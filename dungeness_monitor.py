import streamlit as st
import requests
import datetime
import random  # <--- New tool for cache busting

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="Dungeness River Monitor",
    page_icon="🌊",
    layout="centered"
)

# --- CONSTANTS ---
GAUGE_ID = "12048000"
# We removed the URL from here to build it dynamically later

# --- LOGIC FUNCTIONS ---
def get_flow_status(flow):
    # [cite_start]Logic per requirements [cite: 6-19]
    status = {"bg_color": "white", "text": "Unknown Flow", "blink": False, "range_min": 0, "range_max": 100}

    if 0 <= flow <= 62.5:
        status = {"bg_color": "#FF0000", "text": "Extremely Low- Salmon Endangered", "blink": True, "range_min": 0, "range_max": 62.5}
    elif 62.5 < flow <= 120:
        status = {"bg_color": "#FFBF00", "text": "Critically Low- Withdrawals Reduced", "blink": False, "range_min": 62.5, "range_max": 120}
    elif 120 < flow <= 238:
        status = {"bg_color": "#FFFF00", "text": "Low Flow - Conserve", "blink": False, "range_min": 120, "range_max": 238}
    elif 238 < flow <= 582:
        status = {"bg_color": "#0099FF", "text": "Adequate Flow", "blink": False, "range_min": 238, "range_max": 582}
    elif 582 < flow <= 2700:
        status = {"bg_color": "#800080", "text": "High Flow", "blink": False, "range_min": 582, "range_max": 2700}
    elif 2700 < flow <= 4275:
        status = {"bg_color": "#FFBF00", "text": "Flood Alert", "blink": False, "range_min": 2700, "range_max": 4275}
    elif 4275 < flow <= 6200:
        status = {"bg_color": "#FF0000", "text": "Minor to Moderate Flood -Take Precautions", "blink": False, "range_min": 4275, "range_max": 6200}
    elif flow > 6200:
        status = {"bg_color": "#8B0000", "text": "Extreme Flooding – Evacuation May Be Necessary", "blink": True, "range_min": 6200, "range_max": 99999}
    
    return status

def fetch_data():
    try:
        # CACHE BUSTER: We add a random number to the end of the URL.
        # This forces the USGS server to treat this as a brand new request every time.
        random_code = random.randint(1, 1000000)
        safe_url = f"https://waterservices.usgs.gov/nwis/iv/?format=json&sites={GAUGE_ID}&parameterCd=00060,00065&cb={random_code}"
        
        response = requests.get(safe_url)
        data = response.json()
        val_item = data['value']['timeSeries'][0]['values'][0]['value'][-1]
        
        flow_val = float(val_item['value'])
        timestamp_str = val_item['dateTime']
        
        # Format time nicely
        dt = datetime.datetime.fromisoformat(timestamp_str)
        formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return flow_val, formatted_time
    except Exception as e:
        return None, str(e)

def generate_html(flow, timestamp, gauge_id):
    status = get_flow_status(flow)
    
    # Blink CSS
    blink_css = ""
    if status['blink']:
        blink_css = """
        @keyframes blinker { 0% { opacity: 1; } 50% { opacity: 0.7; background-color: #333; } 100% { opacity: 1; } }
        .app-container { animation: blinker 2s linear infinite; }
        """

    # Bar Segments
    category_defs = [
        (0, 62.5, "#FF0000"), (62.5, 120, "#FFBF00"), (120, 238, "#FFFF00"),
        (238, 582, "#0099FF"), (582, 2700, "#800080"), (2700, 4275, "#FFBF00"),
        (4275, 6200, "#FF0000"), (6200, 7000, "#8B0000")
    ]
    total_scale = 7000
    bar_html = "".join([f'<div style="width:{(e-s)/total_scale*100}%; background-color:{c}; height:100%; float:left; border-right:1px solid white; box-sizing:border-box;"></div>' for s,e,c in category_defs])
    
    # Markers
    top_marker = min((flow / total_scale) * 100, 100)
    
    range_span = status['range_max'] - status['range_min']
    if status['range_min'] == 6200:
        display_max = max(7000, flow * 1.1) 
        range_span = display_max - 6200
        range_max_lbl = f"{int(display_max)}"
    else:
        range_max_lbl = f"{status['range_max']}"
    if range_span == 0: range_span = 1
    
    btm_marker = max(0, min(((flow - status['range_min']) / range_span) * 100, 100))

    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
        .app-wrapper {{ width: 100%; display: flex; justify-content: center; font-family: 'Roboto', sans-serif; color: white; text-shadow: 1px 1px 2px black; }}
        .app-container {{ width: 100%; max-width: 600px; background-color: {status['bg_color']}; padding: 20px; border-radius: 10px; display: flex; flex-direction: column; align-items: center; {blink_css} }}
        .bar-border {{ border: 2px solid white; height: 40px; width: 100%; position: relative; background-color: #333; overflow: hidden; }}
        .triangle-marker {{ width:0; height:0; border-left:10px solid transparent; border-right:10px solid transparent; border-bottom:15px solid white; position:absolute; bottom:0; transform:translateX(-50%); z-index:20; }}
        .axis-labels {{ display: flex; justify-content: space-between; font-size: 14px; margin-top: 5px; font-weight: bold; width: 100%; color: white; }}
    </style>
    <div class="app-wrapper"><div class="app-container">
        <div style="font-size:24px; font-weight:bold; margin-bottom:20px; text-align:center;">{status['text']}</div>
        <div style="font-size:24px; font-weight:bold; margin-bottom:5px;">Current Flow: {flow} CFS</div>
        <div style="font-size:10px; margin-bottom:2px;">Last Updated: {timestamp}</div>
        <div style="font-size:10px; margin-bottom:2px;">USGS Gauge: {gauge_id}</div>
        <hr style="width:50%; border-color:white; opacity:0.5; margin:20px 0;">
        <div style="width:90%; margin-top:25px; margin-bottom:15px;">
            <div style="text-align:center; margin-bottom:5px; font-weight:bold;">Categories of Total River Flow</div>
            <div class="bar-border">{bar_html}<div class="triangle-marker" style="left:{top_marker}%;"></div></div>
        </div>
        <div style="width:90%; margin-top:25px; margin-bottom:15px;">
            <div style="text-align:center; margin-bottom:5px; font-weight:bold;">Categories of Current River Flow</div>
            <div class="bar-border" style="background-color:{status['bg_color']};">
                <div class="triangle-marker" style="left:{btm_marker}%;"></div>
            </div>
            <div class="axis-labels"><span>{status['range_min']} CFS</span><span>{range_max_lbl} CFS</span></div>
        </div>
    </div></div>
    """

# --- MAIN APP LAYOUT ---
st.title("🌊 Dungeness River Monitor")

# We create a placeholder for messages
msg_container = st.empty()

if st.button('🔄 Update River Data Now', use_container_width=True):
    # This clears the cache for this specific function to be triple sure
    st.cache_data.clear()
    # We show a "Toast" message that pops up
    st.toast('Checking USGS servers...', icon='📡')
    st.rerun()

flow, timestamp = fetch_data()

if flow is not None:
    st.markdown(generate_html(flow, timestamp, GAUGE_ID), unsafe_allow_html=True)
else:
    st.error(f"Error fetching data: {timestamp}")
