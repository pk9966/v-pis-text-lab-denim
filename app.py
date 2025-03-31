import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Výpis dle kritérií")
st.title("Filtrování laboratorního deníku dle kritérií")

lab_file = st.file_uploader("Nahraj laboratorní deník (list 'Evidence zkoušek zhotovitele')", type="xlsx")

konstrukce = st.text_input("Zadej text konstrukčního prvku (např. zásyp, základová spára)")
druhy_zk = st.text_input("Zadej druh zkoušky (např. D, SZZ)")
staniceni = st.text_input("Zadej staničení (např. OP1, OP2)")  # Nepovinné
cisla_objektu = st.multiselect("Vyber čísla objektů (sloupec C, volitelné)", options=["209", "210", "211", "212", "213", "214", "215"])

debug = st.checkbox("🔧 Zobrazit důvody vyloučených řádků při nenalezení shody")

if lab_file and konstrukce and druhy_zk:
    output_lines = []
    lab_bytes = lab_file.read()
    df = pd.read_excel(io.BytesIO(lab_bytes), sheet_name="Evidence zkoušek zhotovitele")

    druhy_zk_list = [z.strip().lower() for z in druhy_zk.split(",") if z.strip()]
    stanice_list = [s.strip().lower() for s in staniceni.split(",") if s.strip()]  # Pouze pro informaci, není vyžadováno
    konstrukce_lower = konstrukce.lower().replace("-", " ")

    st.subheader("Výsledky")
    match_count = 0

    for index, row in df.iterrows():

        text_konstrukce = str(row.get("K", "")).lower().replace("-", " ")
        text_zkouska = str(row.get("N", "")).lower().replace("-", " ")
        text_stanice = str(row.get("H", "")).lower()
        konstrukce_ok = any(sub in text_konstrukce for sub in konstrukce_lower.split())
        zkouska_ok = any(z in text_zkouska or z in text_zkouska.replace(" ", "") for z in druhy_zk_list)
        cislo_ok = True if not cisla_objektu else False
        if cisla_objektu:
            text_cislo = str(row.get("C", "")).replace("-", " ").lower()
            for c in cisla_objektu:
                if c in text_cislo or c in text_cislo.replace(" ", ""):
                    cislo_ok = True
                    break
            if not cislo_ok and debug:
                st.markdown(f"❌ číslo objektu (řádek {index + 2}): očekáváno {', '.join(cisla_objektu)}, nalezeno {text_cislo}")

        if konstrukce_ok and zkouska_ok and cislo_ok:
            match_count += 1
            if debug:
                detail_ok = []
                if konstrukce_ok: detail_ok.append("✅ konstrukce")
                if zkouska_ok: detail_ok.append("✅ zkouška")
                if cislo_ok: detail_ok.append("✅ číslo objektu")
            line_text = f"Řádek {index + 2}: " + " | ".join(str(v) for v in row.values if pd.notna(v))
            st.markdown("✅ " + line_text)
            output_lines.append(line_text)
            if debug:
                st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;" + ", ".join(detail_ok))

    st.success(f"Nalezeno {match_count} vyhovujících záznamů.")

    if match_count > 0:
        txt_output = "\n".join(output_lines)
        st.download_button(
            label="📄 Stáhnout výsledky jako TXT",
            data=txt_output,
            file_name="vysledky_filtrace.txt",
            mime="text/plain"
        )
