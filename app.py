import streamlit as st
import datetime
import requests
import time
import random
from google import genai
from PIL import Image
import os

# 1. Initialize Gemini Client
try:
    client = genai.Client()
except Exception as e:
    st.error("Please set your GEMINI_API_KEY environment variable to start the app.")
    client = None

# 2. Automated Geolocation Tracker
def get_automatic_location():
    try:
        response = requests.get("http://ip-api.com", timeout=5).json()
        if response.get("status") == "success":
            city = response.get("city", "Bhilai")
            region = response.get("regionName", "Chhattisgarh")
            country = response.get("country", "India")
            return f"{city}, {region} ({country})"
    except Exception:
        pass
    return "Bhilai, Chhattisgarh (India)"

# 3. Seasonal Regional Nature Lists
def get_localized_suggestions(detected_location):
    current_month_name = datetime.datetime.now().strftime("%B")
    
    if current_month_name in ["December", "January", "February"]:
        season = "Winter"
    elif current_month_name in ["March", "April", "May", "June"]:
        season = "Spring/Summer"
    else:
        season = "Post-Monsoon/Autumn"

    if "India" in detected_location or "Chhattisgarh" in detected_location:
        items = {
            "Winter": ["Migratory ducks near wetlands", "Indian Roller bird (Neelkanth)", "Amla trees", "Dry teak leaves", "Honeybees on garden flowers"],
            "Spring/Summer": ["Palash flowers (Flame of the Forest)", "Mango blossoms (Baur)", "Koel bird sightings", "House Sparrows", "Common Jezebel butterflies"],
            "Post-Monsoon/Autumn": ["Holy Basil (Tulsi) bushes", "Wild Fungi/Mushrooms on bark", "Indian Peafowl (Mor)", "Coppersmith Barbet (Tambat) calling", "Dragonflies near water structures"]
        }
    else:
        items = {
            "Winter": ["Robin birds", "Holly bushes", "Evergreen pine cones"],
            "Spring/Summer": ["Sunflowers", "Monarch butterflies", "Oak tree leaves"],
            "Post-Monsoon/Autumn": ["Chestnuts", "Falling Oak leaves", "Migrating geese flocks"]
        }
        
    return season, items.get(season, ["Local birds", "Green plants", "Insects"])

# 4. Interface Configuration
st.set_page_config(page_title="Touch Grass Challenge", page_icon="🌿", layout="centered")
st.title("🌿 The Touch Grass Challenge")

quotes = [
    "✨ 'Look deep into nature, and then you will understand everything better.' — Albert Einstein",
    "☀️ 'In all things of nature there is something of the marvelous.' — Aristotle",
    "🍃 'Adopt the pace of nature: her secret is patience.' — Ralph Waldo Emerson",
    "🌸 'To walk in nature is to witness a thousand miracles.' — Mary Davis"
]
st.markdown(f"***{random.choice(quotes)}***")
st.write("---")

# 5. Load Geolocation Cache
if "auto_location" not in st.session_state:
    st.session_state.auto_location = get_automatic_location()
detected_place = st.session_state.auto_location

if "challenge_started" not in st.session_state:
    st.session_state.challenge_started = False
if "found_count" not in st.session_state:
    st.session_state.found_count = 0
if "discovered_items" not in st.session_state:
    st.session_state.discovered_items = []
if "final_goal" not in st.session_state:
    st.session_state.final_goal = 5

# 6. Welcome & Conversational Setup Phase
if not st.session_state.challenge_started:
    st.subheader("🎯 Set Your Weekly Goal")
    st.write("Taking a break from screens clears the mind. How many natural things do you think you can explore this week?")
    
    goal_input = st.text_input("Enter your target count (Leave empty for a default of 5):", placeholder="5")
    raw_val = goal_input.strip()
    user_val = int(raw_val) if raw_val.isdigit() else 5
    
    if raw_val.isdigit():
        if 5 <= user_val <= 10:
            suggested_up = user_val + 2
            st.info(f"💡 **Coach Advice:** {user_val} is a great start! But I bet you can discover even more. Why not challenge yourself to explore **{suggested_up}** things this week? You'll easily spot unique birds, butterflies, and leafy textures right outside!")
        elif user_val > 10:
            st.success(f"🔥 **Incredible Ambition!** Targetting {user_val} items means you are going to see an amazing variety of wildlife. Let's do this!")
    
    if st.button("🚀 Confirm Challenge & Step Outside"):
        st.session_state.final_goal = user_val
        st.session_state.challenge_started = True
        st.rerun()

