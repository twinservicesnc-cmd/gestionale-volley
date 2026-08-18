import time
import streamlit as st
import json
import os
import shutil
import pandas as pd
import requests
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def genera_pdf_ricevuta(atleta, importo, societa):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Intestazione e Riferimenti Normativi
    p.setFont("Helvetica-Bold", 13)
    p.drawString(50, height - 40, "RICEVUTA DI PAGAMENTO")
    p.setFont("Helvetica", 8)
    p.drawString(50, height - 55, "Ai sensi e per gli effetti dell'art. 1, c. 319 L. n. 296 del 27.12.2006")
    
    # Dati Società / Rappresentante
    testo_soc = (
        "Il sottoscritto Enrico Galleano, nato a Torino il 25 novembre 1977, in qualità "
        "di presidente e legale rappresentante della Pallavolo Pinerolo S.S.D A.R.L - "
        "cod. Fipav 010050225 - N. registrazione CONI 51944, con sede in Pinerolo (TO) "
        "viale Grande Torino, 2 - P. IVA/C.F. 06598960018"
    )
    
    text_obj = p.beginText(50, height - 85)
    text_obj.setFont("Helvetica", 7.5)
    for line in [testo_soc[i:i+105] for i in range(0, len(testo_soc), 105)]:
        text_obj.textLine(line)
    p.drawText(text_obj)
    
    # Attestazione Pagamento
    data_odierna = datetime.now().strftime("%d/%m/%Y")
    stagione = atleta.get('stagione', '2026/2027')
    cognome_nome = f"{atleta.get('cognome', '')} {atleta.get('nome', '')}".upper()
    
    testo_attesta = (
        f"ATTESTA di aver ricevuto in data {data_odierna} la somma di Euro {importo:,.2f} "
        f"per la quota associativa e di partecipazione all'attività sportiva di Pallavolo "
        f"svolta nella stagione sportiva {stagione} dall'associata/o:"
    )
    
    text_obj2 = p.beginText(50, height - 150)
    text_obj2.setFont("Helvetica", 8.5)
    for line in [testo_attesta[i:i+95] for i in range(0, len(testo_attesta), 95)]:
        text_obj2.textLine(line)
    p.drawText(text_obj2)
    
    # Dati Anagrafici Atleta
    p.setFont("Helvetica-Bold", 9)
    p.drawString(50, height - 200, f"COGNOME E NOME: {cognome_nome}")
    p.setFont("Helvetica", 8.5)
    p.drawString(50, height - 215, f"LUOGO E DATA DI NASCITA: {atleta.get('luogo_data_nascita', '______________________')}")
    p.drawString(50, height - 230, f"CODICE FISCALE: {atleta.get('codice_fiscale', '_________________________________')}")
    
    # Nota Fiscale / IRPEF
    testo_irpef = (
        "La presente attestazione viene rilasciata anche ai fini della detrazione IRPEF "
        "prevista dall'art. 15, c. 1, lett. I-quinquies, D.P.R. 917/1986 e relativo decreto "
        "di attuazione, qualora spettante."
    )
    
    text_obj3 = p.beginText(50, height - 270)
    text_obj3.setFont("Helvetica", 7.5)
    for line in [testo_irpef[i:i+105] for i in range(0, len(testo_irpef), 105)]:
        text_obj3.textLine(line)
    p.drawText(text_obj3)
    
    # Chiusura e Firma
    p.setFont("Helvetica", 8.5)
    p.drawString(50, height - 330, f"In fede. Pinerolo, {data_odierna}")
    
    p.setFont("Helvetica-Bold", 8.5)
    p.drawString(350, height - 320, "PALLAVOLO PINEROLO S.S.D A.R.L.")
    p.setFont("Helvetica", 8.5)
    p.drawString(350, height - 335, "Il Presidente")
    p.drawString(350, height - 350, "ENRICO GALLEANO")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue()# --- CONFIGURAZIONE E FILE ---
FILE_UTENTI = "utenti.json"
FILE_GRUPPI = "gruppi.json"
FILE_CATEGORIE = "categorie.json"
FILE_ATLETE = "atlete.json"
FILE_CONFIG_QUOTE = "config_quote.json"
FILE_BUDGET = "budget_societa.json"
FILE_SQUADRE = "squadre_campionati.json"
FILE_GARE = "calendario_gare.json"
FILE_STORICO_TECNICO = "storico_crescita_atlete.json"
FILE_SCOUT = "scout_squadre.json"
FILE_CONFIG_SOCIETA = "config_societa.json"
FILE_CONFIG_VOCI_COSTI = "config_voci_costi.json"
FILE_CONFIG_COSTI_STANDARD = "config_costi_standard.json"
CARTELLA_BACKUP = "backup"

URL_MASTER_CSV = "https://docs.google.com/spreadsheets/d/10qQFoLrMv0YzO2pVzKjW8L7am96diQq4Eczu4QYRhBg/export?format=csv&gid=1688964221"
LINK_GOOGLE_FORM = "https://forms.gle/suSyRvS2spUM7bk78"
LINK_GOOGLE_SHEETS_EMBED = "https://docs.google.com/spreadsheets/d/10qQFoLrMv0YzO2pVzKjW8L7am96diQq4Eczu4QYRhBg/edit?usp=sharing"

CARTELLA_ALLEGATI = os.path.abspath("allegati")
if not os.path.exists(CARTELLA_ALLEGATI):
    try:
        os.makedirs(CARTELLA_ALLEGATI)
    except Exception:
        pass

st.set_page_config(page_title="Gestionale Societario Volley", page_icon="🏐", layout="wide")

