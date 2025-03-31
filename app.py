import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Výpis dle kritérií")
st.title("Filtrování laboratorního deníku dle kritérií")

lab_file = st.file_uploader("Nahraj laboratorní deník (list 'Evidence zkoušek zhotovitele')", type="xlsx")

konstrukce = st.text_input("Zadej text konstrukčního prvku (např. zásyp, základová spára)")
druhy_zk = st.text_input("Zadej druh zkoušky (např. D, SZZ)")
staniceni = st.text_input("Zadej staničení (např. OP1, OP2)")

if lab_file and konstrukce and druhy_zk and staniceni:
    lab_bytes = lab_file.read()
    df = pd.read_excel(io.BytesIO(lab_bytes), sheet_name="Evidence zkoušek zhotovitele")

    druhy_zk_list = [z.strip().lower() for z in druhy_zk.split(",") if z.strip()]
    stanice_list = [s.strip().lower() for s in staniceni.split(",") if s.strip()]
    konstrukce_lower = konstrukce.lower()

    st.subheader("Výsledky")
    match_count = 0

    for index, row in df.iterrows():
        text_row = " ".join(str(v).lower() for v in row.values if pd.notna(v))
        konstrukce_ok = konstrukce_lower in text_row
        zkouska_ok = any(z in text_row for z in druhy_zk_list)
        stanice_ok = any(s in text_row for s in stanice_list)

        if konstrukce_ok and zkouska_ok and stanice_ok:
            match_count += 1
            st.markdown(f"✅ **Řádek {index + 2}:** " + " | ".join(str(v) for v in row.values if pd.notna(v)))

    if match_count == 0:
        st.warning("Nenalezena žádná shoda podle zadaných kritérií.")
    else:
        st.success(f"Nalezeno {match_count} vyhovujících záznamů.")