# 7. Core Application Phase
else:
    weekly_goal = st.session_state.final_goal
    
    st.sidebar.header("🎒 Your Adventure Backpack")
    st.sidebar.write(f"📍 **Location:** {detected_place}")
    st.sidebar.write("---")
    
    st.sidebar.subheader("📊 Your Progress")
    progress_percentage = min(float(st.session_state.found_count / weekly_goal), 1.0)
    st.sidebar.progress(progress_percentage)
    st.sidebar.write(f"**Discovered:** {st.session_state.found_count} out of {weekly_goal} items")
    st.sidebar.write("---")
    
    if st.session_state.found_count >= weekly_goal:
        st.sidebar.balloons()
        st.sidebar.success("🎉 Goal Reached! Fantastic job connecting with nature!")
        
    if st.sidebar.button("⚙️ Reset & Set New Goal"):
        st.session_state.challenge_started = False
        st.session_state.found_count = 0
        st.session_state.discovered_items = []
        st.rerun()

    season_name, items = get_localized_suggestions(detected_place)
    st.subheader(f"📅 Your Scout Guide ({season_name})")
    st.write(f"Look outside for these common birds, plants, and elements around **{detected_place}** right now:")
    for item in items:
        st.markdown(f"- 🔎 *{item}*")
        
    st.write("---")

    # 8. Upload Processing Pipeline
    st.subheader("📸 Document an Item You Found")
    uploaded_file = st.file_uploader("Upload a photo of a plant, bird, insect, or tree:", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Your Natural Discovery", use_container_width=True)
        
        if st.button("🧬 Identify & Analyze with Open AI"):
            if client is None:
                st.error("API client not configured. Check your GEMINI_API_KEY environment variable.")
            else:
                status_container = st.empty()
                max_retries = 3
                success = False
                response_text = ""
                
                for attempt in range(max_retries):
                    try:
                        status_container.spinner(f"AI is examining your discovery (Attempt {attempt + 1}/{max_retries})...")
                        
                        prompt = f"""
                        You are an encouraging, expert open-source nature AI assistant built for the 'Touch Grass' challenge.
                        Identify the plant, bird, animal, tree, or insect in this photo.
                        
                        Structure your response clearly:
                        1. **Names**: Provide the standard English name, the scientific name, and the common regional names or vernacular names used specifically in this location: "{detected_place}" (e.g. Hindi/Chhattisgarhi regional variants if in India).
                        2. **Characteristics**: Provide 3 unique characteristics or fun facts about it.
                        3. **Encouragement**: End with an enthusiastic paragraph praising the user for going outdoors and touching grass.
                        """
                        
                        response = client.models.generate_content(
                            model='gemini-3.8-flash',
                            contents=[image, prompt]
                        )
                        response_text = response.text
                        success = True
                        break
                        
                    except Exception as e:
                        error_msg = str(e)
                        if "503" in error_msg or "UNAVAILABLE" in error_msg:
                            wait_time = (attempt + 1) * 3
                            status_container.warning(f"Google's servers are busy. Retrying automatically in {wait_time} seconds...")
                            time.sleep(wait_time)
                        else:
                            status_container.error(f"An unexpected error occurred: {e}")
                            break
                
                if success:
                    status_container.success("Analysis Complete!")
                    st.session_state.found_count += 1
                    st.session_state.discovered_items.append({"name": uploaded_file.name, "analysis": response_text})
                    st.rerun()
                elif not success and ("503" in error_msg or "UNAVAILABLE" in error_msg):
                    status_container.error("Google's public servers are heavily overloaded. Please try again in a few seconds.")

    # 9. Collection Log History Drawer
    if st.session_state.discovered_items:
        st.write("---")
        st.subheader("🎒 Your Discovered Collection This Week")
        for idx, discovery in enumerate(st.session_state.discovered_items, 1):
            with st.expander(f"✨ Discovery #{idx}: {discovery['name']}"):
                st.markdown(discovery['analysis'])