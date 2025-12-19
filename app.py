import streamlit as st
import requests

st.set_page_config(
    page_title="Quran Cards", 
    page_icon="📖", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Scheherazade+New:wght@400;700&display=swap');
    
    /* Dölj hamburgermenyn till höger (inställningar), men BEHÅLL headern för navigation */
    #MainMenu { visibility: hidden; }
    
    /* TA BORT eller KOMMENTERA BORT denna rad för att se menyknappen på mobilen: */
    /* header { visibility: hidden; } */ 
    
    footer { visibility: hidden; }
    
    .block-container {
        padding: 2.8rem 1rem !important;
        max-width: 100%;
    }
    
    .quran-card {
        background-color: #ffffff;
        border-radius: 16px;
        height: 65vh;
        width: 100%;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        display: flex;
        flex-direction: column;
        overflow: hidden;
        position: relative;
    }

    .card-header {
        background-color: #f8f9fa;
        border-bottom: 1px solid #eee;
        padding: 5px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-shrink: 0;
        height: 25px;
    }

    .header-center { display: flex; gap: 15px; align-items: baseline; }
    .surah-en { font-weight: 700; color: #2E8B57; font-size: 1rem; font-family: sans-serif; }
    .surah-ar { font-family: 'Scheherazade New', serif; font-size: 1.3rem; color: #333; line-height: 1; }
    
    .meta-tag {
        font-family: sans-serif; font-size: 0.8rem; color: #555;
        font-weight: 600; background-color: #e8f5e9; padding: 2px 10px; border-radius: 8px;
    }

    .progress-track { width: 100%; height: 4px; background-color: #eee; }
    .progress-fill { height: 100%; background-color: #2E8B57; transition: width 0.3s ease; }

    .card-content {
        flex-grow: 1;
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 0 30px;
        overflow-y: auto;
    }

    .arabic-text {
        font-family: 'Scheherazade New', serif;
        line-height: 2.2;
        direction: rtl;
        text-align: center;
        color: #000;
        width: 100%;
    }
    
    .card-content::-webkit-scrollbar { display: none; }
    .card-content { -ms-overflow-style: none; scrollbar-width: none; }

    div.stButton > button {
        height: 85vh; width: 100%; border: none; background-color: transparent;
        color: #e0e0e0; font-size: 40px; cursor: pointer;
        transition: background-color 0.2s, color 0.2s;
    }
    div.stButton > button:hover { color: #2E8B57; background-color: rgba(0,0,0,0.03); }
    div.stButton > button:active { background-color: rgba(46, 139, 87, 0.1); }
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def get_chapter_info(chapter_id):
    try:
        resp = requests.get(f"https://api.quran.com/api/v4/chapters/{chapter_id}").json()
        return resp['chapter']['name_simple'], resp['chapter']['name_arabic']
    except: return "Unknown", ""

@st.cache_data(show_spinner=False)
def fetch_verses_data(chapter_num):
    url = f"https://api.quran.com/api/v4/verses/by_chapter/{chapter_num}?language=en&words=false&fields=text_uthmani,juz_number&per_page=1000"
    try: return requests.get(url).json()['verses']
    except: return []

def calculate_font_size(text):
    l = len(text)
    if l < 50: return "40px"
    elif l < 100: return "35px"
    elif l < 200: return "30px"
    elif l < 400: return "25px"
    elif l < 700: return "20px"
    else: return "16px"

with st.sidebar:
    st.title("Inställningar")
    chapter = st.number_input("Kapitel", 1, 114, 1)
    verses_data = fetch_verses_data(chapter)
    surah_en, surah_ar = get_chapter_info(chapter)
    max_verses = len(verses_data)
    col_a, col_b = st.columns(2)
    with col_a: start_v = st.number_input("Start", 1, max_verses, 1)
    with col_b: end_v = st.number_input("Slut", 1, max_verses, max_verses)
    selected_data = verses_data[start_v-1 : end_v]

if 'card_index' not in st.session_state: st.session_state.card_index = 0
if st.session_state.card_index >= len(selected_data): st.session_state.card_index = 0

if selected_data:
    obj = selected_data[st.session_state.card_index]
    raw_text = obj['text_uthmani']
    juz = obj['juz_number']
    verse_num = obj['verse_key'].split(':')[1]
    
    progress_pct = (int(verse_num) / max_verses) * 100
    font_size = calculate_font_size(raw_text)

    col_l, col_c, col_r = st.columns([1, 10, 1])
    
    with col_l:
        st.write("")
        if st.button("❮", key="prev"):
            if st.session_state.card_index > 0:
                st.session_state.card_index -= 1
                st.rerun()

    with col_c:
        html_code = f"""
        <div class="quran-card">
            <div class="card-header">
                <span class="meta-tag">Juz {juz}</span>
                <div class="header-center">
                    <span class="surah-en">{surah_en}</span>
                    <span class="surah-ar">{surah_ar}</span>
                </div>
                <span class="meta-tag"># {verse_num}</span>
            </div>
            <div class="progress-track">
                <div class="progress-fill" style="width: {progress_pct}%;"></div>
            </div>
            <div class="card-content">
                <div class="arabic-text" style="font-size: {font_size};">{raw_text}</div>
            </div>
        </div>
        """
        st.markdown(html_code, unsafe_allow_html=True)

    with col_r:
        st.write("")
        if st.button("❯", key="next"):
            if st.session_state.card_index < len(selected_data) - 1:
                st.session_state.card_index += 1
                st.rerun()
else:
    st.info("Laddar...")