# --- CSS PERSONALIZZATO ---
st.markdown("""
    <style>
    .user-box { background-color: #e8f4fd; padding: 10px 15px; border-radius: 6px; border-left: 5px solid #1f77b4; font-weight: bold; color: #0c5460; }
    .legenda-container { background-color: #f8f9fa; padding: 8px 15px; border-radius: 6px; border: 1px solid #dee2e6; margin-bottom: 15px; font-size: 14px; font-weight: bold; color: #333; display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }
    .badge-completa { background-color: #d4edda; color: #155724; padding: 2px 8px; border-radius: 4px; border: 1px solid #c3e6cb; }
    .badge-incompleta { background-color: #f8d7da; color: #721c24; padding: 2px 8px; border-radius: 4px; border: 1px solid #f5c6cb; }
    
    .rate-grid-container { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
    .rata-card { background-color: #e7f1ff; border: 1px solid #b8daff; border-radius: 8px; padding: 12px 15px; flex: 1; min-width: 200px; text-align: center; color: #004085; }
    .rata-card-title { font-size: 13px; font-weight: bold; text-transform: uppercase; margin-bottom: 4px; color: #002752; }
    .rata-card-val { font-size: 16px; font-weight: bold; }
    .rata-card-data { font-size: 13px; color: #495057; margin-top: 2px; }

    div.stLinkButton > a { background-color: #28a745 !important; color: white !important; font-weight: bold; border-radius: 6px; }
    </style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI BACKUP E SERVIZIO ---
def esegui_backup():
    if not os.path.exists(CARTELLA_BACKUP):
        os.makedirs(CARTELLA_BACKUP)
    data_oggi = datetime.now().strftime("%Y%m%d_%H%M%S")
    for file in [FILE_UTENTI, FILE_GRUPPI, FILE_CATEGORIE, FILE_ATLETE, FILE_CONFIG_QUOTE, FILE_BUDGET, FILE_SQUADRE, FILE_GARE, FILE_STORICO_TECNICO, FILE_SCOUT, FILE_CONFIG_SOCIETA, FILE_CONFIG_VOCI_COSTI, FILE_CONFIG_COSTI_STANDARD]:
        if os.path.exists(file):
            try:
                shutil.copy(file, os.path.join(CARTELLA_BACKUP, f"{file}_{data_oggi}.bak"))
            except:
                pass

def controlla_visita(data_str):
    if not data_str or str(data_str).lower() in ["nan", "none", ""]: return "🔴 MANCANTE"
    try:
        data_visita = datetime.strptime(str(data_str).strip(), "%d/%m/%Y")
        oggi = datetime.now()
        if data_visita < oggi: return "🔴 SCADUTA"
        elif (data_visita - oggi).days < 30: return "🟡 IN SCADENZA"
        return "🟢 VALIDA"
    except: return "🔴 VERIFICA"

def carica_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return default

def salva_json_sicuro(file, dati):
    esegui_backup()
    temp_file = file + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=4, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_file, file)

def normalizza_nome_gruppo(nome):
    if not nome or str(nome).lower() in ["nan", "none", ""]: return ""
    return str(nome).strip().title()

def safe_float(val, default=0.0):
    if val is None: return default
    try:
        return float(str(val).replace(',', '.'))
    except:
        return default

def ricalcola_finanze(atleta):
    sconto_perc = round(safe_float(atleta.get("sconto", 0.0)), 2)
    quota_tot = round(safe_float(atleta.get("quota_tot", 0.0)), 2)
    
    r1_imp = safe_float(atleta.get("r1_imp", 0.0))
    r2_imp = safe_float(atleta.get("r2_imp", 0.0))
    r3_imp = safe_float(atleta.get("r3_imp", 0.0))
    r4_imp = safe_float(atleta.get("r4_imp", 0.0))

    r1_versato = safe_float(atleta.get("r1_versato", r1_imp))
    r2_versato = safe_float(atleta.get("r2_versato", r2_imp))
    r3_versato = safe_float(atleta.get("r3_versato", r3_imp))
    r4_versato = safe_float(atleta.get("r4_versato", r4_imp))
    
    r1_data = str(atleta.get("r1_data", "")).strip()
    r2_data = str(atleta.get("r2_data", "")).strip()
    r3_data = str(atleta.get("r3_data", "")).strip()
    r4_data = str(atleta.get("r4_data", "")).strip()

    importo_sconto = round(r1_imp * (sconto_perc / 100.0), 2)
    tot_scontato = round(max(0.0, quota_tot - importo_sconto), 2)
    atleta["tot_scontato"] = tot_scontato

    versato = 0.0
    rate_pagate_count = 0
    tot_rate_previste = 1
    nr_str = str(atleta.get("n_rate", "1 Rata"))
    if "2" in nr_str: tot_rate_previste = 2
    elif "3" in nr_str: tot_rate_previste = 3
    elif "4" in nr_str: tot_rate_previste = 4

    if r1_data and r1_data.lower() not in ["nan", "none", ""]: versato += r1_versato; rate_pagate_count += 1
    if tot_rate_previste >= 2 and r2_data and r2_data.lower() not in ["nan", "none", ""]: versato += r2_versato; rate_pagate_count += 1
    if tot_rate_previste >= 3 and r3_data and r3_data.lower() not in ["nan", "none", ""]: versato += r3_versato; rate_pagate_count += 1
    if tot_rate_previste >= 4 and r4_data and r4_data.lower() not in ["nan", "none", ""]: versato += r4_versato; rate_pagate_count += 1

    if "storico_pagamenti" in atleta and isinstance(atleta["storico_pagamenti"], list):
        try:
            tot_storico = sum(safe_float(p.get("importo", 0)) for p in atleta["storico_pagamenti"])
            if tot_storico > versato:
                versato = tot_storico
        except:
            pass

    atleta["quota_versata"] = round(versato, 2)
    saldo_rimanente = round(tot_scontato - versato, 2)
    atleta["saldo_rimanente"] = saldo_rimanente
    atleta["rate_pagate_str"] = f"{rate_pagate_count}/{tot_rate_previste}"
    
    atleta["stato_rate"] = "🔴 INCOMPLETA" if saldo_rimanente > 0.0 else "🟢 COMPLETA"
    atleta["stato_visita"] = controlla_visita(atleta.get("scad_visita", ""))
    return atleta

def carica_atlete():
    atlete_caricate = carica_json(FILE_ATLETE, [])
    for a in atlete_caricate:
        if "gruppo" in a and a["gruppo"]: a["gruppo"] = normalizza_nome_gruppo(a["gruppo"])
        if "gruppo2" in a and a["gruppo2"] and str(a["gruppo2"]).lower() not in ["nan", "none", "nessuno"]: 
            a["gruppo2"] = normalizza_nome_gruppo(a["gruppo2"])
        else:
            a["gruppo2"] = ""
        if "storico_pagamenti" not in a:
            a["storico_pagamenti"] = []
        if "valutazioni_tecniche" not in a:
            a["valutazioni_tecniche"] = {}
        ricalcola_finanze(a)
    if atlete_caricate: salva_atlete(atlete_caricate)
    return atlete_caricate

def salva_atlete(atlete):
    for a in atlete: ricalcola_finanze(a)
    salva_json_sicuro(FILE_ATLETE, atlete)

# --- CONFIGURAZIONE NOME SOCIETA & VOCI COSTI ---
config_societa = carica_json(FILE_CONFIG_SOCIETA, {"nome": "Monviso Volley"})
nome_societa = config_societa.get("nome", "Monviso Volley")

voci_costi_default = ["rimborso allenatore", "aiuto allenatore", "tuta", "zaino", "divisa allenamento", "palestre", "gare", "tornei", "tesseramento", "etc", "altro"]
voci_costi_configurate = carica_json(FILE_CONFIG_VOCI_COSTI, voci_costi_default)

# --- PULIZIA GRUPPI ---
gruppi_standard_base = ["Minivolley", "Scuola", "Gruppi Promozionali", "Under 14", "Under 16", "Under 18", "Serie C", "Serie D"]
gruppi_grezzi = carica_json(FILE_GRUPPI, gruppi_standard_base)
visti = set()
gruppi_puliti = []
for g in gruppi_grezzi:
    norm = normalizza_nome_gruppo(g)
    if norm and norm.lower() not in visti:
        visti.add(norm.lower())
        gruppi_puliti.append(norm)
salva_json_sicuro(FILE_GRUPPI, gruppi_puliti)

# --- INIZIALIZZAZIONE STATO UTENTI ---
utenti_base = carica_json(FILE_UTENTI, {"admin": {"password": "monviso", "ruolo": "Amministratore", "area": ["Area Amministratori", "Promozionale", "Giovanile", "Gestionale", "Area Tecnica", "Segreteria", "Report Finanziario", "Bilancio and Budget"]}})
if "admin" not in utenti_base:
    utenti_base["admin"] = {"password": "monviso", "ruolo": "Amministratore", "area": ["Area Amministratori", "Promozionale", "Giovanile", "Gestionale", "Area Tecnica", "Segreteria", "Report Finanziario", "Bilancio and Budget"]}
salva_json_sicuro(FILE_UTENTI, utenti_base)

if "utenti" not in st.session_state: st.session_state["utenti"] = utenti_base
if "gruppi_societa" not in st.session_state: st.session_state["gruppi_societa"] = gruppi_puliti
if "categorie_societa" not in st.session_state: st.session_state["categorie_societa"] = carica_json(FILE_CATEGORIE, ["Promozionale", "Giovanile Under", "Senior / Serie", "Master"])
if "config_quote" not in st.session_state: st.session_state["config_quote"] = carica_json(FILE_CONFIG_QUOTE, {})
if "budget_societa" not in st.session_state: st.session_state["budget_societa"] = carica_json(FILE_BUDGET, {})
if "config_costi_standard" not in st.session_state: st.session_state["config_costi_standard"] = carica_json(FILE_CONFIG_COSTI_STANDARD, {})
if "squadre_campionati" not in st.session_state: st.session_state["squadre_campionati"] = carica_json(FILE_SQUADRE, {})
if "calendario_gare" not in st.session_state: st.session_state["calendario_gare"] = carica_json(FILE_GARE, {})
if "storico_tecnico" not in st.session_state: st.session_state["storico_tecnico"] = carica_json(FILE_STORICO_TECNICO, {})
if "scout_squadre" not in st.session_state: st.session_state["scout_squadre"] = carica_json(FILE_SCOUT, {})
if "voci_costi_config" not in st.session_state: st.session_state["voci_costi_config"] = voci_costi_configurate
if "elenco_atlete" not in st.session_state: st.session_state["elenco_atlete"] = carica_atlete()
if "utente_autenticato" not in st.session_state: st.session_state["utente_autenticato"] = False

def crea_scheda_standard(dati, stagione_attiva="2026/2027"):
    gruppo = normalizza_nome_gruppo(dati.get("gruppo", "Minivolley"))
    if not gruppo: gruppo = "Minivolley"
    categoria = dati.get("categoria", "Promozionale")
    
    config_quote_salvate = st.session_state.get("config_quote", {})
    config_gruppo = {}
    for g_chiave, g_val in config_quote_salvate.items():
        if g_chiave.strip().lower() == gruppo.strip().lower():
            config_gruppo = g_val
            break
    
    if not config_gruppo or safe_float(config_gruppo.get("quota_tot", 0)) == 0.0:
        quota_default = 500.0
        config_gruppo = {
            "n_rate": "1 Rata", "quota_tot": quota_default,
            "r1_imp": quota_default, "r2_imp": 0.0, "r3_imp": 0.0, "r4_imp": 0.0,
            "r1_data": "", "r2_data": "", "r3_data": "", "r4_data": ""
        }
    
    standard = {
        "cognome": "", "nome": "", "sesso": "M", "cf": "", "data_nas": "",
        "luogo_nas": "", "prov_nas": "", "indirizzo_res": "", "citta_res": "", "prov_res": "", 
        "categoria": categoria, "gruppo": gruppo, "gruppo2": "", "scad_visita": "", 
        "allegato_visita": "", "allegato_privacy": "", "foto_atleta": "", "allegato_altro": "",
        "gen1": "", "tel1": "", "mail1": "", "gen2": "", "tel2": "", "mail2": "", 
        "n_rate": config_gruppo.get("n_rate", "1 Rata"), 
        "quota_tot": safe_float(config_gruppo.get("quota_tot", 500.0)), 
        "sconto": 0.0, "tot_scontato": 0.0, 
        "r1_imp": safe_float(config_gruppo.get("r1_imp", 500.0)), "r1_versato": safe_float(config_gruppo.get("r1_imp", 500.0)), "r1_data": "", 
        "r2_imp": safe_float(config_gruppo.get("r2_imp", 0.0)), "r2_versato": safe_float(config_gruppo.get("r2_imp", 0.0)), "r2_data": "", 
        "r3_imp": safe_float(config_gruppo.get("r3_imp", 0.0)), "r3_versato": safe_float(config_gruppo.get("r3_imp", 0.0)), "r3_data": "", 
        "r4_imp": safe_float(config_gruppo.get("r4_imp", 0.0)), "r4_versato": safe_float(config_gruppo.get("r4_imp", 0.0)), "r4_data": "", 
        "quota_versata": 0.0, "saldo_rimanente": 0.0, "rate_pagate_str": "0/1", "stato_rate": "🔴 INCOMPLETA", 
        "stato": "Confermato", "stagione": stagione_attiva, "storico_pagamenti": [],
        "valutazioni_tecniche": {}
    }
    for k, v in dati.items():
        if k in standard and v != "":
            standard[k] = str(v).strip() if isinstance(v, str) else v
    return ricalcola_finanze(standard)

MAPPING_COLONNE = {
    "cognome": "Cognome", "nome": "Nome", "sesso": "Genere", "cf": "Codice Fiscale",
    "data_nas": "Data Nascita", "luogo_nas": "Luogo Nascita", "prov_nas": "Prov. Nascita",
    "indirizzo_res": "Indirizzo Residenza", "citta_res": "Città Residenza", "prov_res": "Prov. Residenza",
    "categoria": "Categoria", "gruppo": "Gruppo Squadra", "gruppo2": "2° Gruppo", "scad_visita": "Scad. Visita", "stato_visita": "Stato Visita",
    "gen1": "Genitore 1", "tel1": "Tel. Gen 1", "mail1": "Mail Gen 1",
    "gen2": "Genitore 2", "tel2": "Tel. Gen 2", "mail2": "Mail Gen 2",
    "n_rate": "N° Rate", "quota_tot": "Quota Totale (€)", "sconto": "Sconto (%)",
    "tot_scontato": "Totale Scontato (€)", "rate_pagate_str": "Rate Pagate", 
    "r1_imp": "1ª Rata Prevista (€)", "r1_data": "Data 1ª Rata",
    "r2_imp": "2ª Rata Prevista (€)", "r2_data": "Data 2ª Rata", 
    "r3_imp": "3ª Rata Prevista (€)", "r3_data": "Data 3ª Rata",
    "r4_imp": "4ª Rata Prevista (€)", "r4_data": "Data 4ª Rata", 
    "quota_versata": "Quota Versata (€)", "saldo_rimanente": "Saldo Rimanente (€)", "stato_rate": "Stato Rate", "stato": "Stato Iscrizione", "stagione": "Stagione"
}

def sincronizza_dal_modulo(stagione_attiva):
    try:
        response = requests.get(URL_MASTER_CSV, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200: return f"❌ Errore connessione Google (HTTP: {response.status_code})"
        df = pd.read_csv(io.StringIO(response.text))
        col_map = {str(c).strip().lower(): c for c in df.columns}
        
        count_nuovi = 0
        for _, row in df.iterrows():
            c = str(row.get(col_map.get("cognome"), row.get(col_map.get("cognome atleta"), ""))).strip()
            n = str(row.get(col_map.get("nome"), row.get(col_map.get("nome atleta"), ""))).strip()
            if not c and not n:
                nc = str(row.get(col_map.get("nome e cognome"), row.get(col_map.get("nominativo"), ""))).strip()
                if nc and nc.lower() not in ["nan", "none"]:
                    parti = nc.split(" ", 1)
                    c = parti[0]
                    n = parti[1] if len(parti) > 1 else ""

            g_raw = str(row.get(col_map.get("categoria gruppo"), row.get(col_map.get("gruppo"), row.get(col_map.get("gruppo squadra"), row.get(col_map.get("categoria"), ""))))).strip()
            gruppo_letto = normalizza_nome_gruppo(g_raw)
            if not gruppo_letto: gruppo_letto = "Minivolley"

            if gruppo_letto not in st.session_state["gruppi_societa"]:
                st.session_state["gruppi_societa"].append(gruppo_letto)
                salva_json_sicuro(FILE_GRUPPI, st.session_state["gruppi_societa"])

            cf_letto = str(row.get(col_map.get("codice fiscale"), row.get(col_map.get("cf"), ""))).strip()
            
            if c and c.lower() not in ["nan", "none", ""]:
                gia_presente = any(str(a["cognome"]).lower() == c.lower() and str(a["nome"]).lower() == n.lower() and a.get("stagione") == stagione_attiva for a in st.session_state["elenco_atlete"])
                if not gia_presente:
                    nuova = crea_scheda_standard({
                        "cognome": c, "nome": n if n else "Senza Nome", 
                        "gruppo": gruppo_letto, "categoria": str(row.get(col_map.get("categoria"), row.get(col_map.get("categoria gruppo"), "Promozionale"))).strip(),
                        "cf": cf_letto if cf_letto.lower() not in ["nan", "none"] else "", 
                        "data_nas": str(row.get(col_map.get("data di nascita"), row.get(col_map.get("data nascita"), ""))).strip(),
                        "luogo_nas": str(row.get(col_map.get("luogo di nascita"), row.get(col_map.get("luogo nascita"), ""))).strip(),
                        "citta_res": str(row.get(col_map.get("città di residenza"), row.get(col_map.get("citta"), ""))).strip(),
                        "gen1": str(row.get(col_map.get("nome e cognome genitore 1"), row.get(col_map.get("genitore 1"), ""))).strip(), 
                        "tel1": str(row.get(col_map.get("telefono genitore 1"), row.get(col_map.get("tel gen 1"), ""))).strip(),
                        "mail1": str(row.get(col_map.get("email genitore 1"), row.get(col_map.get("mail gen 1"), ""))).strip(), 
                        "gen2": str(row.get(col_map.get("nome e cognome genitore 2"), row.get(col_map.get("genitore 2"), ""))).strip(), 
                        "tel2": str(row.get(col_map.get("telefono genitore 2"), row.get(col_map.get("tel gen 2"), ""))).strip(),
                        "mail2": str(row.get(col_map.get("email genitore 2"), row.get(col_map.get("mail gen 2"), ""))).strip(), 
                        "scad_visita": str(row.get(col_map.get("scadenza visita medica"), row.get(col_map.get("scadenza visita"), ""))).strip()
                    }, stagione_attiva=stagione_attiva)
                    st.session_state["elenco_atlete"].append(nuova)
                    count_nuovi += 1
        salva_atlete(st.session_state["elenco_atlete"])
        return f"✅ Sincronizzazione completata per la stagione {stagione_attiva} (Aggiunte {count_nuovi} schede)."
    except Exception as e: return f"❌ Errore: {e}"

def verifica_accesso(area_richiesta):
    user_corrente = st.session_state.get("username_corrente", "")
    info_u = st.session_state["utenti"].get(user_corrente, {})
    
    aree_utente = info_u.get("area", ["Area Amministratori"])
    if isinstance(aree_utente, str):
        aree_utente = [aree_utente]
        
    is_admin = "Amministratore" in str(st.session_state.get("ruolo_corrente", "")) or user_corrente == "admin"
    
    if not is_admin and "Tutte" not in aree_utente and area_richiesta not in aree_utente:
        st.error(f"⛔ Accesso negato: il tuo account non è autorizzato ad accedere a questa sezione ({area_richiesta}).")
        st.stop()

# --- LOGIN & ACCESSO (SCHERMATA PRINCIPALE) ---
if not st.session_state["utente_autenticato"]:
    st.markdown(f"<h1 style='text-align: center; color: #1f77b4;'>🏐 GESTIONALE {nome_societa.upper()}</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    col_vuota1, col_testo, col_pulsante, col_vuota2 = st.columns([1, 2, 1.5, 1])
    with col_testo:
        st.subheader("📝 Modulo di Iscrizione Online")
        st.write("Compila il modulo ufficiale cliccando a lato:")
    with col_pulsante:
        st.write("") 
        st.link_button("👉 VAI AL MODULO DI ISCRIZIONE", url=LINK_GOOGLE_FORM, use_container_width=True)
    
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #555; font-size: 15px;'><i>(Accesso al gestionale - solo personale autorizzato)</i></p>", unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([1, 2, 1])
    with col_login:
        with st.form("form_login"):
            username_input = st.text_input("Username:")
            password_input = st.text_input("Password:", type="password")
            if st.form_submit_button("Accedi all'Area Riservata", use_container_width=True):
                utenti = st.session_state["utenti"]
                u_clean = username_input.strip().lower()
                p_clean = password_input.strip()
                if u_clean in utenti and utenti[u_clean]["password"] == p_clean:
                    st.session_state["utente_autenticato"] = True
                    st.session_state["username_corrente"] = u_clean
                    st.session_state["ruolo_corrente"] = utenti[u_clean]["ruolo"]
                    
                    raw_area = utenti[u_clean].get("area", ["Area Amministratori"])
                    st.session_state["area_corrente"] = raw_area if isinstance(raw_area, list) else [raw_area]
                    st.rerun()
                else:
                    st.error("❌ Credenziali errate.")
    st.stop()

# --- SIDEBAR DI NAVIGAZIONE GLOBALE E SELETTORE STAGIONE ---
atlete_totali = st.session_state["elenco_atlete"]
stagioni_disponibili = sorted(list(set(a.get("stagione", "2026/2027") for a in atlete_totali)), reverse=True)
if "2026/2027" not in stagioni_disponibili: stagioni_disponibili.insert(0, "2026/2027")

try:
    default_season_idx = stagioni_disponibili.index("2026/2027")
except ValueError:
    default_season_idx = 0

with st.sidebar:
    st.markdown(f"### 🏐 {nome_societa}")
    ruolo_corr_display = st.session_state.get('ruolo_corrente', 'Admin')
    st.markdown(f'<div class="user-box">Utente: <b>{st.session_state.get("username_corrente")}</b><br>({ruolo_corr_display})</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    stagione_selezionata = st.selectbox("🗓️ Stagione Attiva:", stagioni_disponibili, index=default_season_idx)
    st.markdown("---")
    
    st.markdown("### 📌 Menu di Navigazione")
    pagina_scelta = st.radio("Vai a:", [
        "Home", 
        "Area Promozionale", 
        "Area Giovanile", 
        "Anagrafiche e Rate", 
        "Report Finanziario", 
        "Bilancio and Budget", 
        "Area Tecnica", 
        "Area Amministratori"
    ])
    
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["utente_autenticato"] = False
        st.rerun()

# --- HEADER COMUNE E ALLERTE ---
st.markdown("""
    <div class="legenda-container">
        <span><b>LEGENDA RATE:</b></span>
        <span class="badge-completa">🟢 COMPLETA (Saldo <= 0)</span>
        <span class="badge-incompleta">🔴 INCOMPLETA (Saldo > 0)</span>
        <span style="margin-left: 20px;"><b>ALLERTE VISITE MEDICHE:</b></span>
        <span style="color: #721c24;">🔴 SCADUTA</span>
        <span style="color: #856404;">🟡 IN SCADENZA (30 GG)</span>
    </div>
""", unsafe_allow_html=True)

atlete_stagione_attiva = [a for a in atlete_totali if a.get("stagione") == stagione_selezionata]
scadenze_critiche = []
for a in atlete_stagione_attiva:
    if a.get("cognome") == "--- Inizializzazione": continue
    stato = a.get("stato_visita", "")
    if "SCADUTA" in stato or "IN SCADENZA" in stato or "MANCANTE" in stato:
        scadenze_critiche.append(f"• **{stato}**: {a.get('cognome')} {a.get('nome')} ({a.get('gruppo')}) - Scadenza: {a.get('scad_visita', 'Mancante')}")
if scadenze_critiche:
    st.warning(f"⚠️ **Avviso Scadenze / Mancanza Visite Mediche (Stagione {stagione_selezionata}):**\n\n" + "\n".join(scadenze_critiche))

st.markdown("---")

is_admin_user = "Amministratore" in str(st.session_state.get("ruolo_corrente", "")) or st.session_state.get("username_corrente") == "admin"
info_utente_loggato = st.session_state["utenti"].get(st.session_state.get("username_corrente"), {})
aree_utente_correnti = info_utente_loggato.get("area", ["Area Amministratori"])
if isinstance(aree_utente_correnti, str): aree_utente_correnti = [aree_utente_correnti]

# --- ROUTING DELLE PAGINE TRAMITE SIDEBAR ---

if pagina_scelta == "Home":
    st.markdown(f"<h2 style='text-align: center; color: #1f77b4;'>🏐 BENVENUTO NEL GESTIONALE {nome_societa.upper()}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center; color: #555;'>Stagione Sportiva Attiva: {stagione_selezionata}</h4>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.info(f"👋 **Ciao! Benvenuto nel nuovo sistema di gestione societaria unificato per {nome_societa}.**\n\nDa questo pannello puoi gestire interamente l'anagrafica atleti, controllare le visite mediche, tenere traccia delle quote e dei pagamenti, amministrare i gruppi e consultare i bilanci.")
    st.write("👈 Usa il **Menu di Navigazione** sulla barra laterale a sinistra per muoverti all'interno del gestionale.")

elif pagina_scelta == "Area Promozionale":
    verifica_accesso("Promozionale")
    st.markdown(f"<h2 style='text-align: center;'>AREA PROMOZIONALE (Stagione {stagione_selezionata})</h2>", unsafe_allow_html=True)
    
    gruppi_prom = [g for g in st.session_state["gruppi_societa"] if g.lower() in ["minivolley", "scuola", "gruppi promozionali"] or "promo" in g.lower() or "mini" in g.lower() or "scuola" in g.lower() or (len(g) == 4 and g.isdigit())]
    if not gruppi_prom: gruppi_prom = ["Minivolley", "Scuola", "Gruppi Promozionali"]
    
    tab_gp = st.tabs(gruppi_prom)
    for i, g_nome in enumerate(gruppi_prom):
        with tab_gp[i]:
            st.subheader(f"Roster Gruppo: {g_nome}")
           
                
           # 1. Filtro atlete del gruppo
    atlete_g = [a for a in atleta_stagione_attiva if a.get("cognome") != "--- Inizializzazione" and (str(a.get("gruppo_squadra", "")).lower() == g_nome.lower() or str(a.get("gruppo", "")).lower() == g_nome.lower() or str(a.get("gruppo2", "")).lower() == g_nome.lower())]
    
    oggi = datetime.now().date()
    atlete_scadute = [a for a in atlete_g if str(a.get("scad_visa", "")).strip() and datetime.strptime(str(a.get("scad_visa", "")).strip(), "%d/%m/%Y").date() < oggi]
    atlete_in_scadenza = [a for a in atlete_g if str(a.get("scad_visa", "")).strip() and 0 <= (datetime.strptime(str(a.get("scad_visa", "")).strip(), "%d/%m/%Y").date() - oggi).days <= 30]

    # 2. Visite Scadute
    st.write(f"**Visite Scadute ({len(atlete_scadute)}):**")
    df_scad = pd.DataFrame(atlete_scadute)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📥 Scarica SCADUTE (.csv)", df_scad.to_csv(index=False), f"scadute_{g_nome}.csv", "text/csv", key=f"csv_scad_{g_nome}")
    with c2:
        st.download_button("📥 Scarica SCADUTE (.xlsx)", to_excel(df_scad), f"scadute_{g_nome}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"xlsx_scad_{g_nome}")
    st.dataframe(df_scad, use_container_width=True)

    # 3. In Scadenza nei prossimi 30gg
    st.write(f"**In Scadenza nei prossimi 30gg ({len(atlete_in_scadenza)}):**")
    df_prox = pd.DataFrame(atlete_in_scadenza)
    c3, c4 = st.columns(2)
    with c3:
        st.download_button("📥 Scarica IN SCADENZA (.csv)", df_prox.to_csv(index=False), f"in_scadenza_{g_nome}.csv", "text/csv", key=f"csv_prox_{g_nome}")
    with c4:
        st.download_button("📥 Scarica IN SCADENZA (.xlsx)", to_excel(df_prox), f"in_scadenza_{g_nome}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"xlsx_prox_{g_nome}")
    st.dataframe(df_prox, use_container_width=True)

    # 4. Filtri di ricerca
    col_rt1, col_rt2 = st.columns(2)
    with col_rt1:
        q_prom = st.text_input(f"🔍 Cerca per nome in {g_nome}:", key=f"q_prom_{g_nome}")
    with col_rt2:
        nomi_atlete_g = ["Tutti"] + [f"{a['cognome']} {a['nome']}" for a in atlete_g]
        sel_atleta_tendina = st.selectbox(f"Seleziona atleta a tendina ({g_nome}):", nomi_atlete_g, key=f"sel_tend_prom_{g_nome}")

    if sel_atleta_tendina != "Tutti":
        c_c, c_n = sel_atleta_tendina.split(" ", 1)
        atlete_g = [a for a in atlete_g if a.get("cognome") == c_c and a.get("nome") == c_n]
    elif q_prom:
        atlete_g = [a for a in atlete_g if q_prom.lower() in a.get("cognome", "").lower() or q_prom.lower() in a.get("nome", "").lower()]
                
            if atlete_g:
    df_g = pd.DataFrame(atlete_g)
    col_vis = [c for c in ["cognome", "nome", "sesso", "scad_visa", "stato_visita", "tel1", "mail1"] if c in df_g.columns]
    st.dataframe(df_g[col_vis].rename(columns=MAPPING_COLONNE), use_container_width=True)
                
                col_exp_p1, col_exp_p2 = st.columns(2)
                with col_exp_p1:
                    csv_exp_p = df_g[col_vis].rename(columns=MAPPING_COLONNE).to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button(f"📥 Esporta {g_nome} in CSV", data=csv_exp_p, file_name=f"roster_{g_nome}_{stagione_selezionata.replace('/','_')}.csv", mime="text/csv", key=f"dl_prom_csv_{i}")
                with col_exp_p2:
                    excel_io_p = io.BytesIO()
                    with pd.ExcelWriter(excel_io_p, engine='openpyxl') as writer:
                        df_g[col_vis].rename(columns=MAPPING_COLONNE).to_excel(writer, index=False, sheet_name='Roster')
                    st.download_button(f"📊 Esporta {g_nome} in Excel (.xlsx)", data=excel_io_p.getvalue(), file_name=f"roster_{g_nome}_{stagione_selezionata.replace('/','_')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"dl_prom_xlsx_{i}")

                st.markdown("---")
                atleta_da_canc = st.selectbox("Seleziona atleta da rimuovere o cancellare:", ["-- Seleziona --"] + [f"{a['cognome']} {a['nome']}" for a in atlete_g], key=f"del_prom_{i}")
                if atleta_da_canc != "-- Seleziona --":
                    if st.button(f"🗑️ Rimuovi/Cancella Atleta da {g_nome}", key=f"btn_del_p_{i}"):
                        c_cog, c_nom = atleta_da_canc.split(" ", 1)
                        st.session_state["elenco_atlete"] = [a for a in st.session_state["elenco_atlete"] if not (a.get("cognome") == c_cog and a.get("nome") == c_nom and a.get("stagione") == stagione_selezionata)]
                        salva_atlete(st.session_state["elenco_atlete"])
                        st.success(f"Atleta {atleta_da_canc} rimossa con successo!")
                        st.rerun()
                
                st.markdown("---")
                if st.button(f"🗑️ ELIMINA INTERO GRUPPO: {g_nome}", key=f"btn_del_gruppo_p_{i}"):
                    st.session_state["gruppi_societa"] = [gr for gr in st.session_state["gruppi_societa"] if gr.lower() != g_nome.lower()]
                    salva_json_sicuro(FILE_GRUPPI, st.session_state["gruppi_societa"])
                    
                    st.success(f"Gruppo {g_nome} eliminato con successo!")
                    st.rerun()
            else:
                st.info(f"Nessun iscritto trovato in questo gruppo per la stagione {stagione_selezionata}.")
                st.markdown("---")
                if st.button(f"🗑️ ELIMINA INTERO GRUPPO: {g_nome}", key=f"btn_del_gruppo_vuoto_p_{i}"):
                    st.session_state["gruppi_societa"] = [gr for gr in st.session_state["gruppi_societa"] if gr.lower() != g_nome.lower()]
                    salva_json_sicuro(FILE_GRUPPI, st.session_state["gruppi_societa"])
		    
                    st.success(f"Gruppo {g_nome} eliminato con successo!")
                    st.rerun()

elif pagina_scelta == "Area Giovanile":
    verifica_accesso("Giovanile")
    st.markdown(f"<h2 style='text-align: center;'>AREA GIOVANILE & SENIOR (Stagione {stagione_selezionata})</h2>", unsafe_allow_html=True)
    
    gruppi_giov = [g for g in st.session_state["gruppi_societa"] if g not in [gp for gp in st.session_state["gruppi_societa"] if gp.lower() in ["minivolley", "scuola", "gruppi promozionali"] or (len(gp) == 4 and gp.isdigit())]]
    if not gruppi_giov: gruppi_giov = ["Under 14", "Under 16", "Under 18", "Serie C", "Serie D"]
    
    tab_gg = st.tabs(gruppi_giov)
    for i, g_nome in enumerate(gruppi_giov):
        with tab_gg[i]:
            st.subheader(f"Roster Squadra / Gruppo: {g_nome}")
            atlete_g = [a for a in atlete_stagione_attiva if a.get("cognome") != "--- Inizializzazione" and (a.get("gruppo", "").lower() == g_nome.lower() or a.get("gruppo2", "").lower() == g_nome.lower())]
            
            col_gt1, col_gt2 = st.columns(2)
            with col_gt1:
                q_giov = st.text_input(f"🔍 Cerca per nome in {g_nome}:", key=f"q_giov_{i}")
            with col_gt2:
                nomi_atlete_gg = ["Tutti"] + [f"{a['cognome']} {a['nome']}" for a in atlete_g]
                sel_atleta_tend_g = st.selectbox(f"Seleziona atleta a tendina ({g_nome}):", nomi_atlete_gg, key=f"sel_tend_giov_{i}")
            
            if sel_atleta_tend_g != "Tutti":
                c_c, c_n = sel_atleta_tend_g.split(" ", 1)
                atlete_g = [a for a in atlete_g if a.get("cognome") == c_c and a.get("nome") == c_n]
            elif q_giov:
                atlete_g = [a for a in atlete_g if q_giov.lower() in a.get("cognome","").lower() or q_giov.lower() in a.get("nome","").lower()]
                
            if atlete_g:
                df_g = pd.DataFrame(atlete_g)
                col_vis = [c for c in ["cognome", "nome", "sesso", "scad_visita", "stato_visita", "tel1", "mail1", "rate_pagate_str", "stato_rate"] if c in df_g.columns]
                st.dataframe(df_g[col_vis].rename(columns=MAPPING_COLONNE), use_container_width=True)
                
                col_exp_g1, col_exp_g2 = st.columns(2)
                with col_exp_g1:
                    csv_exp_g = df_g[col_vis].rename(columns=MAPPING_COLONNE).to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button(f"📥 Esporta {g_nome} in CSV", data=csv_exp_g, file_name=f"roster_{g_nome}_{stagione_selezionata.replace('/','_')}.csv", mime="text/csv", key=f"dl_giov_csv_{i}")
                with col_exp_g2:
                    excel_io_g = io.BytesIO()
                    with pd.ExcelWriter(excel_io_g, engine='openpyxl') as writer:
                        df_g[col_vis].rename(columns=MAPPING_COLONNE).to_excel(writer, index=False, sheet_name='Roster')
                    st.download_button(f"📊 Esporta {g_nome} in Excel (.xlsx)", data=excel_io_g.getvalue(), file_name=f"roster_{g_nome}_{stagione_selezionata.replace('/','_')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"dl_giov_xlsx_{i}")

                st.markdown("---")
                atleta_da_canc_g = st.selectbox("Seleziona atleta da rimuovere o cancellare:", ["-- Seleziona --"] + [f"{a['cognome']} {a['nome']}" for a in atlete_g], key=f"del_giov_{i}")
                if atleta_da_canc_g != "-- Seleziona --":
                    if st.button(f"🗑️ Rimuovi/Cancella Atleta da {g_nome}", key=f"btn_del_g_{i}"):
                        c_cog, c_nom = atleta_da_canc_g.split(" ", 1)
                        st.session_state["elenco_atlete"] = [a for a in st.session_state["elenco_atlete"] if not (a.get("cognome") == c_cog and a.get("nome") == c_nom and a.get("stagione") == stagione_selezionata)]
                        salva_atlete(st.session_state["elenco_atlete"])
                        st.success(f"Atleta {atleta_da_canc_g} rimossa con successo!")
                        st.rerun()

                st.markdown("---")
                if st.button(f"🗑️ ELIMINA INTERO GRUPPO: {g_nome}", key=f"btn_del_gruppo_g_{i}"):
                    st.session_state["gruppi_societa"] = [gr for gr in st.session_state["gruppi_societa"] if gr.lower() != g_nome.lower()]
                    salva_json_sicuro(FILE_GRUPPI, st.session_state["gruppi_societa"])
                    st.success(f"Gruppo {g_nome} eliminato con successo!")
                    st.rerun()
            else:
                st.info(f"Nessun iscritto in questo gruppo per la stagione {stagione_selezionata}.")
                st.markdown("---")
                if st.button(f"🗑️ ELIMINA INTERO GRUPPO: {g_nome}", key=f"btn_del_gruppo_vuoto_g_{i}"):
                    st.session_state["gruppi_societa"] = [gr for gr in st.session_state["gruppi_societa"] if gr.lower() != g_nome.lower()]
                    salva_json_sicuro(FILE_GRUPPI, st.session_state["gruppi_societa"])
                    st.success(f"Gruppo {g_nome} eliminato con successo!")
                    st.rerun()

elif pagina_scelta == "Anagrafiche e Rate":
    verifica_accesso("Gestionale")
    st.markdown(f"<h2 style='text-align: center;'>👥 ANAGRAFICA ISCRITTO/A, GENITORI E RATE (Stagione {stagione_selezionata})</h2>", unsafe_allow_html=True)
    
    with st.expander("🔄 Sincronizzazione Dati e Visualizzazione Google Sheets Master"):
        st.write("Collega, sincronizza o consulta direttamente il foglio Google Sheets ufficiale.")
        if st.button("Avvia Sincronizzazione Cloud Master"):
            risultato_sync = sincronizza_dal_modulo(stagione_selezionata)
            st.success(risultato_sync) 	
            time.sleep(2)
            st.rerun()
        
        st.markdown("---")
        st.markdown("#### 📄 Visualizzazione in tempo reale del Foglio Google Master:")
        st.components.v1.iframe(LINK_GOOGLE_SHEETS_EMBED, height=500, scrolling=True)

    tab_ins, tab_mod, tab_tabella, tab_ricevute = st.tabs(["➕ Inserisci Iscritto/a", "✏️ Modifica Iscritto/a", "📋 Tabella & Ricerca", "🧾 Ricevute e Storico Pagamenti"])

    with tab_ins:
        with st.form("form_inserimento_completo"):
            cognome = st.text_input("Cognome:")
            nome = st.text_input("Nome:")
            col1, col2, col3 = st.columns(3)
            with col1: sesso = st.selectbox("Sesso (M/F):", ["M", "F"], key="s_ins")
            with col2: cf = st.text_input("Codice Fiscale:", key="cf_ins")
            with col3: data_nas = st.text_input("Data Nas (GG/MM/AAAA):", key="dn_ins")
            col4, col5, col6 = st.columns(3)
            with col4: luogo_nas = st.text_input("Luogo di Nascita:", key="ln_ins")
            with col5: prov_nas = st.text_input("Provincia Nascita:", key="pn_ins")
            with col6: indirizzo_res = st.text_input("Indirizzo di Residenza:", key="ir_ins")
            col7, col8, col9 = st.columns(3)
            with col7: citta_res = st.text_input("Città di Residenza:", key="cr_ins")
            with col8: prov_res = st.text_input("Provincia Residenza:", key="pr_res")
            with col9: categoria = st.selectbox("Categoria:", st.session_state["categorie_societa"], key="cat_ins")
            
            col10, col11, col12 = st.columns(3)
            with col10: gruppo = st.selectbox("Gruppo Squadra / Anno Principale:", st.session_state["gruppi_societa"], key="g_ins")
            with col11: gruppo2 = st.selectbox("2° Gruppo / Squadra (Opzionale):", ["Nessuno"] + st.session_state["gruppi_societa"], key="g2_ins")
            with col12: scad_visita = st.text_input("Scad. Visita (GG/MM/AAAA):", key="sv_ins")
            
            st.markdown("---")
            c_gen1, c_gen2 = st.columns(2)
            with c_gen1:
                gen1 = st.text_input("Genitore 1 (Cognome e Nome):", key="g1_ins")
                tel1 = st.text_input("Tel. Gen 1:", key="t1_ins")
                mail1 = st.text_input("Mail Gen 1:", key="m1_ins")
            with c_gen2:
                gen2 = st.text_input("Genitore 2 (Cognome e Nome):", key="g2_in")
                tel2 = st.text_input("Tel. Gen 2:", key="t2_ins")
                mail2 = st.text_input("Mail Gen 2:", key="m2_ins")
            st.markdown("---")
            
            st.subheader("💳 Gestione Rate, Importi e Date di Pagamento")
            
            cfg_q_dict = st.session_state.get("config_quote", {})
            cfg_gruppo_corrente = cfg_q_dict.get(gruppo, {
                "n_rate": "1 Rata", "quota_tot": 500.0,
                "r1_imp": 500.0, "r2_imp": 0.0, "r3_imp": 0.0, "r4_imp": 0.0,
                "r1_data": "", "r2_data": "", "r3_data": "", "r4_data": ""
            })
            
            lista_n_rate_opts = ["1 Rata", "2 Rate", "3 Rate", "4 Rate"]
            default_n_rate_str = cfg_gruppo_corrente.get("n_rate", "1 Rata")
            idx_n_rate_def = lista_n_rate_opts.index(default_n_rate_str) if default_n_rate_str in lista_n_rate_opts else 0

            col_rq1, col_rq2, col_rq3 = st.columns(3)
            with col_rq1: n_rate_ins = st.selectbox("N° Rate:", lista_n_rate_opts, index=idx_n_rate_def, key="n_rate_ins")
            with col_rq2: quota_tot_ins = st.number_input("Quota Totale Prevista (€):", value=safe_float(cfg_gruppo_corrente.get("quota_tot", 500.0)), step=10.0, key="quota_tot_ins")
            with col_rq3: sconto_ins = st.number_input("Sconto (%):", value=0.0, step=1.0, key="sconto_ins")
            
            r1_standard = safe_float(cfg_gruppo_corrente.get('r1_imp', 0))
            importo_sconto = r1_standard * (sconto_ins / 100.0)
            r1_scontata = max(0.0, r1_standard - importo_sconto)
            r2_scontata = safe_float(cfg_gruppo_corrente.get('r2_imp', 0))
            r3_scontata = safe_float(cfg_gruppo_corrente.get('r3_imp', 0))
            r4_scontata = safe_float(cfg_gruppo_corrente.get('r4_imp', 0))

            st.markdown(f"**🔵 Configurazione Standard Gruppo ({gruppo}):**", unsafe_allow_html=True)
            st.markdown(f"""
                <div class="rate-grid-container">
                    <div class="rata-card">
                        <div class="rata-card-title">1ª Rata</div>
                        <div class="rata-card-val">€ {r1_scontata:,.2f}</div>
                        <div class="rata-card-data">{cfg_gruppo_corrente.get('r1_data', 'N/D')}</div>
                    </div>
                    <div class="rata-card">
                        <div class="rata-card-title">2ª Rata</div>
                        <div class="rata-card-val">€ {r2_scontata:,.2f}</div>
                        <div class="rata-card-data">{cfg_gruppo_corrente.get('r2_data', 'N/D')}</div>
                    </div>
                    <div class="rata-card">
                        <div class="rata-card-title">3ª Rata</div>
                        <div class="rata-card-val">€ {r3_scontata:,.2f}</div>
                        <div class="rata-card-data">{cfg_gruppo_corrente.get('r3_data', 'N/D')}</div>
                    </div>
                    <div class="rata-card">
                        <div class="rata-card-title">4ª Rata</div>
                        <div class="rata-card-val">€ {r4_scontata:,.2f}</div>
                        <div class="rata-card-data">{cfg_gruppo_corrente.get('r4_data', 'N/D')}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            st.write("✏️ **Spazi Editabili Personali dell'Atleta:**")
            c_s1, c_s2, c_s3, c_s4 = st.columns(4)
            with c_s1:
                r1_imp_ins = st.number_input("1ª Rata (€):", value=r1_scontata, key="r1_imp_ins")
                r1_data_ins = st.text_input("Data Effettiva 1ª Rata (GG/MM/AAAA):", value=str(cfg_gruppo_corrente.get("r1_data", "")), key="r1_data_ins")
            with c_s2:
                r2_imp_ins = st.number_input("2ª Rata (€):", value=r2_scontata, key="r2_imp_ins")
                r2_data_ins = st.text_input("Data Effettiva 2ª Rata (GG/MM/AAAA):", value=str(cfg_gruppo_corrente.get("r2_data", "")), key="r2_data_ins")
            with c_s3:
                r3_imp_ins = st.number_input("3ª Rata (€):", value=r3_scontata, key="r3_imp_ins")
                r3_data_ins = st.text_input("Data Effettiva 3ª Rata (GG/MM/AAAA):", value=str(cfg_gruppo_corrente.get("r3_data", "")), key="r3_data_ins")
            with c_s4:
                r4_imp_ins = st.number_input("4ª Rata (€):", value=r4_scontata, key="r4_imp_ins")
                r4_data_ins = st.text_input("Data Effettiva 4ª Rata (GG/MM/AAAA):", value=str(cfg_gruppo_corrente.get("r4_data", "")), key="r4_data_ins")

            st.markdown("---")
            file_visita_up = st.file_uploader("Certificato Visita Medica", type=["pdf", "png", "jpg", "jpeg"], key="f_vis_ins")
            file_privacy_up = st.file_uploader("Modulo Privacy Firmato", type=["pdf", "png", "jpg", "jpeg"], key="f_priv_ins")
            foto_atleta_up = st.file_uploader("Allega Foto Tessera Atleta", type=["png", "jpg", "jpeg"], key="f_foto_ins")
            file_altro_up = st.file_uploader("Allega Altro Documento", type=["pdf", "png", "jpg", "jpeg", "doc", "docx"], key="f_altro_ins")
            
            if st.form_submit_button("SALVA / AGGIUNGI ISCRITTO"):
                if cognome and nome:
                    path_v, path_p, path_f, path_a = "", "", "", ""
                    if file_visita_up:
                        path_v = os.path.join(CARTELLA_ALLEGATI, f"{cognome}_{nome}_visita_{file_visita_up.name}")
                        with open(path_v, "wb") as f: f.write(file_visita_up.getbuffer())
                    if file_privacy_up:
                        path_p = os.path.join(CARTELLA_ALLEGATI, f"{cognome}_{nome}_privacy_{file_privacy_up.name}")
                        with open(path_p, "wb") as f: f.write(file_privacy_up.getbuffer())
                    if foto_atleta_up:
                        path_f = os.path.join(CARTELLA_ALLEGATI, f"{cognome}_{nome}_foto_{foto_atleta_up.name}")
                        with open(path_f, "wb") as f: f.write(foto_atleta_up.getbuffer())
                    if file_altro_up:
                        path_a = os.path.join(CARTELLA_ALLEGATI, f"{cognome}_{nome}_altro_{file_altro_up.name}")
                        with open(path_a, "wb") as f: f.write(file_altro_up.getbuffer())
                        
                    nuova_scheda = crea_scheda_standard({
                        "cognome": cognome, "nome": nome, "sesso": sesso, "Codice Fiscale": cf, "data_nas": data_nas,
                        "luogo_nas": luogo_nas, "prov_nas": prov_nas, "indirizzo_res": indirizzo_res, "citta_res": citta_res,
                        "prov_res": prov_res, "categoria": categoria, "gruppo": normalizza_nome_gruppo(gruppo), "gruppo2": normalizza_nome_gruppo(gruppo2) if gruppo2 != "Nessuno" else "",
                        "scad_visita": scad_visita, "allegato_visita": path_v, "allegato_privacy": path_p, "foto_atleta": path_f, "allegato_altro": path_a,
                        "gen1": gen1, "tel1": tel1, "mail1": mail1, "gen2": gen2, "tel2": tel2, "mail2": mail2,
                        "n_rate": n_rate_ins, "quota_tot": quota_tot_ins, "sconto": sconto_ins,
                        "r1_imp": r1_imp_ins, "r1_versato": r1_imp_ins, "r1_data": r1_data_ins.strip(),
                        "r2_imp": r2_imp_ins, "r2_versato": r2_imp_ins, "r2_data": r2_data_ins.strip(),
                        "r3_imp": r3_imp_ins, "r3_versato": r3_imp_ins, "r3_data": r3_data_ins.strip(),
                        "r4_imp": r4_imp_ins, "r4_versato": r4_imp_ins, "r4_data": r4_data_ins.strip(),
                        "stato": "Confermato"
                    }, stagione_attiva=stagione_selezionata)
                    st.session_state["elenco_atlete"].append(nuova_scheda)
                    salva_atlete(st.session_state["elenco_atlete"])
                    st.success(f"✅ Iscritto/a {cognome} {nome} aggiunto/a con successo!")
                else: st.error("⚠️ Inserisci almeno Cognome e Nome.")

    with tab_mod:
        st.subheader("Modifica Dati Atleta, Rate, Sconti, Allegati e Storico Pagamenti")
        atlete_mod_filtrate = [a for a in st.session_state["elenco_atlete"] if a.get("stagione") == stagione_selezionata and a.get("cognome") != "--- Inizializzazione"]
        if not atlete_mod_filtrate:
            st.info("Nessuna atleta registrata per la stagione.")
        else:
            mappa_indici = {f"{a['cognome']} {a['nome']} ({a['gruppo']})": a for a in atlete_mod_filtrate}
            
            scelta_nome = st.selectbox("Seleziona atleta da modificare:", list(mappa_indici.keys()), key="selectbox_modifica_atleta")
            atleta_corr = mappa_indici[scelta_nome]
            
            form_key_suffix = f"{atleta_corr.get('cognome')}_{atleta_corr.get('nome')}_{atleta_corr.get('gruppo')}".replace(" ", "_")

            with st.form(f"form_mod_{form_key_suffix}"):
                m_cognome = st.text_input("Cognome:", value=atleta_corr.get("cognome", ""), key=f"m_cog_{form_key_suffix}")
                m_nome = st.text_input("Nome:", value=atleta_corr.get("nome", ""), key=f"m_nom_{form_key_suffix}")
                
                gruppi_disponibili_mod = st.session_state["gruppi_societa"]
                gruppo_corrente_atl = atleta_corr.get("gruppo", "Minivolley")
                idx_gruppo_mod = gruppi_disponibili_mod.index(gruppo_corrente_atl) if gruppo_corrente_atl in gruppi_disponibili_mod else 0
                m_gruppo = st.selectbox("Gruppo Squadra / Anno Principale:", gruppi_disponibili_mod, index=idx_gruppo_mod, key=f"m_gruppo_{form_key_suffix}")

                m_cf = st.text_input("Codice Fiscale:", value=atleta_corr.get("cf", ""), key=f"m_cf_{form_key_suffix}")
                m_data_nas = st.text_input("Data Nascita (GG/MM/AAAA):", value=atleta_corr.get("data_nas", ""), key=f"m_dn_{form_key_suffix}")
                m_luogo_nas = st.text_input("Luogo Nascita:", value=atleta_corr.get("luogo_nas", ""), key=f"m_ln_{form_key_suffix}")
                m_citta_res = st.text_input("Città Residenza:", value=atleta_corr.get("citta_res", ""), key=f"m_cr_{form_key_suffix}")
                m_scad_visita = st.text_input("Scadenza Visita Medica:", value=atleta_corr.get("scad_visita", ""), key=f"m_sv_{form_key_suffix}")
                
                st.markdown("---")
                st.subheader("👥 Genitori e Contatti")
                m_gen1 = st.text_input("Genitore 1:", value=atleta_corr.get("gen1", ""), key=f"m_g1_{form_key_suffix}")
                m_tel1 = st.text_input("Tel Gen 1:", value=atleta_corr.get("tel1", ""), key=f"m_t1_{form_key_suffix}")
                m_mail1 = st.text_input("Mail Gen 1:", value=atleta_corr.get("mail1", ""), key=f"m_m1_{form_key_suffix}")
                m_gen2 = st.text_input("Genitore 2:", value=atleta_corr.get("gen2", ""), key=f"m_g2_{form_key_suffix}")
                m_tel2 = st.text_input("Tel Gen 2:", value=atleta_corr.get("tel2", ""), key=f"m_t2_{form_key_suffix}")
                m_mail2 = st.text_input("Mail Gen 2:", value=atleta_corr.get("mail2", ""), key=f"m_m2_{form_key_suffix}")

                st.markdown("---")
                st.subheader("💳 Gestione Rate, Importi e Date di Pagamento")
                
                cfg_q_dict = st.session_state.get("config_quote", {})
                cfg_gruppo_atleta = cfg_q_dict.get(m_gruppo, {
                    "n_rate": "1 Rata", "quota_tot": 500.0,
                    "r1_imp": 500.0, "r1_data": "", "r2_imp": 0.0, "r2_data": "",
                    "r3_imp": 0.0, "r3_data": "", "r4_imp": 0.0, "r4_data": ""
                })

                lista_n_rate = ["1 Rata", "2 Rate", "3 Rate", "4 Rate"]
                default_nr_mod = cfg_gruppo_atleta.get("n_rate", atleta_corr.get("n_rate", "1 Rata"))
                idx_nr = lista_n_rate.index(default_nr_mod) if default_nr_mod in lista_n_rate else 0
                
                col_mr1, col_mr2, col_mr3 = st.columns(3)
                with col_mr1: m_n_rate = st.selectbox("N° Rate:", lista_n_rate, index=idx_nr, key=f"m_nr_{form_key_suffix}")
                with col_mr2: m_quota_tot = st.number_input("Quota Totale (€):", value=safe_float(cfg_gruppo_atleta.get("quota_tot", atleta_corr.get("quota_tot", 500))), key=f"m_qt_{form_key_suffix}")
                with col_mr3: m_sconto = st.number_input("Sconto (%):", value=safe_float(atleta_corr.get("sconto", 0)), key=f"m_sc_{form_key_suffix}")

                r1_standard_mod = safe_float(cfg_gruppo_atleta.get('r1_imp', 0))
                importo_sconto_mod = r1_standard_mod * (m_sconto / 100.0)
                r1_scontata_mod = max(0.0, r1_standard_mod - importo_sconto_mod)
                r2_scontata_mod = safe_float(cfg_gruppo_atleta.get('r2_imp', 0))
                r3_scontata_mod = safe_float(cfg_gruppo_atleta.get('r3_imp', 0))
                r4_scontata_mod = safe_float(cfg_gruppo_atleta.get('r4_imp', 0))

                st.markdown(f"**🔵 Configurazione Standard Gruppo ({m_gruppo}):**", unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="rate-grid-container">
                        <div class="rata-card">
                            <div class="rata-card-title">1ª Rata</div>
                            <div class="rata-card-val">€ {r1_scontata_mod:,.2f}</div>
                            <div class="rata-card-data">{cfg_gruppo_atleta.get('r1_data', 'N/D')}</div>
                        </div>
                        <div class="rata-card">
                            <div class="rata-card-title">2ª Rata</div>
                            <div class="rata-card-val">€ {r2_scontata_mod:,.2f}</div>
                            <div class="rata-card-data">{cfg_gruppo_atleta.get('r2_data', 'N/D')}</div>
                        </div>
                        <div class="rata-card">
                            <div class="rata-card-title">3ª Rata</div>
                            <div class="rata-card-val">€ {r3_scontata_mod:,.2f}</div>
                            <div class="rata-card-data">{cfg_gruppo_atleta.get('r3_data', 'N/D')}</div>
                        </div>
                        <div class="rata-card">
                            <div class="rata-card-title">4ª Rata</div>
                            <div class="rata-card-val">€ {r4_scontata_mod:,.2f}</div>
                            <div class="rata-card-data">{cfg_gruppo_atleta.get('r4_data', 'N/D')}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                st.write("✏️ **Spazi Editabili Personali dell'Atleta:**")
                col_mp1, col_mp2, col_mp3, col_mp4 = st.columns(4)
                with col_mp1:
                    val_r1_init = safe_float(atleta_corr.get("r1_imp", r1_scontata_mod))
                    m_r1_i = st.number_input("1ª Rata (€):", value=val_r1_init, key=f"m_r1i_{form_key_suffix}")
                    m_r1_d = st.text_input("Data Effettiva 1ª Rata:", value=str(atleta_corr.get("r1_data", cfg_gruppo_atleta.get("r1_data", ""))), key=f"m_r1d_{form_key_suffix}")
                with col_mp2:
                    val_r2_init = safe_float(atleta_corr.get("r2_imp", r2_scontata_mod))
                    m_r2_i = st.number_input("2ª Rata (€):", value=val_r2_init, key=f"m_r2i_{form_key_suffix}")
                    m_r2_d = st.text_input("Data Effettiva 2ª Rata:", value=str(atleta_corr.get("r2_data", cfg_gruppo_atleta.get("r2_data", ""))), key=f"m_r2d_{form_key_suffix}")
                with col_mp3:
                    val_r3_init = safe_float(atleta_corr.get("r3_imp", r3_scontata_mod))
                    m_r3_i = st.number_input("3ª Rata (€):", value=val_r3_init, key=f"m_r3i_{form_key_suffix}")
                    m_r3_d = st.text_input("Data Effettiva 3ª Rata:", value=str(atleta_corr.get("r3_data", cfg_gruppo_atleta.get("r3_data", ""))), key=f"m_r3d_{form_key_suffix}")
                with col_mp4:
                    val_r4_init = safe_float(atleta_corr.get("r4_imp", r4_scontata_mod))
                    m_r4_i = st.number_input("4ª Rata (€):", value=val_r4_init, key=f"m_r4i_{form_key_suffix}")
                    m_r4_d = st.text_input("Data Effettiva 4ª Rata:", value=str(atleta_corr.get("r4_data", cfg_gruppo_atleta.get("r4_data", ""))), key=f"m_r4d_{form_key_suffix}")

                if st.form_submit_button("Salva Modifiche Generali e Rate"):
                    atleta_corr["cognome"] = m_cognome.strip()
                    atleta_corr["nome"] = m_nome.strip()
                    atleta_corr["gruppo"] = normalizza_nome_gruppo(m_gruppo)
                    atleta_corr["cf"] = m_cf.strip()
                    atleta_corr["data_nas"] = m_data_nas.strip()
                    atleta_corr["luogo_nas"] = m_luogo_nas.strip()
                    atleta_corr["citta_res"] = m_citta_res.strip()
                    atleta_corr["scad_visita"] = m_scad_visita.strip()
                    atleta_corr["gen1"] = m_gen1.strip()
                    atleta_corr["tel1"] = m_tel1.strip()
                    atleta_corr["mail1"] = m_mail1.strip()
                    atleta_corr["gen2"] = m_gen2.strip()
                    atleta_corr["tel2"] = m_tel2.strip()
                    atleta_corr["mail2"] = m_mail2.strip()
                    atleta_corr["n_rate"] = m_n_rate
                    atleta_corr["quota_tot"] = m_quota_tot
                    atleta_corr["sconto"] = m_sconto
                    atleta_corr["r1_imp"] = m_r1_i
                    atleta_corr["r1_versato"] = m_r1_i
                    atleta_corr["r1_data"] = m_r1_d.strip()
                    atleta_corr["r2_imp"] = m_r2_i
                    atleta_corr["r2_versato"] = m_r2_i
                    atleta_corr["r2_data"] = m_r2_d.strip()
                    atleta_corr["r3_imp"] = m_r3_i
                    atleta_corr["r3_versato"] = m_r3_i
                    atleta_corr["r3_data"] = m_r3_d.strip()
                    atleta_corr["r4_imp"] = m_r4_i
                    atleta_corr["r4_versato"] = m_r4_i
                    atleta_corr["r4_data"] = m_r4_d.strip()
                    ricalcola_finanze(atleta_corr)
                    salva_atlete(st.session_state["elenco_atlete"])
                    st.success("✅ Modifiche salvate con successo!")

            st.markdown("---")
            st.subheader("📎 Gestione e Upload Allegati (Visita, Privacy, Foto, Altro)")
            c_al1, c_al2 = st.columns(2)
            with c_al1:
                st.write(f"Certificato Visita: {'✅ Presente' if atleta_corr.get('allegato_visita') else '❌ Mancante'}")
                f_v_mod = st.file_uploader("Aggiorna Visita Medica", type=["pdf", "png", "jpg"], key=f"f_v_m_{form_key_suffix}")
                if f_v_mod:
                    p_vm = os.path.join(CARTELLA_ALLEGATI, f"{atleta_corr.get('cognome')}_{atleta_corr.get('nome')}_visita_{f_v_mod.name}")
                    with open(p_vm, "wb") as f: f.write(f_v_mod.getbuffer())
                    atleta_corr["allegato_visita"] = p_vm
                    salva_atlete(st.session_state["elenco_atlete"])
                    st.success("Visita aggiornata!")

                st.write(f"Foto Tessera: {'✅ Presente' if atleta_corr.get('foto_atleta') else '❌ Mancante'}")
                f_foto_mod = st.file_uploader("Aggiorna Foto Tessera", type=["png", "jpg", "jpeg"], key=f"f_foto_m_{form_key_suffix}")
                if f_foto_mod:
                    p_fm = os.path.join(CARTELLA_ALLEGATI, f"{atleta_corr.get('cognome')}_{atleta_corr.get('nome')}_foto_{f_foto_mod.name}")
                    with open(p_fm, "wb") as f: f.write(f_foto_mod.getbuffer())
                    atleta_corr["foto_atleta"] = p_fm
                    salva_atlete(st.session_state["elenco_atlete"])
                    st.success("Foto aggiornata!")

            with c_al2:
                st.write(f"Privacy: {'✅ Presente' if atleta_corr.get('allegato_privacy') else '❌ Mancante'}")
                f_p_mod = st.file_uploader("Aggiorna Privacy", type=["pdf", "png", "jpg"], key=f"f_p_m_{form_key_suffix}")
                if f_p_mod:
                    p_pm = os.path.join(CARTELLA_ALLEGATI, f"{atleta_corr.get('cognome')}_{atleta_corr.get('nome')}_privacy_{f_p_mod.name}")
                    with open(p_pm, "wb") as f: f.write(f_p_mod.getbuffer())
                    atleta_corr["allegato_privacy"] = p_pm
                    salva_atlete(st.session_state["elenco_atlete"])
                    st.success("Privacy aggiornata!")

                st.write(f"Altro Documento: {'✅ Presente' if atleta_corr.get('allegato_altro') else '❌ Mancante'}")
                f_altro_mod = st.file_uploader("Aggiorna Altro Documento", type=["pdf", "png", "jpg", "doc"], key=f"f_altro_m_{form_key_suffix}")
                if f_altro_mod:
                    p_am = os.path.join(CARTELLA_ALLEGATI, f"{atleta_corr.get('cognome')}_{atleta_corr.get('nome')}_altro_{f_altro_mod.name}")
                    with open(p_am, "wb") as f: f.write(f_altro_mod.getbuffer())
                    atleta_corr["allegato_altro"] = p_am
                    salva_atlete(st.session_state["elenco_atlete"])
                    st.success("Documento aggiornato!")

    with tab_tabella:
        st.subheader("Tabella Generale Iscritti, Ricerca ed Export Excel/CSV")
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            testo_ricerca = st.text_input("🔍 Cerca per Cognome o Nome:")
        with col_f2:
            gruppi_filtro_opt = ["Tutti"] + st.session_state["gruppi_societa"]
            gruppo_selezionato_f = st.selectbox("Filtra per Gruppo:", gruppi_filtro_opt)
        with col_f3:
            atlete_tabella_base = [a for a in st.session_state["elenco_atlete"] if a.get("stagione") == stagione_selezionata and a.get("cognome") != "--- Inizializzazione"]
            tendina_atleti_opt = ["Tutti"] + [f"{a['cognome']} {a['nome']}" for a in atlete_tabella_base]
            atleta_tendina_scelta = st.selectbox("Seleziona atleta a tendina:", tendina_atleti_opt)

        atlete_tabella = atlete_tabella_base
        if atleta_tendina_scelta != "Tutti":
            c_tc, c_tn = atleta_tendina_scelta.split(" ", 1)
            atlete_tabella = [a for a in atlete_tabella if a.get("cognome") == c_tc and a.get("nome") == c_tn]
        else:
            if gruppo_selezionato_f != "Tutti":
                atlete_tabella = [a for a in atlete_tabella if a.get("gruppo", "").lower() == gruppo_selezionato_f.lower() or a.get("gruppo2", "").lower() == gruppo_selezionato_f.lower()]
            if testo_ricerca:
                atlete_tabella = [a for a in atlete_tabella if testo_ricerca.lower() in a.get("cognome","").lower() or testo_ricerca.lower() in a.get("nome","").lower()]

        if atlete_tabella:
            df_tab = pd.DataFrame(atlete_tabella)
            colonne_presenti = [c for c in MAPPING_COLONNE.keys() if c in df_tab.columns]
            st.dataframe(df_tab[colonne_presenti].rename(columns=MAPPING_COLONNE), use_container_width=True)
            
            c_ex1, c_ex2 = st.columns(2)
            with c_ex1:
                csv_data = df_tab[colonne_presenti].rename(columns=MAPPING_COLONNE).to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 Scarica in formato CSV", data=csv_data, file_name=f"iscritti_{stagione_selezionata.replace('/','_')}.csv", mime="text/csv")
            with c_ex2:
                excel_io = io.BytesIO()
                with pd.ExcelWriter(excel_io, engine='openpyxl') as writer:
                    df_tab[colonne_presenti].rename(columns=MAPPING_COLONNE).to_excel(writer, index=False, sheet_name='Iscritti')
                st.download_button("📊 Scarica in formato Excel (.xlsx)", data=excel_io.getvalue(), file_name=f"iscritti_{stagione_selezionata.replace('/','_')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("Nessuna atleta trovata con i filtri selezionati.")

    with tab_ricevute:
        st.subheader("🧾 Storico Finanziario e Emissione Ricevute PDF")
        atlete_ric = [a for a in st.session_state["elenco_atlete"] if a.get("stagione") == stagione_selezionata and a.get("cognome") != "--- Inizializzazione"]
        if atlete_ric:
            mappa_r = {f"{a.get('cognome')} {a.get('nome')} ({a.get('gruppo')})": a for a in atlete_ric}
            scelta_r = st.selectbox("Seleziona Atleta:", list(mappa_r.keys()))
            atlet_r = mappa_r[scelta_r]
            
            q_tot_s = safe_float(atlet_r.get("tot_scontato", atlet_r.get("quota_tot", 0)))
            v_tot_s = safe_float(atlet_r.get("quota_versata", 0))
            s_rim_s = safe_float(atlet_r.get("saldo_rimanente", 0))
            n_rate_s = atlet_r.get("n_rate", "1 Rata")
            rate_pagate_s = atlet_r.get("rate_pagate_str", "0/1")
            
            st.markdown(f"""
                <div style="background-color: #f1f3f5; padding: 15px; border-radius: 8px; border: 1px solid #ced4da; margin-bottom: 20px;">
                    <h4>📋 Storico Finanziario: {atlet_r.get('cognome')} {atlet_r.get('nome')} (Stagione {stagione_selezionata})</h4>
                    <p><b>Gruppo:</b> {atlet_r.get('gruppo')} | <b>N° Rate previste:</b> {n_rate_s} | <b>Rate Pagate:</b> {rate_pagate_s}</p>
                    <p><b>Quota Totale Scontata:</b> € {q_tot_s:,.2f} &nbsp;|&nbsp; <b>Totale Versato:</b> € {v_tot_s:,.2f} &nbsp;|&nbsp; <span style="color: {'red' if s_rim_s > 0 else 'green'};"><b>Rimanenza / Saldo:</b> € {s_rim_s:,.2f}</span></p>
                </div>
            """, unsafe_allow_html=True)
            
            imp_cons = safe_float(atlet_r.get("quota_versata", 0))
            importo_ricevuta = st.number_input("Importo Ricevuta PDF da emettere (€):", value=imp_cons if imp_cons > 0 else 50.0)
            
            if st.button("📥 Genera e Scarica Ricevuta PDF"):
                pdf_bytes = genera_pdf_ricevuta(atlet_r, importo_ricevuta, nome_societa)
                st.download_button(
                    label="👉 CLICCA QUI PER SCARICARE IL PDF", 
                    data=pdf_bytes, 
                    file_name=f"Ricevuta_{atlet_r.get('cognome')}_{atlet_r.get('nome')}.pdf", 
                    mime="application/pdf"
                )
            
            
                
 
elif pagina_scelta == "Report Finanziario":
    verifica_accesso("Report Finanziario")
    st.markdown(f"<h2 style='text-align: center;'>📊 Report Quote Versate - Stagione {stagione_selezionata}</h2>", unsafe_allow_html=True)
    
    gruppo_scelto_report = st.selectbox("🔍 Seleziona Gruppo per Report:", ["Tutti i Gruppi"] + st.session_state["gruppi_societa"])
    
    atlete_tot_base = [a for a in atlete_stagione_attiva if a.get("cognome") != "--- Inizializzazione"]
    
    tot_iscr_gen = len(atlete_tot_base)
    tot_asp_gen = sum(safe_float(a.get("tot_scontato", 0)) for a in atlete_tot_base)
    tot_inc_gen = sum(safe_float(a.get("quota_versata", 0)) for a in atlete_tot_base)
    tot_rim_gen = tot_asp_gen - tot_inc_gen
    
    st.markdown("#### 🌐 Riepilogo Globale Società")
    cg1, cg2, cg3, cg4 = st.columns(4)
    cg1.metric("Totale Iscritte", tot_iscr_gen)
    cg2.metric("Da Incassare", f"€ {tot_asp_gen:,.2f}")
    cg3.metric("Incassato Totale", f"€ {tot_inc_gen:,.2f}")
    
    rim_gen_color = "#dc3545" if tot_rim_gen > 0 else "#28a745"
    rim_gen_dot = "🔴" if tot_rim_gen > 0 else "🟢"
    cg4.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 14px; border-radius: 8px; border: 1px solid #e6e9ef;">
            <div style="font-size: 14px; color: #6c757d; margin-bottom: 4px;">Rimanenza da Incassare</div>
            <div style="font-size: 24px; font-weight: 600; color: {rim_gen_color};">
                {rim_gen_dot} € {tot_rim_gen:,.2f}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

    atlete_fin = atlete_tot_base
    if gruppo_scelto_report != "Tutti i Gruppi":
        atlete_fin = [a for a in atlete_fin if a.get("gruppo", "").lower() == gruppo_scelto_report.lower() or a.get("gruppo2", "").lower() == gruppo_scelto_report.lower()]
        
        tot_inc_g = sum(safe_float(a.get("quota_versata", 0)) for a in atlete_fin)
        tot_asp_g = sum(safe_float(a.get("tot_scontato", 0)) for a in atlete_fin)
        tot_rim_g = tot_asp_g - tot_inc_g
        
        st.markdown(f"#### 📌 Metriche Specifiche per Gruppo: {gruppo_scelto_report}")
        c_gg1, c_gg2, c_gg3, c_gg4 = st.columns(4)
        c_gg1.metric(f"Iscritte", len(atlete_fin))
        c_gg2.metric("Da Incassare", f"€ {tot_asp_g:,.2f}")
        c_gg3.metric("Incassato", f"€ {tot_inc_g:,.2f}")
        
        rim_g_color = "#dc3545" if tot_rim_g > 0 else "#28a745"
        rim_g_dot = "🔴" if tot_rim_g > 0 else "🟢"
        c_gg4.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 14px; border-radius: 8px; border: 1px solid #e6e9ef;">
                <div style="font-size: 14px; color: #6c757d; margin-bottom: 4px;">Rimanenza</div>
                <div style="font-size: 24px; font-weight: 600; color: {rim_g_color};">
                    {rim_g_dot} € {tot_rim_g:,.2f}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")

    if atlete_fin:
        df_fin = pd.DataFrame(atlete_fin)
        col_mostrate = [c for c in ["cognome", "nome", "gruppo", "quota_tot", "sconto", "tot_scontato", "quota_versata", "saldo_rimanente", "rate_pagate_str", "stato_rate"] if c in df_fin.columns]
        st.dataframe(df_fin[col_mostrate].rename(columns=MAPPING_COLONNE), use_container_width=True)
        
        c_rf1, c_rf2 = st.columns(2)
        with c_rf1:
            csv_fin = df_fin[col_mostrate].rename(columns=MAPPING_COLONNE).to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 Esporta Report in CSV", data=csv_fin, file_name=f"report_finanziario_{stagione_selezionata.replace('/','_')}.csv", mime="text/csv")
        with c_rf2:
            excel_io_fin = io.BytesIO()
            with pd.ExcelWriter(excel_io_fin, engine='openpyxl') as writer:
                df_fin[col_mostrate].rename(columns=MAPPING_COLONNE).to_excel(writer, index=False, sheet_name='ReportFinanziario')
            st.download_button("📊 Esporta Report in Excel (.xlsx)", data=excel_io_fin.getvalue(), file_name=f"report_finanziario_{stagione_selezionata.replace('/','_')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Nessuna atleta trovata per il gruppo selezionato.")

elif pagina_scelta == "Bilancio and Budget":
    verifica_accesso("Bilancio and Budget")
    st.markdown(f"<h2 style='text-align: center;'>📈 Analisi Costi e Ricavi per Gruppo (Stagione {stagione_selezionata})</h2>", unsafe_allow_html=True)
    
    if stagione_selezionata not in st.session_state["config_costi_standard"]:
        st.session_state["config_costi_standard"][stagione_selezionata] = {}
    
    costi_stagione = st.session_state["config_costi_standard"][stagione_selezionata]
    gruppi_societa = st.session_state["gruppi_societa"]
    
    gruppo_scelto_b = st.selectbox("Seleziona Gruppo per Bilancio:", ["Tutti i Gruppi"] + gruppi_societa)
    
    def ottieni_dettaglio_costi_gruppo(g_nome, num_iscr):
        if g_nome not in costi_stagione: return [], 0.0
        dati_g = costi_stagione[g_nome]
        voci_salvate = dati_g.get("voci", [])
        righe_tabella = []
        totale_c = 0.0
        for item in voci_salvate:
            tipo = item.get("tipo", "Voce")
            v1 = safe_float(item.get("val1", 0))
            v2 = safe_float(item.get("val2", 0))
            tot = v1 * v2
            totale_c += tot
            righe_tabella.append({
                "Voce di Costo": tipo.title(),
                "Importo Unitario / Mensile (€)": f"€ {v1:,.2f}",
                "Quantità / Mesi / Atlete": v2,
                "Totale (€)": f"€ {tot:,.2f}"
            })
        return righe_tabella, totale_c

    if gruppo_scelto_b != "Tutti i Gruppi":
        atlete_gruppo_bil = [a for a in atlete_stagione_attiva if a.get("gruppo", "").lower() == gruppo_scelto_b.lower() or a.get("gruppo2", "").lower() == gruppo_scelto_b.lower()]
        num_iscritti_g = len(atlete_gruppo_bil)
        q_tot_gruppo = sum(safe_float(a.get("tot_scontato", 0)) for a in atlete_gruppo_bil)
        v_tot_gruppo = sum(safe_float(a.get("quota_versata", 0)) for a in atlete_gruppo_bil)
        
        righe_dettaglio, tot_costi_gruppo_fin = ottieni_dettaglio_costi_gruppo(gruppo_scelto_b, num_iscritti_g)
        
        st.markdown(f"#### 📋 Tabella Costi Associata al Gruppo: {gruppo_scelto_b}")
        if righe_dettaglio:
            st.dataframe(pd.DataFrame(righe_dettaglio), use_container_width=True)
        else:
            st.info("Nessun costo configurato per questo gruppo.")

        st.markdown("---")
        st.markdown(f"#### 📊 Riepilogo Costi e Ricavi per Gruppo: {gruppo_scelto_b}")
        
        margine_gruppo = v_tot_gruppo - tot_costi_gruppo_fin
        colore_margine = "#28a745" if margine_gruppo >= 0 else "#dc3545"
        simbolo_margine = "🟢" if margine_gruppo >= 0 else "🔴"
        
        df_singolo_gruppo = pd.DataFrame([{
            "Gruppo": gruppo_scelto_b,
            "Iscritti": num_iscritti_g,
            "Incassato (€)": f"€ {v_tot_gruppo:,.2f}",
            "Costi Totali (€)": f"€ {tot_costi_gruppo_fin:,.2f}",
            "Margine (€)": f"{simbolo_margine} € {margine_gruppo:,.2f}"
        }])
        st.dataframe(df_singolo_gruppo, use_container_width=True)

        st.markdown("---")
        dg1, dg2, dg3 = st.columns(3)
        dg1.metric("Quote Versate Gruppo", f"€ {v_tot_gruppo:,.2f}")
        dg2.metric("Costi Totali Gruppo", f"€ {tot_costi_gruppo_fin:,.2f}")
        dg3.metric("Margine Gruppo", f"€ {margine_gruppo:,.2f}")
    else:
        st.subheader("📋 Tabella Costi e Ricavi per Tutti i Gruppi")
        lista_righe_riepilogo = []
        for g in gruppi_societa:
            atlete_g_temp = [a for a in atlete_stagione_attiva if a.get("gruppo", "").lower() == g.lower() or a.get("gruppo2", "").lower() == g.lower()]
            n_iscr_t = len(atlete_g_temp)
            t_vers_g = sum(safe_float(a.get("quota_versata", 0)) for a in atlete_g_temp)
            _, t_costi_g = ottieni_dettaglio_costi_gruppo(g, n_iscr_t)
            m_g = t_vers_g - t_costi_g
            sim_g = "🟢" if m_g >= 0 else "🔴"
            lista_righe_riepilogo.append({
                "Gruppo": g,
                "Iscritti": n_iscr_t,
                "Incassato (€)": f"€ {t_vers_g:,.2f}",
                "Costi Totali (€)": f"€ {t_costi_g:,.2f}",
                "Margine (€)": f"{sim_g} € {m_g:,.2f}"
            })
        df_riepilogo_bilancio = pd.DataFrame(lista_righe_riepilogo)
        st.dataframe(df_riepilogo_bilancio, use_container_width=True)

    st.markdown("---")
    tot_costi_societa = 0.0
    tot_entrate_societa = sum(safe_float(a.get("quota_versata", 0)) for a in atlete_stagione_attiva if a.get("cognome") != "--- Inizializzazione")
    for g in gruppi_societa:
        atlete_g_temp = [a for a in atlete_stagione_attiva if a.get("gruppo", "").lower() == g.lower() or a.get("gruppo2", "").lower() == g.lower()]
        _, t_c_g = ottieni_dettaglio_costi_gruppo(g, len(atlete_g_temp))
        tot_costi_societa += t_c_g

    bc1, bc2, bc3 = st.columns(3)
    bc1.metric("Entrate Totali (Quote)", f"€ {tot_entrate_societa:,.2f}")
    bc2.metric("Costi Totali (Spese)", f"€ {tot_costi_societa:,.2f}")
    bc3.metric("Utile / Perdita", f"€ {tot_entrate_societa - tot_costi_societa:,.2f}")

elif pagina_scelta == "Area Tecnica":
    verifica_accesso("Area Tecnica")
    st.markdown(f"<h2 style='text-align: center;'>📋 Area Tecnica - Squadre e Roster (Stagione {stagione_selezionata})</h2>", unsafe_allow_html=True)
    
    tab_sq, tab_cal, tab_scout, tab_val_tecnica = st.tabs(["🏐 Squadre & Roster", "📅 Calendario Gare", "📊 Scout & Statistiche", "⭐ Valutazioni & Crescita Atlete"])
    
    with tab_sq:
        st.subheader("Gestione, Modifica e Cancellazione Squadre e Categorie")
        
        with st.form("form_aggiungi_squadra_cat"):
            st.write("Aggiungi nuova squadra/gruppo specificando la categoria di appartenenza:")
            nuovo_s_nome = st.text_input("Nome Squadra / Gruppo (es. Under 14, 2015):")
            nuovo_s_cat = st.selectbox("Categoria di Appartenenza:", st.session_state["categorie_societa"])
            nuovo_gruppo_ev = st.selectbox("Seleziona Gruppo:", st.session_state["gruppi_societa"])
            if st.form_submit_button("Crea / Aggiungi Squadra"):
                norm_s = normalizza_nome_gruppo(nuovo_s_nome)
                if norm_s and norm_s not in st.session_state["gruppi_societa"]:
                    st.session_state["gruppi_societa"].append(norm_s)
                    salva_json_sicuro(FILE_GRUPPI, st.session_state["gruppi_societa"])
                    st.success(f"Squadra '{norm_s}' (Categoria: {nuova_s_cat}) aggiunta con successo!")
                    st.rerun()

        st.markdown("---")
        gruppo_scelto_t = st.selectbox("Seleziona Squadra / Gruppo da consultare:", st.session_state["gruppi_societa"], key="sel_gruppo_tecnico")
        
        atlete_gruppo_t = [a for a in atlete_stagione_attiva if a.get("cognome") != "--- Inizializzazione" and (a.get("gruppo", "").lower() == gruppo_scelto_t.lower() or a.get("gruppo2", "").lower() == gruppo_scelto_t.lower())]
        if atlete_gruppo_t:
            df_t = pd.DataFrame(atlete_gruppo_t)
            st.dataframe(df_t[["cognome", "nome", "sesso", "scad_visita", "stato_visita"]].rename(columns=MAPPING_COLONNE), use_container_width=True)
            
            st.markdown("---")
            atleta_da_canc_tec = st.selectbox("Seleziona atleta da rimuovere o cancellare:", ["-- Seleziona --"] + [f"{a['cognome']} {a['nome']}" for a in atlete_gruppo_t], key="del_atleta_tec")
            if atleta_da_canc_tec != "-- Seleziona --":
                if st.button("🗑️ Rimuovi/Cancella Atleta dalla Squadra", key="btn_del_atleta_tec_s"):
                    c_cog, c_nom = atleta_da_canc_tec.split(" ", 1)
                    st.session_state["elenco_atlete"] = [a for a in st.session_state["elenco_atlete"] if not (a.get("cognome") == c_cog and a.get("nome") == c_nom and a.get("stagione") == stagione_selezionata)]
                    salva_atlete(st.session_state["elenco_atlete"])
                    st.success(f"Atleta {atleta_da_canc_tec} rimossa con successo!")
                    st.rerun()
                    
            st.markdown("---")
            if st.button(f"🗑️ ELIMINA INTERO GRUPPO: {gruppo_scelto_t}", key="btn_del_gr_tec"):
                st.session_state["gruppi_societa"] = [gr for gr in st.session_state["gruppi_societa"] if gr.lower() != gruppo_scelto_t.lower()]
                salva_json_sicuro(FILE_GRUPPI, st.session_state["gruppi_societa"])
                st.success(f"Gruppo {gruppo_scelto_t} eliminato con successo!")
                st.rerun()
        else:
            st.info("Nessuna atleta in questo gruppo per la stagione selezionata.")
            st.markdown("---")
            if st.button(f"🗑️ ELIMINA INTERO GRUPPO: {gruppo_scelto_t}", key="btn_del_gr_vuoto_tec"):
                st.session_state["gruppi_societa"] = [gr for gr in st.session_state["gruppi_societa"] if gr.lower() != gruppo_scelto_t.lower()]
                salva_json_sicuro(FILE_GRUPPI, st.session_state["gruppi_societa"])
                st.success(f"Gruppo {gruppo_scelto_t} eliminato con successo!")
                st.rerun()

    with tab_cal:
        st.subheader("📅 Calendario Gare e Partite (Ricerca per Squadra o Generale & Export/Import)")
        if stagione_selezionata not in st.session_state["calendario_gare"]:
            st.session_state["calendario_gare"][stagione_selezionata] = []
        
        gare_stagione = st.session_state["calendario_gare"][stagione_selezionata]
        
        squadra_filtro_cal = st.selectbox("Filtra Calendario per Squadra:", ["Tutte le Squadre"] + st.session_state["gruppi_societa"])
        gare_filtrate = gare_stagione if squadra_filtro_cal == "Tutte le Squadre" else [g for g in gare_stagione if g.get("squadra") == squadra_filtro_cal]

        if gare_filtrate:
            df_gare = pd.DataFrame(gare_filtrate)
            st.dataframe(df_gare, use_container_width=True)
            
            c_ex_g1, c_ex_g2 = st.columns(2)
            with c_ex_g1:
                csv_gare = df_gare.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 Esporta Calendario in CSV", data=csv_gare, file_name=f"calendario_{squadra_filtro_cal}_{stagione_selezionata.replace('/','_')}.csv", mime="text/csv")
            with c_ex_g2:
                excel_io_gare = io.BytesIO()
                with pd.ExcelWriter(excel_io_gare, engine='openpyxl') as writer:
                    df_gare.to_excel(writer, index=False, sheet_name='CalendarioGare')
                st.download_button("📊 Esporta Calendario in Excel (.xlsx)", data=excel_io_gare.getvalue(), file_name=f"calendario_{squadra_filtro_cal}_{stagione_selezionata.replace('/','_')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("Nessuna gara registrata per la selezione corrente.")
            
        with st.form("form_aggiungi_gara"):
            st.write("Aggiungi nuova Partita al Calendario:")
            g_data = st.text_input("Data Partita (GG/MM/AAAA):")
            g_sq = st.selectbox("Squadra:", st.session_state["gruppi_societa"])
            g_avv = st.text_input("Avversario:")
            g_casa = st.selectbox("Luogo:", ["Casa", "Trasferta"])
            if st.form_submit_button("Aggiungi Partita"):
                if g_data and g_avv:
                    gare_stagione.append({"data": g_data, "squadra": g_sq, "avversario": g_avv, "luogo": g_casa})
                    salva_json_sicuro(FILE_GARE, st.session_state["calendario_gare"])
                    st.success("✅ Partita aggiunta con successo!")
                    st.rerun()

    with tab_scout:
        st.subheader("📊 Modulo Scout e Monitoraggio Prestazioni")
        if stagione_selezionata not in st.session_state["scout_squadre"]:
            st.session_state["scout_squadre"][stagione_selezionata] = {}
        
        scout_s = st.session_state["scout_squadre"][stagione_selezionata]
        squadra_scout = st.selectbox("Seleziona Squadra per Scout:", st.session_state["gruppi_societa"], key="scout_sq_sel")
        
        note_esistenti = scout_s.get(squadra_scout, "")
        nuove_note = st.text_area("Note Tecniche / Analisi Fondamentali:", value=note_esistenti, height=150)
        if st.button("Salva Note Scout"):
            scout_s[squadra_scout] = nuove_note
            salva_json_sicuro(FILE_SCOUT, st.session_state["scout_squadre"])
            st.success("✅ Note tecniche salvate con successo!")

    with tab_val_tecnica:
        st.subheader("⭐ Valutazioni Tecniche, Ruoli, Misure e Crescita Sportiva")
        atlete_val_base = [a for a in st.session_state["elenco_atlete"] if a.get("cognome") != "--- Inizializzazione"]
        if atlete_val_base:
            mappa_v = {f"{a.get('cognome')} {a.get('nome')} ({a.get('stagione')})": a for a in atlete_val_base}
            atleta_scelta_str = st.selectbox("Seleziona Atleta (tutte le stagioni):", list(mappa_v.keys()))
            atleta_v = mappa_v[atleta_scelta_str]
            
            if "valutazioni_tecniche" not in atleta_v or not isinstance(atleta_v["valutazioni_tecniche"], dict):
                atleta_v["valutazioni_tecniche"] = {}
            
            v_data = atleta_v["valutazioni_tecniche"]
            
            with st.form(f"form_valutazione_tecnica_{atleta_v.get('cognome')}_{atleta_v.get('nome')}_{atleta_v.get('stagione')}"):
                st.markdown(f"### Scheda Tecnica: {atleta_v.get('cognome')} {atleta_v.get('nome')} - Stagione: {atleta_v.get('stagione')}")
                
                c_t1, c_t2, c_t3 = st.columns(3)
                with c_t1:
                    ruolo_atleta = st.selectbox("Ruolo in Campo:", ["Palleggiatrice", "Schiacciatrice / Banda", "Opposto", "Centrale", "Libero"], index=["Palleggiatrice", "Schiacciatrice / Banda", "Opposto", "Centrale", "Libero"].index(v_data.get("ruolo", "Schiacciatrice / Banda")) if v_data.get("ruolo") in ["Palleggiatrice", "Schiacciatrice / Banda", "Opposto", "Centrale", "Libero"] else 0)
                with c_t2:
                    altezza_cm = st.number_input("Altezza (cm):", min_value=120, max_value=210, value=int(safe_float(v_data.get("altezza", 170))))
                with c_t3:
                    attacco_cm = st.number_input("Raggiungimento / Salto Attacco (cm):", min_value=150, max_value=330, value=int(safe_float(v_data.get("salto_attacco", 250))))

                st.markdown("---")
                st.markdown("#### 📈 Valutazione Fondamentali (Tendina / Giudizio)")
                
                giudizi_possibili = ["Ottimo (9-10)", "Buono (7-8)", "Sufficienza (6)", "Da Sviluppare (<6)"]
                
                def get_idx_giudizio(val):
                    try: return giudizi_possibili.index(val)
                    except: return 1

                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1:
                    fond_battuta = st.selectbox("Battuta:", giudizi_possibili, index=get_idx_giudizio(v_data.get("battuta", "Buono (7-8)")))
                    fond_attacco = st.selectbox("Attacco:", giudizi_possibili, index=get_idx_giudizio(v_data.get("attacco", "Buono (7-8)")))
                with col_f2:
                    fond_ricezione = st.selectbox("Ricezione:", giudizi_possibili, index=get_idx_giudizio(v_data.get("ricezione", "Buono (7-8)")))
                    fond_palleggio = st.selectbox("Palleggio:", giudizi_possibili, index=get_idx_giudizio(v_data.get("palleggio", "Buono (7-8)")))
                with col_f3:
                    fond_muro = st.selectbox("Muro:", giudizi_possibili, index=get_idx_giudizio(v_data.get("muro", "Buono (7-8)")))
                    fond_difesa = st.selectbox("Difesa:", giudizi_possibili, index=get_idx_giudizio(v_data.get("difesa", "Buono (7-8)")))

                st.markdown("---")
                crescita_sportiva = st.text_area("Crescita Sportiva e Note Tecniche dell'Allenatore:", value=v_data.get("crescita", ""), height=120)
                
                if st.form_submit_button("Salva Valutazione e Misure Tecniche"):
                    atleta_v["valutazioni_tecniche"] = {
                        "ruolo": ruolo_atleta,
                        "altezza": altezza_cm,
                        "salto_attacco": attacco_cm,
                        "battuta": fond_battuta,
                        "attacco": fond_attacco,
                        "ricezione": fond_ricezione,
                        "palleggio": fond_palleggio,
                        "muro": fond_muro,
                        "difesa": fond_difesa,
                        "crescita": crescita_sportiva
                    }
                    salva_atlete(st.session_state["elenco_atlete"])
                    st.success("✅ Valutazione tecnica e misure salvate con successo!")

            st.markdown("---")
            st.subheader(f"📊 Confronto Storico / Altre Stagioni per: {atleta_v.get('cognome')} {atleta_v.get('nome')}")
            stionar_atleta = [a for a in st.session_state["elenco_atlete"] if a.get("cognome", "").lower() == atleta_v.get("cognome", "").lower() and a.get("nome", "").lower() == atleta_v.get("nome", "").lower()]
            
            if stionar_atleta:
                righe_storico = []
                for s_item in stionar_atleta:
                    v_storica = s_item.get("valutazioni_tecniche", {})
                    righe_storico.append({
                        "Stagione": s_item.get("stagione"),
                        "Gruppo": s_item.get("gruppo"),
                        "Ruolo": v_storica.get("ruolo", "N/D"),
                        "Altezza (cm)": v_storica.get("altezza", "-"),
                        "Salto Attacco (cm)": v_storica.get("salto_attacco", "-"),
                        "Battuta": v_storica.get("battuta", "-"),
                        "Attacco": v_storica.get("attacco", "-"),
                        "Ricezione": v_storica.get("ricezione", "-"),
                        "Note Crescita": v_storica.get("crescita", "-")
                    })
                st.dataframe(pd.DataFrame(righe_storico), use_container_width=True)
            else:
                st.info("Nessun dato storico disponibile.")
        else:
            st.info("Nessuna atleta registrata nel sistema.")

elif pagina_scelta == "Area Amministratori":
    st.markdown("<h2 style='text-align: center;'>⚙️ Pannello Amministrazione e Backup</h2>", unsafe_allow_html=True)
    
    tab_adm1, tab_adm2, tab_adm3, tab_adm4, tab_adm5, tab_adm6 = st.tabs(["🏛️ Nome Società", "🔐 Gestione Utenti", "📁 Gestione Gruppi", "⚙️ Configurazione Quote", "⚙️ Configurazione Costi", "💾 Backup di Sicurezza"])
    
    with tab_adm1:
        st.subheader("Personalizzazione Nome della Società Sportiva")
        with st.form("form_nome_societa"):
            nuovo_nome_soc = st.text_input("Nome Ufficiale Società:", value=nome_societa)
            if st.form_submit_button("Aggiorna Nome Società"):
                if nuovo_nome_soc.strip():
                    config_societa["nome"] = nuovo_nome_soc.strip()
                    salva_json_sicuro(FILE_CONFIG_SOCIETA, config_societa)
                    st.success("✅ Nome società aggiornato! Ricarica la pagina per applicarlo ovunque.")
                    st.rerun()

    with tab_adm2:
        st.subheader("Gestione Account e Permessi d'Accesso")
        utenti_d = st.session_state["utenti"]
        
        with st.form("form_nuovo_utente"):
            nuovo_user = st.text_input("Nuovo Username:")
            nuova_pwd = st.text_input("Password:", type="password")
            nuovo_ruolo = st.selectbox("Ruolo:", ["Amministratore", "Dirigente", "Allenatore", "Segreteria"])
            aree_possibili = ["Area Amministratori", "Promozionale", "Giovanile", "Gestionale", "Area Tecnica", "Segreteria", "Report Finanziario", "Bilancio and Budget"]
            aree_scelte = st.multiselect("Aree Accessibili:", aree_possibili, default=["Gestionale"])
            
            if st.form_submit_button("Crea Utente"):
                if nuovo_user and nuova_pwd:
                    utenti_d[nuovo_user.strip().lower()] = {
                        "password": nuova_pwd.strip(),
                        "ruolo": nuovo_ruolo,
                        "area": aree_scelte
                    }
                    salva_json_sicuro(FILE_UTENTI, utenti_d)
                    st.success(f"✅ Utente '{nuovo_user}' creato con successo!")
                    st.rerun()
                else:
                    st.error("Inserisci username e password validi.")

    with tab_adm3:
        st.subheader("Inserisci o Cancella Gruppi / Squadre")
        gruppi_attivi = st.session_state["gruppi_societa"]
        st.write("Gruppi attivi attuali:", ", ".join(gruppi_attivi))
        
        with st.form("form_aggiungi_gruppo"):
            nuovo_gruppo = st.text_input("Nome Nuovo Gruppo / Squadra (es. Under 14, 2015):")
            if st.form_submit_button("Aggiungi Gruppo"):
                norm_g = normalizza_nome_gruppo(nuovo_gruppo)
                if norm_g and norm_g not in gruppi_attivi:
                    gruppi_attivi.append(norm_g)
                    salva_json_sicuro(FILE_GRUPPI, gruppi_attivi)
                    st.success(f"Gruppo '{norm_g}' aggiunto!")
                    st.rerun()

        gruppo_da_eliminare = st.selectbox("Seleziona gruppo da eliminare:", ["-- Seleziona --"] + gruppi_attivi)
        if gruppo_da_eliminare != "-- Seleziona --":
            if st.button("🗑️ Elimina Gruppo Selezionato"):
                st.session_state["gruppi_societa"] = [g for g in gruppi_attivi if g != gruppo_da_eliminare]
                salva_json_sicuro(FILE_GRUPPI, st.session_state["gruppi_societa"])
                st.success(f"Gruppo '{gruppo_da_eliminare}' eliminato!")
                st.rerun()

    with tab_adm4:
        st.subheader("⚙️ Configurazione Centralizzata Quote e Rate per Gruppo")
        gruppo_config = st.selectbox("Seleziona Gruppo / Squadra da configurare:", st.session_state["gruppi_societa"], key="cfg_gruppo")
        
        if "config_quote" not in st.session_state:
            st.session_state["config_quote"] = {}
            
        conf_corr = st.session_state["config_quote"].get(gruppo_config, {"n_rate": "1 Rata", "quota_tot": 500.0, "r1_imp": 500.0, "r2_imp": 0.0, "r3_imp": 0.0, "r4_imp": 0.0})
        
        with st.form("form_config_quote_gruppo"):
            c_rate = st.selectbox("N° Rate Standard:", ["1 Rata", "2 Rate", "3 Rate", "4 Rate"], index=["1 Rata", "2 Rate", "3 Rate", "4 Rate"].index(conf_corr.get("n_rate", "1 Rata")) if conf_corr.get("n_rate") in ["1 Rata", "2 Rate", "3 Rate", "4 Rate"] else 0)
            c_tot = st.number_input("Quota Totale Prevista (€):", value=safe_float(conf_corr.get("quota_tot", 500.0)))
            
            col_cr1, col_cr2 = st.columns(2)
            with col_cr1:
                c_r1 = st.number_input("Importo 1ª Rata (€):", value=safe_float(conf_corr.get("r1_imp", 500.0)))
                c_r1_d = st.text_input("Data Scadenza 1ª Rata (GG/MM/AAAA):", value=conf_corr.get("r1_data", ""))
                c_r2 = st.number_input("Importo 2ª Rata (€):", value=safe_float(conf_corr.get("r2_imp", 0.0)))
                c_r2_d = st.text_input("Data Scadenza 2ª Rata (GG/MM/AAAA):", value=conf_corr.get("r2_data", ""))
            with col_cr2:
                c_r3 = st.number_input("Importo 3ª Rata (€):", value=safe_float(conf_corr.get("r3_imp", 0.0)))
                c_r3_d = st.text_input("Data Scadenza 3ª Rata (GG/MM/AAAA):", value=conf_corr.get("r3_data", ""))
                c_r4 = st.number_input("Importo 4ª Rata (€):", value=safe_float(conf_corr.get("r4_imp", 0.0)))
                c_r4_d = st.text_input("Data Scadenza 4ª Rata (GG/MM/AAAA):", value=conf_corr.get("r4_data", ""))
            
            if st.form_submit_button("Salva Configurazione Quote Gruppo"):
                st.session_state["config_quote"][gruppo_config] = {
                    "n_rate": c_rate, "quota_tot": c_tot,
                    "r1_imp": c_r1, "r1_data": c_r1_d,
                    "r2_imp": c_r2, "r2_data": c_r2_d,
                    "r3_imp": c_r3, "r3_data": c_r3_d,
                    "r4_imp": c_r4, "r4_data": c_r4_d
                }
                salva_json_sicuro(FILE_CONFIG_QUOTE, st.session_state["config_quote"])
                st.success(f"✅ Configurazione quote salvata per {gruppo_config}!")

    with tab_adm5:
        st.subheader("⚙️ Configurazione Costi Standard per Gruppo (Stile Excel)")
        
        voci_correnti = st.session_state.get("voci_costi_config", voci_costi_default)
        st.write("Voci di costo disponibili per le righe:", ", ".join(voci_correnti))
        
        col_vc1, col_vc2 = st.columns(2)
        with col_vc1:
            with st.form("form_aggiungi_voce_costo_adm"):
                nuova_voce_c = st.text_input("Inserisci Nuova Voce:")
                if st.form_submit_button("Aggiungi Voce"):
                    n_clean = nuova_voce_c.strip().lower()
                    if n_clean and n_clean not in voci_correnti:
                        voci_correnti.append(n_clean)
                        st.session_state["voci_costi_config"] = voci_correnti
                        salva_json_sicuro(FILE_CONFIG_VOCI_COSTI, voci_correnti)
                        st.success(f"✅ Voce '{n_clean}' aggiunta!")
                        st.rerun()
        with col_vc2:
            with st.form("form_elimina_voce_costo_adm"):
                voce_da_rimuovere = st.selectbox("Elimina / Cancella Voce:", ["-- Seleziona --"] + voci_correnti)
                if st.form_submit_button("Elimina Voce Selezionata"):
                    if voce_da_rimuovere != "-- Seleziona --":
                        st.session_state["voci_costi_config"] = [v for v in voci_correnti if v != voce_da_rimuovere]
                        salva_json_sicuro(FILE_CONFIG_VOCI_COSTI, st.session_state["voci_costi_config"])
                        st.success(f"❌ Voce '{voce_da_rimuovere}' rimossa!")
                        st.rerun()

        st.markdown("---")
        gruppo_scelto_config_costi = st.selectbox("Seleziona Gruppo per configurare i costi:", st.session_state["gruppi_societa"], key="sel_gruppo_config_costi_std")
        
        if stagione_selezionata not in st.session_state["config_costi_standard"]:
            st.session_state["config_costi_standard"][stagione_selezionata] = {}
        
        costi_stagione_dict = st.session_state["config_costi_standard"][stagione_selezionata]
        if gruppo_scelto_config_costi not in costi_stagione_dict:
            costi_stagione_dict[gruppo_scelto_config_costi] = {
                "voci": [
                    {"tipo": "rimborso allenatore", "val1": 450.0, "val2": 10.0},
                    {"tipo": "aiuto allenatore", "val1": 100.0, "val2": 10.0},
                    {"tipo": "tuta", "val1": 26.0, "val2": 0.0},
                    {"tipo": "zaino", "val1": 20.0, "val2": 0.0},
                    {"tipo": "divisa allenamento", "val1": 15.0, "val2": 0.0},
                    {"tipo": "palestre", "val1": 10.0, "val2": 100.0},
                    {"tipo": "tesseramento", "val1": 5.0, "val2": 0.0}
                ]
            }

        dati_costi_gruppo = costi_stagione_dict[gruppo_scelto_config_costi]
        lista_voci_salvate = dati_costi_gruppo.get("voci", [])

        atlete_gruppo_config = [a for a in atlete_stagione_attiva if a.get("gruppo", "").lower() == gruppo_scelto_config_costi.lower() or a.get("gruppo2", "").lower() == gruppo_scelto_config_costi.lower()]
        num_iscritti_reale = len(atlete_gruppo_config)

        st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 6px; border: 1px solid #dee2e6; margin-bottom: 15px;">
                <b>Gruppo Selezionato:</b> {gruppo_scelto_config_costi} &nbsp;|&nbsp; <b>Atlete reali registrate:</b> {num_iscritti_reale}
            </div>
        """, unsafe_allow_html=True)

        with st.form(f"form_maschera_costi_dinamica_{gruppo_scelto_config_costi}"):
            st.write("📋 **Tabella Costi (Con Totale Calcolato e Valore Atlete Editabile):**")
            
            nuove_voci_inserite = []
            
            for idx, item in enumerate(lista_voci_salvate):
                c_t1, c_t2, c_t3, c_t4, c_t5 = st.columns([2, 2, 2, 1.5, 1])
                with c_t1:
                    tipo_scelto = st.selectbox(f"Voce #{idx+1}", voci_correnti, index=voci_correnti.index(item.get("tipo")) if item.get("tipo") in voci_correnti else 0, key=f"v_tipo_{gruppo_scelto_config_costi}_{idx}")
                with c_t2:
                    is_atlete_dep = tipo_scelto in ["tuta", "zaino", "divisa allenamento", "tesseramento"]
                    label_val1 = "Importo unitario (€):" if is_atlete_dep else "Importo mensile / Valore (€):"
                    val1_in = st.number_input(label_val1, value=safe_float(item.get("val1", 0)), step=5.0, key=f"v_val1_{gruppo_scelto_config_costi}_{idx}")
                with c_t3:
                    default_val2 = safe_float(item.get("val2", num_iscritti_reale if is_atlete_dep else 10))
                    if is_atlete_dep:
                        val2_in = st.number_input("Atlete gruppo:", value=default_val2 if default_val2 > 0 else float(num_iscritti_reale), step=1.0, key=f"v_val2_{gruppo_scelto_config_costi}_{idx}")
                    elif "palestra" in tipo_scelto:
                        val2_in = st.number_input("Totale Ore:", value=default_val2, step=10.0, key=f"v_val2_{gruppo_scelto_config_costi}_{idx}")
                    else:
                        val2_in = st.number_input("Mesi / Q.tà:", value=default_val2, step=1.0, key=f"v_val2_{gruppo_scelto_config_costi}_{idx}")
                with c_t4:
                    totale_riga = val1_in * val2_in
                    st.markdown(f"**Totale:**<br>`€ {totale_riga:,.2f}`", unsafe_allow_html=True)
                with c_t5:
                    st.write("")
                    rimuovi_riga = st.checkbox("🗑️ Elimina", key=f"del_riga_{gruppo_scelto_config_costi}_{idx}")

                if not rimuovi_riga:
                    nuove_voci_inserite.append({"tipo": tipo_scelto, "val1": val1_in, "val2": val2_in})

            st.markdown("---")
            st.write("➕ **Aggiungi Nuova Riga di Costo:**")
            c_add1, c_add2, c_add3 = st.columns(3)
            with c_add1:
                nuova_riga_tipo = st.selectbox("Tipo Voce da aggiungere:", voci_correnti, key=f"add_tipo_{gruppo_scelto_config_costi}")
            with c_add2:
                nuova_riga_v1 = st.number_input("Valore 1 (€):", value=0.0, step=10.0, key=f"add_v1_{gruppo_scelto_config_costi}")
            with c_add3:
                is_atlete_dep_add = nuova_riga_tipo in ["tuta", "zaino", "divisa allenamento", "tesseramento"]
                default_v2_add = float(num_iscritti_reale) if is_atlete_dep_add else 10.0
                nuova_riga_v2 = st.number_input("Valore 2 (Atlete/Mesi/Ore):", value=default_v2_add, step=1.0, key=f"add_v2_{gruppo_scelto_config_costi}")

            if st.form_submit_button("Salva Configurazione Costi"):
                if nuova_riga_v1 > 0:
                    nuove_voci_inserite.append({"tipo": nuova_riga_tipo, "val1": nuova_riga_v1, "val2": nuova_riga_v2})
                
                costi_stagione_dict[gruppo_scelto_config_costi] = {"voci": nuove_voci_inserite}
                st.session_state["config_costi_standard"] = costi_stagione_dict
                salva_json_sicuro(FILE_CONFIG_COSTI_STANDARD, st.session_state["config_costi_standard"])
                st.success(f"✅ Costi salvati con successo per {gruppo_scelto_config_costi}!")
                st.rerun()

    with tab_adm6:
        st.subheader("Gestione Backup Automatici e Manuali")
        st.write("Le modifiche e i dati salvati vengono protetti automaticamente.")
        if st.button("Forza Backup Manuale di Sicurezza Now", use_container_width=True):
            esegui_backup()
            st.success("✅ Backup eseguito con successo nella cartella 'backup/'!")
