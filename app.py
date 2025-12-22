import streamlit as st
import requests
import unicodedata
import streamlit.components.v1 as components
import re

# --- 1. SETUP & STATE ---
st.set_page_config(
    page_title="Quran Cards", 
    page_icon="📖", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'chapter' not in st.session_state: st.session_state.chapter = 1
if 'start_v' not in st.session_state: st.session_state.start_v = 1
if 'end_v' not in st.session_state: st.session_state.end_v = 7 
if 'card_index' not in st.session_state: st.session_state.card_index = 0
if 'hifz_colors' not in st.session_state: st.session_state.hifz_colors = False
if 'qalqalah_mode' not in st.session_state: st.session_state.qalqalah_mode = False 
if 'show_links' not in st.session_state: st.session_state.show_links = False

# --- 2. LOGIC & HELPER FUNCTIONS ---

@st.cache_data(show_spinner=False)
def get_chapter_info(chapter_id):
    try:
        resp = requests.get(f"https://api.quran.com/api/v4/chapters/{chapter_id}").json()
        return resp['chapter']['name_simple'], resp['chapter']['name_arabic'], resp['chapter']['verses_count']
    except: return "Unknown", "", 0

@st.cache_data(show_spinner=False)
def fetch_verses_data(chapter_num):
    url = f"https://api.quran.com/api/v4/verses/by_chapter/{chapter_num}?language=en&words=false&fields=text_uthmani,juz_number&per_page=1000"
    try: return requests.get(url).json()['verses']
    except: return []

def get_clean_length(text):
    return len([c for c in text if unicodedata.category(c) != 'Mn'])

def calculate_text_settings(text):
    clean_len = get_clean_length(text)
    max_size, min_size = 7.0, 2.5
    short_threshold, long_threshold = 15, 400
    
    if clean_len <= short_threshold:
        final_size = max_size
        line_height = "1.9"
    elif clean_len >= long_threshold:
        final_size = min_size
        line_height = "1.65"
    else:
        progr = (clean_len - short_threshold) / (long_threshold - short_threshold)
        final_size = max_size - (progr * (max_size - min_size))
        line_height = f"{1.8 - (progr * 0.3):.2f}"

    return f"{final_size:.2f}vw", line_height

# --- FÄRGNINGSFUNKTIONER ---

def get_hifz_html(text):
    words = text.split(" ")
    colored_words = []
    highlight_color = "#D35400" 
    for word in words:
        if word:
            colored_words.append(f'<span style="color: {highlight_color};">{word[0]}</span>{word[1:]}')
        else:
            colored_words.append(word)
    return " ".join(colored_words)

def get_qalqalah_background_html(text):
    """
    Skapar HTML för BAKGRUNDSLAGRET.
    Texten här är TRANSPARENT.
    Vi sätter BACKGROUND-COLOR på bokstäverna vi vill markera.
    """
    qalqalah_letters = "\u0642\u0637\u0628\u062c\u062f"
    sukoon_marks = "\u0652\u06E1"
    
    # Ljusa pastellfärger för bakgrunden så texten syns tydligt ovanpå
    bg_sughra = "#B3E5FC" # Ljusblå (Light Blue 100)
    bg_kubra = "#FFCDD2"  # Ljusröd (Red 100)
    
    # Eftersom texten är transparent spelar "shaping" ingen roll visuellt här,
    # men vi vill att markeringen ska täcka rätt yta.
    
    # 1. Sughra (Mitten) - Markera bokstav + sukoon
    regex_sughra = f"([{qalqalah_letters}])([{sukoon_marks}])"
    text = re.sub(regex_sughra, f'<span style="background-color: {bg_sughra}; border-radius: 4px;">\\1\\2</span>', text)

    # 2. Kubra (Slutet) - Markera bokstav + ev. vokal
    regex_kubra = f"([{qalqalah_letters}])([\u064B-\u065F]*)$"
    text = re.sub(regex_kubra, f'<span style="background-color: {bg_kubra}; border-radius: 4px;">\\1\\2</span>', text)
    
    return text

# --- 3. CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Scheherazade+New:wght@400;700&display=swap');
    
    .stApp { background-color: #ffffff; }
    .block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
    header, footer, [data-testid="stSidebar
