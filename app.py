import streamlit as st
import json
import os
import shutil
import pandas as pd
import requests
import io
from datetime import datetime

# --- CONFIGURAZIONE E FILE ---
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

URL_MASTER_CSV = "https://google.com"
LINK_GOOGLE_FORM = "https://forms.gle"
LINK_GOOGLE_SHEETS_EMBED = "https://google.com"

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
    div.stLinkButton > a { background-color: #28a745 !important; color: white !important; font-weight: bold; border-radius: 6px; }
    </style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SERVIZIO ---
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

    importo_sconto = round(quota_tot * (sconto_perc / 100.0), 2)
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
        ricalcola_finanze(a)
    return atlete_caricate

# --- MAIN APP ---
config_societa = carica_json(FILE_CONFIG_SOCIETA, {"nome": "Monviso Volley"})
nome_societa = config_societa.get("nome", "Monviso Volley")
atlete = carica_atlete()
storico_tecnico = carica_json(FILE_STORICO_TECNICO, {})

menu = st.sidebar.radio("Menu Navigazione", ["Dashboard", "Registro Atlete", "Aggiungi Atleta", "Valutazioni e Crescita"])

if menu == "Dashboard":
    st.subheader("📊 Stato Generale Società")
    tot_iscritti = len(atlete)
    visite_ok = sum(1 for a in atlete if a.get("stato_visita") == "🟢 VALIDA")
    visite_ko = sum(1 for a in atlete if a.get("stato_visita") in ["🔴 SCADUTA", "🔴 MANCANTE"])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Atlete Totali", tot_iscritti)
    col2.metric("Certificati OK 🟢", visite_ok)
    col3.metric("Certificati KO 🔴", visite_ko)

elif menu == "Registro Atlete":
    st.subheader("👥 Elenco Atlete")
    if not atlete:
        st.info("Nessuna atleta registrata.")
    else:
        df = pd.DataFrame(atlete)
        col_visibili = ["cognome", "nome", "gruppo", "gruppo2", "stato_visita", "scad_visita", "rate_pagate_str", "quota_versata", "saldo_rimanente", "stato_rate"]
        st.dataframe(df[col_visibili], use_container_width=True)

elif menu == "Aggiungi Atleta":
    st.subheader("📝 Registrazione Nuova Anagrafica")
    with st.form("nuovo_utente"):
        c1, c2 = st.columns(2)
        cognome = c1.text_input("Cognome *")
        nome = c2.text_input("Nome *")
        g1 = c1.text_input("Gruppo")
        scad = c2.text_input("Scadenza Certificato (GG/MM/AAAA)")
        
        quota = c1.number_input("Quota Base (€)", min_value=0.0, step=10.0)
        sconto = c2.number_input("Sconto (%)", min_value=0.0, max_value=100.0)
        
        salva = st.form_submit_button("Salva Atleta")
        if salva:
            if not cognome or not nome:
                st.error("I campi Nome e Cognome sono obbligatori!")
            else:
                nuovo = {"cognome": cognome.strip(), "nome": nome.strip(), "gruppo": g1, "gruppo2": "", "scad_visita": scad, "quota_tot": quota, "sconto": sconto}
                atlete.append(nuovo)
                salva_json_sicuro(FILE_ATLETE, atlete)
                st.success("Atleta inserita!")
                st.rerun()

elif menu == "Valutazioni e Crescita":
    st.subheader("📈 Parametri Fisici e Tecnici")
    if not atlete:
        st.info("Registra prima un'atleta.")
    else:
        nomi = [f"{a['cognome']} {a['nome']}" for a in atlete]
        scelta = st.selectbox("Seleziona Atleta", nomi)
        id_atleta = scelta.replace(" ", "_")
        
        if id_atleta not in storico_tecnico:
            storico_tecnico[id_atleta] = []
            
        with st.form("val_form"):
            h = st.number_input("Altezza (cm)", min_value=100, max_value=250, value=170)
            w = st.number_input("Peso (kg)", min_value=30.0, max_value=150.0, value=60.0)
            v_pagg = st.slider("Voto Palleggio", 1, 10, 6)
            
            invia = st.form_submit_button("Registra Misure")
            if invia:
                storico_tecnico[id_atleta].append({"data": datetime.now().strftime("%d/%m/%Y"), "altezza": h, "peso": w, "palleggio": v_pagg})
