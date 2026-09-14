import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
import urllib.parse

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
    ["7 Hari Terakhir", "24 Jam Terakhir", "30 Hari Terakhir"],
    index=0
)

time_limit_map = {
    "24 Jam Terakhir": "d",
    "7 Hari Terakhir": "w",
    "30 Hari Terakhir": "m"
}
selected_time = time_limit_map[time_filter]

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

# Presets Kata Kunci Sederhana (Tanpa OR bertumpuk)
default_keywords = ""
if kategori == "Bencana Hidrometeorologi":
    default_keywords = "banjir longsor"
elif kategori == "Kualitas Udara & Karhutla":
    default_keywords = "karhutla kebakaran hutan"
elif kategori == "Gempabumi & Tsunami":
    default_keywords = "gempa tsunami"
elif kategori == "Dampak Pertanian & Perubahan Iklim":
    default_keywords = "kekeringan gagal panen"
else:
    default_keywords = "cuaca ekstrem"

# 3. Input Kata Kunci
keywords = st.sidebar.text_input("Kata Kunci Spesifik:", value=default_keywords)

# 4. Cakupan Wilayah
wilayah_option = st.sidebar.selectbox(
    "Pilih Cakupan Wilayah:",
    ["Sulawesi Tengah", "Palu", "Sigi", "Donggala", "Poso", "Parigi", "Morowali", "Tolitoli", "Buol", "Banggai", "Indonesia", "Kustom Wilayah"]
)

if wilayah_option == "Kustom Wilayah":
    wilayah_str = st.sidebar.text_input("Masukkan Wilayah Kustom:", value="Sulawesi Tengah")
else:
    wilayah_str = wilayah_option

st.sidebar.info(f"📍 **Target Query:** `{keywords} {wilayah_str}`")

# 5. Target Platform Media
st.sidebar.subheader("🌐 Sumber Informasi")
check_news = st.sidebar.checkbox("Portal Berita Media Nasional/Lokal", value=True)
check_socmed = st.sidebar.checkbox("Postingan Medsos / Media Viral", value=True)

# Tombol Eksekusi
btn_search = st.sidebar.button("🔍 Mulai Pemantauan Realtime", use_container_width=True, type="primary")

def fetch_google_news(query, time_range):
    # Encoding query untuk URL Google News RSS
    full_query = f"{query} when:{time_range}"
    encoded_query = urllib.parse.quote(full_query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=id&gl=ID&ceid=ID:id"
    
    feed = feedparser.parse(rss_url)
    results = []
    
    for entry in feed.entries:
        # Ekstrak nama media dari title
        title_parts = entry.title.rsplit(" - ", 1)
        title = title_parts[0]
        source = title_parts[1] if len(title_parts) > 1 else "Berita Online"
        
        results.append({
            "Sumber / Media": source,
            "Judul Berita / Post": title,
            "Waktu Publish": entry.get("published", "Tidak diketahui"),
            "Link Tautan": entry.link,
            "Waktu Penarikan": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    return results

# Area Hasil Pencarian
if btn_search:
    if not keywords:
        st.error("Harap masukkan kata kunci pencarian!")
    else:
        st.info(f"🔄 Sedang memindai isu terkini ({time_filter}) untuk query: **{keywords} {wilayah_str}**...")
        
        query_text = f"{keywords} {wilayah_str}"
        results = fetch_google_news(query_text, selected_time)
        
        # Tambahkan variasi pencarian medsos jika dicentang
        if check_socmed:
            query_socmed = f"{keywords} {wilayah_str} viral media sosial"
            socmed_results = fetch_google_news(query_socmed, selected_time)
            results.extend(socmed_results)

        st.success(f"✅ Pemantauan selesai! Ditemukan {len(results)} temuan relevan.")
        
        if results:
            df = pd.DataFrame(results).drop_duplicates(subset=["Judul Berita / Post"])
            
            tab1, tab2 = st.tabs(["📋 Tabel & Detail Hasil", "📥 Download Data (CSV)"])
            
            with tab1:
                st.subheader("Distribusi Sumber Berita / Media")
                st.bar_chart(df["Sumber / Media"].value_counts().head(10))
                
                st.subheader("Daftar Temuan Terkini")
                for index, row in df.iterrows():
                    with st.expander(f"[{row['Sumber / Media']}] {row['Judul Berita / Post']}"):
                        st.write(f"**Waktu Publish:** {row['Waktu Publish']}")
                        st.write(f"**Tautan Asli:** [Buka Berita / Media]({row['Link Tautan']})")
                        st.caption(f"Waktu Penarikan Data: {row['Waktu Penarikan']}")

            with tab2:
                st.subheader("Unduh Laporan")
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Download Data (Format CSV)",
                    data=csv,
                    file_name=f"Pantau_Media_BMKG_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )
        else:
            st.warning("Tidak ditemukan isu terkini dalam rentang waktu tersebut. Coba perluas cakupan wilayah atau ganti kata kunci.")
else:
    st.write("👉 Silakan atur parameter di **sidebar kiri**, lalu klik **'Mulai Pemantauan Realtime'**.")
