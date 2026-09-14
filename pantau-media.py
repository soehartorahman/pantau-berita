import streamlit as st
from duckduckgo_search import DDGS
import pandas as pd
from datetime import datetime

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

# 1. Rentang Waktu Pencarian (BARU)
time_filter = st.sidebar.selectbox(
    "📅 Rentang Waktu Pencarian:",
    ["7 Hari Terakhir", "24 Jam Terakhir", "1 Bulan Terakhir", "Semua Waktu"],
    index=0
)

# Mapping kode timelimit DuckDuckGo
time_limit_code = None
if time_filter == "24 Jam Terakhir":
    time_limit_code = "d"
elif time_filter == "7 Hari Terakhir":
    time_limit_code = "w"
elif time_filter == "1 Bulan Terakhir":
    time_limit_code = "m"

# 2. Kategori Bidang
kategori = st.sidebar.selectbox(
    "Pilih Kategori Bidang:",
    [
        "Bencana Hidrometeorologi (Banjir, Longsor, Kekeringan, Puting Beliung)",
        "Kualitas Udara & Karhutla (Asap, Hotspot, ISPU)",
        "Gempabumi & Tsunami",
        "Dampak Pertanian & Perubahan Iklim (Gagal Panen, Hama)",
        "Semua Bidang / Custom"
    ]
)

# Kata kunci dibuat lebih simpel agar pencarian lebih luas
default_keywords = ""
if "Hidrometeorologi" in kategori:
    default_keywords = "banjir OR longsor"
elif "Kualitas Udara" in kategori:
    default_keywords = "karhutla OR kebakaran hutan"
elif "Gempabumi" in kategori:
    default_keywords = "gempa OR tsunami"
elif "Pertanian" in kategori:
    default_keywords = "gagal panen OR kekeringan"
else:
    default_keywords = "banjir OR karhutla OR gempa"

# 3. Input Kata Kunci
keywords = st.sidebar.text_input("Kata Kunci Spesifik:", value=default_keywords)

# 4. Cakupan Wilayah
wilayah_option = st.sidebar.selectbox(
    "Pilih Cakupan Wilayah:",
    ["Sulawesi Tengah", "Palu", "Sigi", "Donggala", "Poso", "Parigi", "Morowali", "Tolitoli", "Indonesia (Nasional)", "Kustom Wilayah"]
)

if wilayah_option == "Kustom Wilayah":
    wilayah_str = st.sidebar.text_input("Masukkan Wilayah Kustom:", value="Sulawesi Tengah")
else:
    wilayah_str = wilayah_option

st.sidebar.info(f"📍 **Target Wilayah Aktif:** {wilayah_str}")

# 5. Target Platform Media
st.sidebar.subheader("🌐 Target Platform")
check_news = st.sidebar.checkbox("Berita Web / Google News", value=True)
check_x = st.sidebar.checkbox("Twitter / X", value=True)
check_fb = st.sidebar.checkbox("Facebook", value=True)
check_ig = st.sidebar.checkbox("Instagram & Threads", value=True)
check_tiktok = st.sidebar.checkbox("TikTok", value=True)

# Tombol Eksekusi
btn_search = st.sidebar.button("🔍 Mulai Pemantauan Realtime", use_container_width=True, type="primary")

# Area Hasil Pencarian
if btn_search:
    if not keywords:
        st.error("Harap masukkan kata kunci pencarian!")
    else:
        st.info(f"🔄 Sedang memindai postingan 7 hari terakhir untuk kata kunci: **{keywords}** di wilayah **{wilayah_str}**...")
        
        # Buat query yang fleksibel
        query_text = f"{keywords} {wilayah_str}"
        targets = []
        
        if check_news: targets.append(("Berita Web", query_text))
        if check_x: targets.append(("Twitter / X", f"site:x.com {query_text}"))
        if check_fb: targets.append(("Facebook", f"site:facebook.com {query_text}"))
        if check_ig: targets.append(("Instagram/Threads", f"site:instagram.com {query_text}"))
        if check_tiktok: targets.append(("TikTok", f"site:tiktok.com {query_text}"))
        
        results = []
        ddgs = DDGS()
        
        progress_bar = st.progress(0)
        total_targets = len(targets)
        
        for idx, (source_name, q_str) in enumerate(targets):
            try:
                # Menggunakan parameter timelimit='w' untuk 7 hari terakhir
                search_results = ddgs.text(
                    keywords=q_str, 
                    region="id-id", 
                    timelimit=time_limit_code, 
                    max_results=10
                )
                
                if search_results:
                    for res in search_results:
                        results.append({
                            "Platform": source_name,
                            "Judul / Cuplikan": res.get("title", ""),
                            "Ringkasan Konten": res.get("body", ""),
                            "Link Tautan": res.get("href", ""),
                            "Waktu Penarikan": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
            except Exception as e:
                st.warning(f"Gagal memindai {source_name}: {e}")
            
            progress_bar.progress((idx + 1) / total_targets)
            
        st.success(f"✅ Pemantauan selesai! Ditemukan {len(results)} hasil pencarian.")
        
        if results:
            df = pd.DataFrame(results)
            
            tab1, tab2 = st.tabs(["📋 Tabel & Detail Hasil", "📥 Download Data (CSV)"])
            
            with tab1:
                st.subheader("Statistik Hasil per Platform")
                st.bar_chart(df["Platform"].value_counts())
                
                st.subheader("Daftar Temuan Postingan & Berita")
                for index, row in df.iterrows():
                    with st.expander(f"[{row['Platform']}] {row['Judul / Cuplikan']}"):
                        st.write(f"**Ringkasan:** {row['Ringkasan Konten']}")
                        st.write(f"**Tautan:** [Buka Postingan / Berita]({row['Link Tautan']})")
                        st.caption(f"Waktu Penarikan: {row['Waktu Penarikan']}")

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
            st.warning("Pencarian tidak menemukan hasil. Coba sederhanakan kata kunci (misal hanya: 'banjir Palu' atau 'karhutla Sulteng').")
else:
    st.write("👉 Pilih rentang waktu dan parameter di **sidebar kiri**, lalu klik **'Mulai Pemantauan Realtime'**.")
