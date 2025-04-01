import streamlit as st
import pandas as pd
import io
from openpyxl import load_workbook
from difflib import SequenceMatcher

st.set_page_config(page_title="Výpis dle kritérií")
st.title("Vyhledání dle klíče (PM+LM OP1)")

col1, col2 = st.columns(2)
with col1:
    lab_file = st.file_uploader("Nahraj laboratorní deník (XLSX, list 'Evidence zkoušek zhotovitele')", type="xlsx", key="lab")
with col2:
    klic_file = st.file_uploader("Nahraj klíč (XLSX se seznamem zkoušek)", type="xlsx", key="klic")

if lab_file and klic_file:
    lab_bytes = lab_file.read()
    klic_bytes = klic_file.read()

    df = pd.read_excel(io.BytesIO(lab_bytes), sheet_name="Evidence zkoušek zhotovitele")
    workbook = load_workbook(io.BytesIO(klic_bytes))

    # Načíst klíčové hodnoty z listu "seznam zkoušek PM+LM OP1"
    try:
        klic_df = pd.read_excel(io.BytesIO(klic_bytes), sheet_name="seznam zkoušek PM+LM OP1", header=None)
        konstrukce = str(klic_df.at[1, 1]).strip().lower()
        zkouska = str(klic_df.at[1, 2]).strip().lower()
        stanice = str(klic_df.at[1, 3]).strip().lower()
    except Exception as e:
        st.error(f"Chyba při čtení klíče: {e}")
        st.stop()

    # Předzpracování dat
    konstrukce = konstrukce.replace("-", " ")
    zkousky = [z.strip().lower().replace("-", " ") for z in zkouska.split(",") if z.strip()]
    stanice_list = [s.strip().lower() for s in stanice.split(",") if s.strip()]

    # Úprava názvů sloupců pro jistotu
    df.columns.values[10] = "K"  # konstrukční prvek
    df.columns.values[13] = "N"  # druh zkoušky
    df.columns.values[7] = "H"   # staničení

    def contains_relaxed(text, keyword):
        return all(k in text for k in keyword.split())

    match_count = 0
    matched_rows = []

    for _, row in df.iterrows():
        text_konstrukce = str(row.get("K", "")).lower().replace("-", " ").strip()
        text_zkouska = str(row.get("N", "")).lower().replace("-", " ").strip()
        text_stanice = str(row.get("H", "")).lower().strip()

        konstrukce_ok = contains_relaxed(text_konstrukce, konstrukce)
        zkouska_ok = any(z in text_zkouska for z in zkousky)
        stanice_ok = any(s in text_stanice for s in stanice_list)

        if konstrukce_ok and zkouska_ok and stanice_ok:
            match_count += 1
            matched_rows.append(row)

    # Zobrazení nalezených řádků
    if matched_rows:
        st.subheader("🔎 Nalezené odpovídající řádky")
        st.dataframe(pd.DataFrame(matched_rows))

    # Zapsání výsledku do souboru
    try:
        ws = workbook["PM - OP1"]
        ws["D2"] = match_count
        output = io.BytesIO()
        workbook.save(output)

        st.success(f"✅ Nalezeno {match_count} shod. Výsledek zapsán do souboru (list 'PM - OP1', buňka D2)")
        st.download_button(
            label="📥 Stáhnout aktualizovaný soubor",
            data=output.getvalue(),
            file_name="klic_vyhodnoceny.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Chyba při zápisu výsledku: {e}")
