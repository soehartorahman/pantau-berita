import streamlit as st
from duckduckgo_search import DDGS
import pandas as pd
from datetime import datetime

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="BMKG Sulteng - Early Warning & Issue Monitor",
    page_icon="🌩️",
    layout="wide"
)

# Header Utama
st.title("🌩️ BMKG SPAG Lore Lindu Bariri")
st.subheader("Sistem Pemantauan Media Sosial & Berita Terkini (Sulawesi Tengah)")
st.markdown("---")

# Sidebar - Parameter Input
st.sidebar.header("⚙️ Filter & Parameter Pencarian")

# 1. Kategori Bidang
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

# Set kata kunci bawaan berdasarkan kategori
default_keywords = ""
if "Hidrometeorologi" in kategori:
    default_keywords = "banjir OR longsor OR kekeringan OR angin kencang OR puting beliung"
elif "Kualitas Udara" in kategori:
    default_keywords = "karhutla OR kebakaran hutan OR asap OR kualitas udara OR ISPU"
elif "Gempabumi" in kategori:
    default_keywords = "gempa OR gempabumi OR tsunami OR kerusakan bangunan"
elif "Pertanian" in kategori:
    default_keywords = "gagal panen OR kekeringan sawah OR hama iklim OR cuaca ekstrim pertanian"
else:
    default_keywords = "banjir OR karhutla OR gempa OR iklim"

# 2. Input Kata Kunci
keywords = st.sidebar.text_area("Kata Kunci Spesifik (Pisahkan dengan OR / spasi):", value=default_keywords)

# 3. Cakupan Wilayah
wilayah_option = st.sidebar.selectbox(
    "Pilih Cakupan Wilayah:",
    ["Sulawesi Tengah (Spesifik Kabupaten/Kota)", "Indonesia (Nasional)", "Kustom Wilayah Lain"]
)

if wilayah_option == "Sulawesi Tengah (Spesifik Kabupaten/Kota)":
    wilayah_str = "Palu OR Sigi OR Donggala OR Poso OR Parigi OR Morowali OR Tolitoli OR Buol OR Banggai OR Tojo Una-Una"
elif wilayah_option == "Indonesia (Nasional)":
    wilayah_str = "Indonesia"
else:
    wilayah_str = st.sidebar.text_input("Masukkan Wilayah Kustom:", value="Sulawesi Tengah")

st.sidebar.info(f"📍 **Target Wilayah Active:**\n{wilayah_str}")

# 4. Target Platform Media
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
        st.info("🔄 Sedang memindai postingan media sosial dan berita terkini...")
        
        base_query = f"({keywords}) ({wilayah_str})"
        targets = []
        
        if check_news: targets.append(("Berita Web", base_query))
        if check_x: targets.append(("Twitter / X", f"site:x.com {base_query}"))
        if check_fb: targets.append(("Facebook", f"site:facebook.com {base_query}"))
        if check_ig: targets.append(("Instagram/Threads", f"(site:instagram.com OR site:threads.net) {base_query}"))
        if check_tiktok: targets.append(("TikTok", f"site:tiktok.com {base_query}"))
        
        results = []
        ddgs = DDGS()
        
        progress_bar = st.progress(0)
        total_targets = len(targets)
        
        for idx, (source_name, query_str) in enumerate(targets):
            try:
                # Pencarian via DuckDuckGo Text & News Search
                search_results = ddgs.text(query_str, max_results=8)
                for res in search_results:
                    results.append({
                        "Platform": source_name,
                        "Judul / Cuplikan": res.get("title", ""),
                        "Ringkasan Konten": res.get("body", ""),
                        "Link Tautan": res.get("href", ""),
                        "Waktu Ditemukan": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            except Exception as e:
                st.warning(f"Gagal memindai {source_name}: {e}")
            
            progress_bar.progress((idx + 1) / total_targets)
            
        st.success(f"✅ Pemantauan selesai! Ditemukan {len(results)} potensi isu hangat.")
        
        if results:
            df = pd.DataFrame(results)
            
            # Tab Tampilan Data
            tab1, tab2 = st.tabs(["📋 Tabel & Detail Hasil", "📥 Download Data (Excel/CSV)"])
            
            with tab1:
                # Tampilkan Ringkasan Jumlah per Platform
                st.subheader("Statistik Hasil per Platform")
                st.bar_chart(df["Platform"].value_counts())
                
                st.subheader("Daftar Temuan Postingan & Berita")
                for index, row in df.iterrows():
                    with st.expander(f"[{row['Platform']}] {row['Judul / Cuplikan']}"):
                        st.write(f"**Ringkasan:** {row['Ringkasan Konten']}")
                        st.write(f"**Tautan:** [Buka Postingan / Berita]({row['Link Tautan']})")
                        st.caption(f"Waktu Penarikan: {row['Waktu Ditemukan']}")

            with tab2:
                st.subheader("Unduh Laporan untuk Analisis Lebih Lanjut")
                
                # Download CSV
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Download Data (Format CSV)",
                    data=csv,
                    file_name=f"Laporan_BMKG_Sulteng_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )
        else:
            st.warning("Tidak ditemukan postingan/berita terkini dengan kombinasi kata kunci dan wilayah tersebut.")
else:
    st.write("👉 Silakan atur parameter di **sidebar kiri**, lalu klik tombol **'Mulai Pemantauan Realtime'** untuk memulai analisis.")
