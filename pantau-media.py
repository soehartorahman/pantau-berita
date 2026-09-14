import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
import urllib.parse
from duckduckgo_search import DDGS

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="BMKG Sulteng - Media Monitor",
    page_icon="🌩️",
    layout="wide"
)

# Header Utama
st.title("🌩️ BMKG SPAG Lore Lindu Bariri")
st.subheader("Sistem Pemantauan Media Sosial & Berita Terkini (Sulawesi Tengah)")
st.markdown("---")

# Sidebar - Parameter Input
st.sidebar.header("⚙️ Filter & Parameter Pencarian")

# 1. Rentang Waktu Pencarian
time_filter = st.sidebar.selectbox(
    "📅 Rentang Waktu Pencarian:",
    ["7 Hari Terakhir", "24 Jam Terakhir", "30 Hari Terakhir", "Semua Waktu"],
    index=0
)

# 2. Kategori Bidang
kategori = st.sidebar.selectbox(
    "Pilih Kategori Bidang:",
    [
        "Bencana Hidrometeorologi",
        "Kualitas Udara & Karhutla",
        "Gempabumi & Tsunami",
        "Dampak Pertanian & Perubahan Iklim",
        "Kustom / Semua"
    ]
)

# Preset kata kunci sederhana
if kategori == "Bencana Hidrometeorologi":
    default_keywords = "banjir longsor"
elif kategori == "Kualitas Udara & Karhutla":
    default_keywords = "karhutla kebakaran hutan"
elif kategori == "Gempabumi & Tsunami":
    default_keywords = "gempa tsunami"
elif kategori == "Dampak Pertanian & Perubahan Iklim":
    default_keywords = "kekeringan gagal panen"
else:
    default_keywords = "banjir karhutla gempa"

# 3. Input Kata Kunci
keywords = st.sidebar.text_input("Kata Kunci Spesifik:", value=default_keywords)

# 4. Dropdown Resmi 13 Kabupaten/Kota di Sulawesi Tengah
daftar_wilayah_sulteng = [
    "Seluruh Sulawesi Tengah",
    "Kota Palu",
    "Kabupaten Sigi",
    "Kabupaten Donggala",
    "Kabupaten Parigi Moutong",
    "Kabupaten Poso",
    "Kabupaten Tojo Una-Una",
    "Kabupaten Tolitoli",
    "Kabupaten Buol",
    "Kabupaten Banggai",
    "Kabupaten Banggai Kepulauan",
    "Kabupaten Banggai Laut",
    "Kabupaten Morowali",
    "Kabupaten Morowali Utara",
    "Indonesia (Nasional)",
    "Kustom Wilayah Lain"
]

wilayah_option = st.sidebar.selectbox("Pilih Cakupan Wilayah:", daftar_wilayah_sulteng)

if wilayah_option == "Kustom Wilayah Lain":
    wilayah_str = st.sidebar.text_input("Masukkan Wilayah Kustom:", value="Sulawesi Tengah")
elif wilayah_option == "Seluruh Sulawesi Tengah":
    wilayah_str = "Sulawesi Tengah"
else:
    # Mengambil kata kunci ringkas wilayah (misal: "Parigi Moutong" atau "Parigi")
    wilayah_str = wilayah_option.replace("Kabupaten ", "").replace("Kota ", "")

st.sidebar.info(f"📍 **Target Query Pencarian:** `{keywords} {wilayah_str}`")

# 5. Target Platform
st.sidebar.subheader("🌐 Sumber Informasi")
check_news = st.sidebar.checkbox("Portal Berita Media (Google News)", value=True)
check_socmed = st.sidebar.checkbox("Media Sosial (X/FB/IG/TikTok)", value=True)

# Tombol Eksekusi
btn_search = st.sidebar.button("🔍 Mulai Pemantauan Realtime", use_container_width=True, type="primary")

