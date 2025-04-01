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

cislo_objektu_input = st.text_input("Volitelné: Číslo objektu pro filtrování (např. 209)").strip()

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

    konstrukce = konstrukce.replace("-", " ")
    zkousky = [z.strip().lower().replace("-", " ") for z in zkouska.split(",") if z.strip()]
    stanice_list = [s.strip().lower() for s in stanice.split(",") if s.strip()]
    cislo_objektu_input = cislo_objektu_input.replace(" ", "")

    df.columns.values[10] = "K"  # konstrukční prvek
    df.columns.values[13] = "N"  # druh zkoušky
    df.columns.values[7] = "H"   # staničení
    df.columns.values[2] = "C"   # číslo objektu

    def contains_relaxed(text, keyword):
        return all(k in text for k in keyword.split())

    match_count = 0
    matched_rows = []

    for _, row in df.iterrows():
        text_konstrukce = str(row.get("K", "")).lower().replace("-", " ").strip()
        text_zkouska = str(row.get("N", "")).lower().replace("-", " ").strip()
        text_stanice = str(row.get("H", "")).lower().strip()
        text_objekt = str(row.get("C", "")).replace(" ", "").lower()

        konstrukce_ok = contains_relaxed(text_konstrukce, konstrukce)
        zkouska_ok = any(z in text_zkouska for z in zkousky)
        stanice_ok = any(s in text_stanice for s in stanice_list) if stanice_list else True
        objekt_ok = True
        if cislo_objektu_input:
            objekt_ok = cislo_objektu_input in text_objekt

        if konstrukce_ok and zkouska_ok and stanice_ok and objekt_ok:
            match_count += 1
            matched_rows.append({
                "D (Datum odběru)": row.iloc[5],
                "E (Staničení)": row["H"],
                "H (Konstrukční část)": row.iloc[9],
                "J (Konstrukční prvek)": row["K"],
                "K (Materiál)": row.iloc[11],
                "L (Datum zkoušky)": row.iloc[12],
                "N (Druh zkoušky)": row["N"],
                "O (Požadovaná hodnota)": row.iloc[14],
                "P (Naměřená hodnota)": row.iloc[15],
                "Q (Hodnocení)": row.iloc[16],
            })

    if matched_rows:
        st.subheader("🔎 Nalezené odpovídající řádky")
        st.dataframe(pd.DataFrame(matched_rows))

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
