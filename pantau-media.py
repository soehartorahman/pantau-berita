import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
import urllib.parse
import requests
from bs4 import BeautifulSoup

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

# 1. Rentang Waktu
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

# 4. Dropdown Resmi 13 Kabupaten/Kota Sulteng
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
    # Mengambil nama simpel wilayah (misal: "Parigi" atau "Sigi")
    wilayah_str = wilayah_option.replace("Kabupaten ", "").replace("Kota ", "")

st.sidebar.info(f"📍 **Target Query:** `{keywords} {wilayah_str}`")

# 5. Target Platform
st.sidebar.subheader("🌐 Sumber Informasi")
check_news = st.sidebar.checkbox("Portal Berita Media", value=True)
check_tiktok = st.sidebar.checkbox("TikTok", value=True)
check_x = st.sidebar.checkbox("Twitter / X", value=True)
check_fb = st.sidebar.checkbox("Facebook", value=True)
check_ig = st.sidebar.checkbox("Instagram", value=True)

btn_search = st.sidebar.button("🔍 Mulai Pemantauan Realtime", use_container_width=True, type="primary")

# Fungsi Scrape Engine Google Langsung (Menangkap Medsos seperti TikTok, IG, FB, X)
def fetch_google_search(query, time_str, platform_name):
    time_map = {
        "24 Jam Terakhir": "qdr:d",
        "7 Hari Terakhir": "qdr:w",
        "30 Hari Terakhir": "qdr:m",
        "Semua Waktu": ""
    }
    t_code = time_map.get(time_str, "")
    encoded_query = urllib.parse.quote(query)
    
    url = f"https://www.google.com/search?q={encoded_query}&hl=id&tbs={t_code}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    results = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        for g in soup.find_all('div', class_='g'):
            anchors = g.find_all('a')
            if anchors:
                link = anchors[0]['href']
                title = g.find('h3')
                title_text = title.text if title else f"Postingan {platform_name}"
                
                snippet = g.find('div', class_='VwiC3b')
                snippet_text = snippet.text if snippet else ""
                
                if link.startswith("http"):
                    results.append({
                        "Platform/Sumber": platform_name,
                        "Judul / Ringkasan": f"{title_text} - {snippet_text[:120]}",
                        "Waktu Publish": time_str,
                        "Link Tautan": link,
                        "Waktu Penarikan": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
    except Exception:
        pass
        
    return results

# Fungsi Google News RSS khusus Berita Online
def fetch_google_news(query, time_str):
    time_map = {
        "24 Jam Terakhir": "1d",
        "7 Hari Terakhir": "7d",
        "30 Hari Terakhir": "30d",
        "Semua Waktu": ""
    }
    t_code = time_map.get(time_str, "")
    full_query = f"{query} when:{t_code}" if t_code else query
    encoded_query = urllib.parse.quote(full_query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=id&gl=ID&ceid=ID:id"
    
    feed = feedparser.parse(rss_url)
    results = []
    
    for entry in feed.entries:
        title_parts = entry.title.rsplit(" - ", 1)
        title = title_parts[0]
        source = title_parts[1] if len(title_parts) > 1 else "Berita Online"
        
        results.append({
            "Platform/Sumber": f"Berita ({source})",
            "Judul / Ringkasan": title,
            "Waktu Publish": entry.get("published", "Terbaru"),
            "Link Tautan": entry.link,
            "Waktu Penarikan": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    return results

# Process Utama
if btn_search:
    if not keywords:
        st.error("Harap masukkan kata kunci pencarian!")
    else:
        st.info(f"🔄 Memindai Google untuk: **{keywords} {wilayah_str}**...")
        results = []
        
        # 1. Berita Portal
        if check_news:
            results.extend(fetch_google_news(f"{keywords} {wilayah_str}", time_filter))
            
        # 2. Medsos via Google Direct Search (Tepat seperti cara Anda mengetik di browser)
        if check_tiktok:
            results.extend(fetch_google_search(f"{keywords} {wilayah_str} tiktok", time_filter, "TikTok"))
        if check_x:
            results.extend(fetch_google_search(f"{keywords} {wilayah_str} site:x.com", time_filter, "Twitter / X"))
        if check_fb:
            results.extend(fetch_google_search(f"{keywords} {wilayah_str} site:facebook.com", time_filter, "Facebook"))
        if check_ig:
            results.extend(fetch_google_search(f"{keywords} {wilayah_str} site:instagram.com", time_filter, "Instagram"))

        st.success(f"✅ Selesai! Ditemukan {len(results)} temuan relevan.")
        
        if results:
            df = pd.DataFrame(results).drop_duplicates(subset=["Link Tautan"])
            
            tab1, tab2 = st.tabs(["📋 Tabel & Detail Hasil", "📥 Download Data (CSV)"])
            
            with tab1:
                st.subheader("Distribusi Sumber Informasi")
                st.bar_chart(df["Platform/Sumber"].value_counts())
                
                st.subheader("Daftar Temuan Terkini")
                for index, row in df.iterrows():
                    with st.expander(f"[{row['Platform/Sumber']}] {row['Judul / Ringkasan']}"):
                        st.write(f"**Waktu Publish:** {row['Waktu Publish']}")
                        st.write(f"**Tautan Asli:** [Buka Postingan / Berita]({row['Link Tautan']})")
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
            st.warning("Tidak ditemukan hasil. Coba ubah rentang waktu ke 'Semua Waktu' atau sesuaikan kata kunci.")
else:
    st.write("👉 Silakan atur parameter di **sidebar kiri**, lalu klik **'Mulai Pemantauan Realtime'**.")