def fetch_google_news(query, time_str):
    time_map = {
        "24 Jam Terakhir": "1d",
        "7 Hari Terakhir": "7d",
        "30 Hari Terakhir": "30d",
        "Semua Waktu": ""
    }
    t_code = time_map.get(time_str, "")
    
    # Format Query Google News RSS
    full_query = f"{query} when:{t_code}" if t_code else query
    encoded_query = urllib.parse.quote(full_query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=id&gl=ID&ceid=ID:id"
    
    feed = feedparser.parse(rss_url)
    results = []
    
    for entry in feed.entries:
        title_parts = entry.title.rsplit(" - ", 1)
        title = title_parts[0]
        source = title_parts[1] if len(title_parts) > 1 else "Google News"
        
        results.append({
            "Platform/Sumber": f"Berita ({source})",
            "Judul / Ringkasan": title,
            "Waktu Publish": entry.get("published", "Terbaru"),
            "Link Tautan": entry.link,
            "Waktu Penarikan": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    return results

def fetch_social_media(query, time_str):
    time_map_ddg = {
        "24 Jam Terakhir": "d",
        "7 Hari Terakhir": "w",
        "30 Hari Terakhir": "m",
        "Semua Waktu": None
    }
    t_code = time_map_ddg.get(time_str)
    ddgs = DDGS()
    results = []
    
    socmed_sites = [
        ("Twitter / X", f"site:x.com {query}"),
        ("Facebook", f"site:facebook.com {query}"),
        ("Instagram", f"site:instagram.com {query}"),
        ("TikTok", f"site:tiktok.com {query}")
    ]
    
    for platform_name, site_query in socmed_sites:
        try:
            res_list = ddgs.text(site_query, region="id-id", timelimit=t_code, max_results=4)
            if res_list:
                for res in res_list:
                    results.append({
                        "Platform/Sumber": platform_name,
                        "Judul / Ringkasan": f"{res.get('title', '')} - {res.get('body', '')[:120]}...",
                        "Waktu Publish": "Terkini",
                        "Link Tautan": res.get("href", ""),
                        "Waktu Penarikan": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
        except Exception:
            continue
    return results

# Process Pencarian
if btn_search:
    if not keywords:
        st.error("Harap masukkan kata kunci pencarian!")
    else:
        st.info(f"🔄 Sedang memindai isu ({time_filter}) untuk query: **{keywords} {wilayah_str}**...")
        
        results = []
        search_query = f"{keywords} {wilayah_str}"
        
        # 1. Tarik dari Berita Google News
        if check_news:
            news_data = fetch_google_news(search_query, time_filter)
            results.extend(news_data)
            
        # 2. Tarik dari Media Sosial
        if check_socmed:
            socmed_data = fetch_social_media(search_query, time_filter)
            results.extend(socmed_data)
            
        st.success(f"✅ Pemantauan selesai! Ditemukan {len(results)} temuan relevan.")
        
        if results:
            df = pd.DataFrame(results).drop_duplicates(subset=["Judul / Ringkasan"])
            
            tab1, tab2 = st.tabs(["📋 Tabel & Detail Hasil", "📥 Download Data (CSV)"])
            
            with tab1:
                st.subheader("Distribusi Sumber Informasii")
                st.bar_chart(df["Platform/Sumber"].value_counts())
                
                st.subheader("Daftar Temuan Terkini")
                for index, row in df.iterrows():
                    with st.expander(f"[{row['Platform/Sumber']}] {row['Judul / Ringkasan']}"):
                        st.write(f"**Waktu Publish:** {row['Waktu Publish']}")
                        st.write(f"**Tautan Asli:** [Buka Tautan Post/Berita]({row['Link Tautan']})")
                        st.caption(f"Waktu Penarikan Data: {row['Waktu Penarikan']}")

            with tab2:
                st.subheader("Unduh Laporan CSV")
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Download Data (Format CSV)",
                    data=csv,
                    file_name=f"Pantau_BMKG_Sulteng_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )
        else:
            st.warning("Tidak ditemukan postingan/berita terkini. Coba pilih rentang waktu 'Semua Waktu' atau persempit kata kunci.")
else:
    st.write("👉 Silakan atur parameter di **sidebar kiri**, lalu klik **'Mulai Pemantauan Realtime'**.")
