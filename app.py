import streamlit as st
import pandas as pd
import io
from difflib import SequenceMatcher

st.set_page_config(page_title="Výpis dle kritérií")
st.title("Filtrování laboratorního deníku dle kritérií")

lab_file = st.file_uploader("Nahraj laboratorní deník (list 'Evidence zkoušek zhotovitele')", type="xlsx")

konstrukce = st.text_input("Zadej text konstrukčního prvku (např. zásyp, základová spára)")
druhy_zk = st.text_input("Zadej druh zkoušky (např. D, SZZ)")
staniceni = st.text_input("Zadej staničení (např. OP1, OP2)")  # Nepovinné
cisla_objektu = st.multiselect("Vyber čísla objektů (sloupec C, volitelné)", options=["209", "210", "211", "212", "213", "214", "215"])

debug = st.checkbox("🔧 Zobrazit důvody vyloučených řádků při nenalezení shody")

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def contains_fuzzy(text, keyword, threshold=0.6):
    text = text.lower().replace("-", " ").strip()
    keyword = keyword.lower().replace("-", " ").strip()
    return keyword in text or similar(text, keyword) >= threshold

if lab_file and konstrukce and druhy_zk:
    output_lines = []
    lab_bytes = lab_file.read()
    df = pd.read_excel(io.BytesIO(lab_bytes), sheet_name="Evidence zkoušek zhotovitele")

    druhy_zk_list = [z.strip().lower() for z in druhy_zk.split(",") if z.strip()]
    konstrukce_clean = konstrukce.lower().replace("-", " ").strip()

    st.subheader("Výsledky")
    match_count = 0

    for index, row in df.iterrows():

        text_konstrukce = str(row.get("K", "")).lower().replace("-", " ").strip()
        text_zkouska = str(row.get("N", "")).lower().replace("-", " ").strip()
        text_stanice = str(row.get("H", "")).lower()
        text_cislo = str(row.get("C", "")).replace("-", " ").lower()

        konstrukce_ok = contains_fuzzy(text_konstrukce, konstrukce_clean)
        zkouska_ok = any(z in text_zkouska.replace(" ", "") for z in druhy_zk_list)
        cislo_ok = True if not cisla_objektu else any(
            c in text_cislo or c in text_cislo.replace(" ", "") for c in cisla_objektu
        )

        if konstrukce_ok and zkouska_ok and cislo_ok:
            match_count += 1
            line_text = f"Řádek {index + 2}: " + " | ".join(str(v) for v in row.values if pd.notna(v))
            st.markdown("✅ " + line_text)
            output_lines.append(line_text)
            if debug:
                detail_ok = []
                if konstrukce_ok: detail_ok.append("✅ konstrukce")
                if zkouska_ok: detail_ok.append("✅ zkouška")
                if cislo_ok: detail_ok.append("✅ číslo objektu")
                st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;" + ", ".join(detail_ok))
        else:
            if debug:
                reason = []
                if not konstrukce_ok: reason.append("❌ konstrukce")
                if not zkouska_ok: reason.append("❌ zkouška")
                if not cislo_ok: reason.append("❌ číslo objektu")
                line_text = f"Řádek {index + 2}: " + " | ".join(str(v) for v in row.values if pd.notna(v))
                st.markdown("🚫 " + line_text)
                st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;" + ", ".join(reason))

    st.success(f"Nalezeno {match_count} vyhovujících záznamů.")

    if match_count > 0:
        txt_output = "\n".join(output_lines)
        st.download_button(
            label="📄 Stáhnout výsledky jako TXT",
            data=txt_output,
            file_name="vysledky_filtrace.txt",
            mime="text/plain",
            key="download-txt"
        )
