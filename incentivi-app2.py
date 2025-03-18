import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime

DATA_FILE = "incentives_data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"employees": {}}

def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

data = load_data()

# ----------------------------------------------------------------------------
# MENU DI NAVIGAZIONE
# ----------------------------------------------------------------------------
st.sidebar.title("Menu di Navigazione")
page = st.sidebar.radio(
    "Vai a", 
    [
        "Dashboard Avanzata",  # <--- NUOVA DASHBOARD
        # "Dashboard",         # <-- vecchia Dashboard (COMMENTATA O RIMOSSA)
        "Gestione Dipendenti", 
        "Gestione KPI", 
        "Inserimento Risultati", 
        "Report e Analisi"
    ]
)

# ----------------------------------------------------------------------------
# UTILS PER PDF (rimangono uguali)
# ----------------------------------------------------------------------------

def genera_scheda_dipendente_pdf(emp, incentivi_mensili):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)

    pdf.cell(200, 10, "Scheda Dipendente", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, f"Nome: {emp['name']}", ln=True)
    pdf.cell(200, 10, f"Data Stampa: {datetime.today().strftime('%Y-%m-%d')}", ln=True)
    pdf.ln(10)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Dettagli KPI", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "", 12)
    for kpi_name, kpi_details in emp.get("kpis", {}).items():
        pdf.cell(200, 8, f"KPI: {kpi_name}", ln=True)
        pdf.cell(200, 8, f"Tipo Incentivo: {kpi_details.get('incentive_type', 'N/A')}", ln=True)
        pdf.cell(200, 8, f"Risultato Minimo: {kpi_details.get('risultato_minimo', 'N/A')}", ln=True)
        pdf.cell(200, 8, f"Premio: {kpi_details.get('premio', 'N/A')} EUR", ln=True)
        pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Risultati Inseriti", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "", 12)
    for kpi_name, kpi_details in emp.get("kpis", {}).items():
        if "storico_risultati" in kpi_details:
            pdf.cell(200, 8, f"KPI: {kpi_name}", ln=True)
            for entry in kpi_details["storico_risultati"]:
                pdf.cell(200, 8, f"  - Data: {entry['data']} | Valore: {entry['valore_raggiunto']}", ln=True)
            pdf.ln(5)

    return pdf

def genera_riassunto_mensile_pdf(emp, incentivi_mensili):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)

    pdf.cell(200, 10, "Riepilogo Incentivi Mensili", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, f"Nome: {emp['name']}", ln=True)
    pdf.cell(200, 10, f"Data Stampa: {datetime.today().strftime('%Y-%m-%d')}", ln=True)
    pdf.ln(10)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Incentivi Maturati", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "", 12)
    for mese, dati in incentivi_mensili.items():
        pdf.cell(200, 8, f"Mese: {mese}", ln=True)
        for kpi_name, info in dati.items():
            if isinstance(info, dict):
                pdf.cell(200, 8, f"  - KPI: {kpi_name} | Incentivo: {info.get('totale', 0)} EUR | Risultato: {info.get('valore_raggiunto', 0)}", ln=True)
            else:
                pdf.cell(200, 8, f"  - KPI: {kpi_name} | Incentivo: 0 EUR | Risultato: 0", ln=True)
        pdf.ln(5)

    return pdf

def genera_pdf_report_mensile_singolo_dipendente(emp, mese, incentivi_mensili):
    """
    Genera un PDF professionale per il singolo dipendente 'emp' relativo al mese 'mese',
    con i dati presi da 'incentivi_mensili[mese]'.
    Riepiloga: stipendio, incentivi totali, % PPF (se impostato), testo introduttivo e conclusivo.
    """
    from fpdf import FPDF
    
    # Recupero dati principali
    nome_dipendente = emp.get("name", "Dipendente Sconosciuto")
    stipendio_base = float(emp.get("salario_mensile", 0))
    ppf = float(emp.get("ppf", 0))
    
    # Incentivi totali di questo mese
    dettagli_mese = incentivi_mensili.get(mese, {})
    
    # Somma di tutti i KPI di questo mese
    incentivo_mese = 0
    for kpi_name, info in dettagli_mese.items():
        if isinstance(info, dict):
            incentivo_mese += info.get("totale", 0)
    
    # Calcolo del totale compenso
    compenso_totale = stipendio_base + incentivo_mese
    
    # Calcolo % raggiungimento PPF se > 0
    percent_ppf = 0
    if ppf > 0:
        percent_ppf = (compenso_totale / ppf) * 100
    
    # Creiamo il PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Titolo
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Riepilogo Incentivi - Mese {mese}", ln=True, align="C")
    pdf.ln(5)
    
    # Testo introduttivo
    pdf.set_font("Arial", "", 12)
    testo_intro = (
        f"Gentile {nome_dipendente},\n\n"
        f"Desideriamo informarla in merito ai risultati raggiunti e agli incentivi maturati "
        f"nel corso del mese {mese}.\n"
        "Grazie alle sue performance e al suo impegno, sono stati calcolati i seguenti importi:\n"
    )
    pdf.multi_cell(0, 7, testo_intro)
    pdf.ln(3)
    
    # Riepilogo importi
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, f"Stipendio base mensile: {stipendio_base:,.2f} EUR", ln=True)
    pdf.cell(0, 8, f"Incentivi totali: {incentivo_mese:,.2f} EUR", ln=True)
    pdf.cell(0, 8, f"Compenso totale (stipendio + incentivi): {compenso_totale:,.2f} EUR", ln=True)
    
    if ppf > 0:
        pdf.cell(0, 8, f"PPF mensile: {ppf:,.2f} EUR", ln=True)
        pdf.cell(0, 8, f"Percentuale di raggiungimento PPF: {percent_ppf:,.2f}%", ln=True)
    
    pdf.ln(5)
    
    # (Opzionale) Dettaglio KPI se vuoi elencarli
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Dettaglio KPI e Incentivi:", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.ln(3)
    
    for kpi_name, info in dettagli_mese.items():
        if isinstance(info, dict):
            val_raggiunto = info.get("valore_raggiunto", 0)
            inc_kpi = info.get("totale", 0)
            pdf.multi_cell(0, 7, f"- KPI: {kpi_name}\n  Valore Raggiunto: {val_raggiunto}\n  Incentivo: {inc_kpi:,.2f} EUR")
            pdf.ln(2)
    
    # Conclusioni
    pdf.ln(5)
    pdf.set_font("Arial", "", 12)
    testo_finale = (
        "Siamo lieti di riconoscere il suo contributo e la invitiamo a proseguire "
        "nell'ottica di miglioramento continuo. Per eventuali chiarimenti o suggerimenti, "
        "restiamo a disposizione.\n\n"
        "Cordiali saluti,\n"
        "Ufficio Risorse Umane"
    )
    pdf.multi_cell(0, 7, testo_finale)
    
    return pdf


# ----------------------------------------------------------------------------
# NUOVA DASHBOARD AVANZATA
# ----------------------------------------------------------------------------

if page == "Dashboard Avanzata":
    st.title("📊 Gestione Piano Incentivo Aziendale")

    if not data["employees"]:
        st.warning("⚠️ Nessun dipendente registrato.")
    else:
        # 1) CAMPO DI RICERCA TESTUALE
        search_term = st.text_input("🔎 Cerca dipendente per nome").strip().lower()
        
        # Filtro base
        filtered_employees = {
            emp_id: emp
            for emp_id, emp in data["employees"].items()
            if search_term in emp["name"].lower()  # match parziale sul nome
        }

        if not filtered_employees:
            st.warning("Nessun dipendente trovato con questo criterio di ricerca.")
        else:
            # 2) SELEZIONE MULTIPLA DEI DIPENDENTI FILTRATI
            selected_emp_ids = st.multiselect(
                "Seleziona uno o più dipendenti",
                list(filtered_employees.keys()),
                default=list(filtered_employees.keys()),  # selezionati di default
                format_func=lambda x: filtered_employees[x]["name"]
            )

            # Se non ci sono dipendenti selezionati, niente da mostrare
            if not selected_emp_ids:
                st.info("Seleziona almeno un dipendente per visualizzare i dati.")
            else:
                st.write("### 📋 Riepilogo Incentivi e Stipendi")
                riepilogo_completo = []
                profitto_completo = []
                mesi_globali = set()

                # --------------------------------
                # CALCOLO E COSTRUZIONE DATI
                # --------------------------------
                for emp_id in selected_emp_ids:
                    emp = data["employees"][emp_id]

                    if "kpis" not in emp:
                        emp["kpis"] = {}

                    incentivi_mensili = {}
                    risultati_mensili_global = set()

                    for kpi_name, kpi_details in emp["kpis"].items():
                        if "storico_risultati" in kpi_details:
                            # Sommiamo i risultati per mese
                            risultati_mensili = {}
                            for entry in kpi_details["storico_risultati"]:
                                mese = entry["data"][:7]
                                valore = entry["valore_raggiunto"]
                                risultati_mensili[mese] = risultati_mensili.get(mese, 0) + valore
                            
                            for mese, valore_totale in risultati_mensili.items():
                                risultati_mensili_global.add(mese)
                                incentivo = 0
                                valore_minimo = kpi_details.get("risultato_minimo", 0)
                                profitto_generato = 0

                                if valore_totale >= valore_minimo:
                                    # Scaglioni
                                    if kpi_details.get("scaglioni", []):
                                        scaglioni_corretto = [
                                            (s[0], s[1], s[2] if len(s) > 2 else 0) 
                                            for s in kpi_details["scaglioni"]
                                        ]
                                        for soglia, premio_scaglione, percentuale_scaglione in sorted(scaglioni_corretto, key=lambda x: x[0]):
                                            if valore_totale >= soglia:
                                                if kpi_details["incentive_type"] == "% sul risultato":
                                                    incentivo = (valore_totale * percentuale_scaglione) / 100
                                                elif kpi_details["incentive_type"] == "% sul salario mensile":
                                                    incentivo = (emp["salario_mensile"] * percentuale_scaglione) / 100
                                                elif kpi_details["incentive_type"] == "Importo fisso":
                                                    incentivo = premio_scaglione
                                                profitto_generato = valore_totale
                                    else:
                                        # Altri tipi di incentivo
                                        itype = kpi_details["incentive_type"]
                                        premio_base = kpi_details["premio"]
                                        if itype == "Importo fisso":
                                            incentivo = premio_base
                                        elif itype == "% sul risultato":
                                            incentivo = (valore_totale * premio_base) / 100
                                        elif itype == "% sul salario mensile":
                                            incentivo = (emp["salario_mensile"] * premio_base) / 100
                                        elif itype == "Importo fisso x risultato":
                                            incentivo = valore_totale * premio_base
                                        profitto_generato = valore_totale
                                
                                if mese not in incentivi_mensili:
                                    incentivi_mensili[mese] = {"totale_incentivi": 0, "profitto": 0}

                                incentivi_mensili[mese]["totale_incentivi"] += incentivo
                                incentivi_mensili[mese]["profitto"] += profitto_generato

                    # Ora costruiamo la tabella riepilogativa su tutti i mesi trovati
                    mesi_globali = mesi_globali.union(risultati_mensili_global)
                    for m in risultati_mensili_global:
                        inc = incentivi_mensili.get(m, {}).get("totale_incentivi", 0)
                        prof = incentivi_mensili.get(m, {}).get("profitto", 0)
                        stipendio = emp.get("salario_mensile", 0)
                        ppf_mensile = float(emp.get("ppf", 0))
                        totale_compenso = stipendio + inc
                        rapporto_totale_ppf = (totale_compenso / ppf_mensile) * 100 if ppf_mensile else 0

                        riepilogo_completo.append({
                            "Dipendente": emp["name"],
                            "Mese": m,
                            "Stipendio (EUR)": round(stipendio, 2),
                            "Totale Incentivo (EUR)": round(inc, 2),
                            "Compenso Totale (EUR)": round(totale_compenso, 2),
                            "PPF (EUR)": round(ppf_mensile, 2),
                            "Rapporto Compenso/PPF (%)": round(rapporto_totale_ppf, 2)
                        })

                        if prof:
                            ratio = (prof / inc)*100 if inc > 0 else 0
                            profitto_completo.append({
                                "Dipendente": emp["name"],
                                "Mese": m,
                                "Profitto Generato (EUR)": round(prof, 2),
                                "Incentivi Pagati (EUR)": round(inc, 2),
                                "Rapporto Profitto/Incentivi (%)": round(ratio, 2)
                            })
                        else:
                            profitto_completo.append({
                                "Dipendente": emp["name"],
                                "Mese": m,
                                "Profitto Generato (EUR)": 0,
                                "Incentivi Pagati (EUR)": round(inc, 2),
                                "Rapporto Profitto/Incentivi (%)": 0
                            })

                # --------------------------------
                # VISUALIZZAZIONE DATI
                # --------------------------------
                if riepilogo_completo:
                    df_riepilogo = pd.DataFrame(riepilogo_completo)
                    # Ordinamento per Mese e Dipendente
                    df_riepilogo["Mese"] = pd.to_datetime(df_riepilogo["Mese"] + "-01")
                    df_riepilogo = df_riepilogo.sort_values(["Mese", "Dipendente"])
                    df_riepilogo["Mese"] = df_riepilogo["Mese"].dt.strftime("%Y-%m")

                    st.dataframe(df_riepilogo, use_container_width=True)

                    st.write("### Grafico: Totale Compenso per Mese")
                    fig1, ax1 = plt.subplots()
                    # Raggruppiamo per Mese, Dipendente
                    for dip_name in df_riepilogo["Dipendente"].unique():
                        df_temp = df_riepilogo[df_riepilogo["Dipendente"] == dip_name].copy()
                        df_temp["Mese_dt"] = pd.to_datetime(df_temp["Mese"] + "-01")
                        df_temp = df_temp.sort_values("Mese_dt")

                        ax1.plot(
                            df_temp["Mese_dt"], 
                            df_temp["Compenso Totale (EUR)"], 
                            marker="o", 
                            linestyle="-", 
                            label=dip_name
                        )
                    ax1.set_xlabel("Mese")
                    ax1.set_ylabel("Compenso Totale (EUR)")
                    ax1.set_title("Andamento Compenso Totale")
                    plt.xticks(rotation=45)
                    ax1.legend()
                    st.pyplot(fig1)
                else:
                    st.info("Nessun incentivo calcolato per i dipendenti selezionati.")

                if profitto_completo:
                    df_profitto = pd.DataFrame(profitto_completo)
                    df_profitto["Mese"] = pd.to_datetime(df_profitto["Mese"] + "-01")
                    df_profitto = df_profitto.sort_values(["Mese", "Dipendente"])
                    df_profitto["Mese"] = df_profitto["Mese"].dt.strftime("%Y-%m")

                    st.write("### Grafico: Profitto Generato vs Incentivi")
                    st.dataframe(df_profitto, use_container_width=True)

                    fig2, ax2 = plt.subplots()
                    for dip_name in df_profitto["Dipendente"].unique():
                        df_temp = df_profitto[df_profitto["Dipendente"] == dip_name].copy()
                        df_temp["Mese_dt"] = pd.to_datetime(df_temp["Mese"] + "-01")
                        df_temp = df_temp.sort_values("Mese_dt")

                        ax2.plot(
                            df_temp["Mese_dt"], 
                            df_temp["Profitto Generato (EUR)"], 
                            marker="o", 
                            linestyle="-", 
                            label=f"{dip_name} - Profitto"
                        )
                        ax2.plot(
                            df_temp["Mese_dt"], 
                            df_temp["Incentivi Pagati (EUR)"], 
                            marker="s", 
                            linestyle="--", 
                            label=f"{dip_name} - Incentivi"
                        )
                    ax2.set_xlabel("Mese")
                    ax2.set_ylabel("EUR")
                    ax2.set_title("Andamento Profitto e Incentivi")
                    plt.xticks(rotation=45)
                    ax2.legend()
                    st.pyplot(fig2)
                else:
                    st.info("Nessun profitto registrato per i dipendenti selezionati.")


# ----------------------------------------------------------------------------
# GESTIONE DIPENDENTI
# ----------------------------------------------------------------------------
if page == "Gestione Dipendenti":
    st.title("Gestione Dipendenti")
    emp_name = st.text_input("Nome del Dipendente")
    salario_mensile = st.number_input("Salario Mensile (EUR)", min_value=0.0, step=100.0, value=0.0)
    ruolo = st.text_input("Ruolo")
    ppf = st.text_area("Obiettivi Personali (PPF)")

    if st.button("Aggiungi Dipendente") and emp_name:
        emp_id = str(len(data["employees"]) + 1)
        data["employees"][emp_id] = {
            "name": emp_name,
            "salario_mensile": salario_mensile,
            "ruolo": ruolo,
            "ppf": ppf,
            "kpis": {}
        }
        save_data(data)
        st.success("✅ Dati salvati con successo!")
        st.experimental_rerun()

    for emp_id, emp in data["employees"].items():
        with st.expander(f"{emp['name']}"):
            new_name = st.text_input("Nome", emp["name"], key=f"name_{emp_id}")
            new_salario = st.number_input("Salario Mensile (EUR)", min_value=0.0, step=100.0, value=emp.get("salario_mensile", 0.0), key=f"salario_{emp_id}")
            new_ruolo = st.text_input("Ruolo", emp.get("ruolo", ""), key=f"ruolo_{emp_id}")
            new_ppf = st.text_area("Obiettivi Personali (PPF)", emp.get("ppf", ""), key=f"ppf_{emp_id}")

            if st.button("Salva", key=f"save_{emp_id}"):
                emp.update({"name": new_name, "salario_mensile": new_salario, "ruolo": new_ruolo, "ppf": new_ppf})
                save_data(data)
                st.success("✅ Dati salvati con successo!")
                st.experimental_rerun()

            if st.button("Elimina", key=f"del_{emp_id}"):
                del data["employees"][emp_id]
                save_data(data)
                st.success("✅ Dipendente eliminato con successo!")
                st.experimental_rerun()

# ----------------------------------------------------------------------------
# GESTIONE KPI
# ----------------------------------------------------------------------------
if page == "Gestione KPI":
    st.title("⚙️ Gestione KPI")

    emp_list = list(data["employees"].keys())
    if emp_list:
        selected_emp = st.selectbox(
            "👤 Seleziona Dipendente", 
            emp_list, 
            format_func=lambda x: data["employees"].get(x, {}).get("name", "Sconosciuto")
        )
        emp = data["employees"].get(selected_emp, {})
        
        if "kpis" not in emp:
            emp["kpis"] = {}

        st.subheader(f"📊 Gestione KPI per {emp.get('name', 'Sconosciuto')}")

        kpi_updates = []

        for kpi_name, kpi_details in emp["kpis"].items():
            with st.expander(f"⚙️ KPI: {kpi_name}"):
                opzioni_incentivo = [
                    "Importo fisso", 
                    "% sul risultato", 
                    "% sul salario mensile", 
                    "Importo fisso x risultato", 
                    "Scaglioni"
                ]

                incentive_type = st.selectbox(
                    "📌 Tipo di Incentivo",
                    opzioni_incentivo,
                    index=opzioni_incentivo.index(kpi_details.get("incentive_type", "Importo fisso")),
                    key=f"incentivo_{kpi_name}"
                )

                risultato_minimo = st.number_input(
                    "📊 Risultato minimo per attivare l'incentivo",
                    min_value=0.0,
                    step=1.0,
                    value=float(kpi_details.get("risultato_minimo", 0)),
                    key=f"risultato_minimo_{kpi_name}"
                )

                premio = st.number_input(
                    "💰 Valore Incentivo (o percentuale)",
                    min_value=0.0,
                    step=10.0,
                    value=float(kpi_details.get("premio", 0)),
                    key=f"premio_{kpi_name}"
                )

                usa_scaglioni = st.checkbox(
                    "📈 Attiva gestione a scaglioni",
                    value=bool(kpi_details.get("scaglioni", [])),
                    key=f"scaglioni_{kpi_name}"
                )

                scaglioni_modificati = []
                if usa_scaglioni:
                    num_scaglioni = st.number_input(
                        "📊 Numero di Scaglioni",
                        min_value=1,
                        step=1,
                        value=max(1, len(kpi_details.get("scaglioni", []))),
                        key=f"num_scaglioni_{kpi_name}"
                    )
                    scaglioni_correnti = kpi_details.get("scaglioni", [])
                    if len(scaglioni_correnti) < num_scaglioni:
                        scaglioni_correnti += [(0, 0, 0)] * (num_scaglioni - len(scaglioni_correnti))
                    scaglioni_correnti = scaglioni_correnti[:num_scaglioni]

                    for i in range(num_scaglioni):
                        col1, col2, col3 = st.columns(3)

                        soglia = col1.number_input(
                            f"Soglia {i+1}", 
                            min_value=0.0, 
                            step=1.0,
                            value=float(scaglioni_correnti[i][0]),
                            key=f"soglia_{kpi_name}_{i}"
                        )

                        premio_scaglione = col2.number_input(
                            f"Premio {i+1}", 
                            min_value=0.0, 
                            step=1.0,
                            value=float(scaglioni_correnti[i][1]),
                            key=f"premio_scaglione_{kpi_name}_{i}"
                        )

                        incentivo_scaglione = col3.number_input(
                            f"Incentivo {i+1} (%)", 
                            min_value=0.0, 
                            step=1.0,
                            value=float(scaglioni_correnti[i][2]),
                            key=f"incentivo_scaglione_{kpi_name}_{i}"
                        )

                        scaglioni_modificati.append((soglia, premio_scaglione, incentivo_scaglione))

                # Elimina KPI
                if st.button(f"❌ Elimina KPI {kpi_name}", key=f"del_kpi_{kpi_name}"):
                    del emp["kpis"][kpi_name]
                    save_data(data)
                    st.success(f"✅ KPI {kpi_name} eliminato con successo!")
                    st.experimental_rerun()

                # Salva Modifiche
                if st.button("✅ Salva Modifiche", key=f"save_kpi_{kpi_name}"):
                    emp["kpis"][kpi_name] = {
                        "incentive_type": incentive_type,
                        "risultato_minimo": risultato_minimo,
                        "premio": premio,
                        "scaglioni": scaglioni_modificati if usa_scaglioni else []
                    }
                    save_data(data)

                    kpi_updates.append({
                        "KPI": kpi_name,
                        "Tipo Incentivo": incentive_type,
                        "Risultato Minimo": risultato_minimo,
                        "Premio": premio,
                        "Scaglioni Attivi": "Sì" if usa_scaglioni else "No",
                        "Numero Scaglioni": len(scaglioni_modificati) if usa_scaglioni else 0
                    })

                    st.success(f"✅ Modifiche salvate per {kpi_name}!")
                    st.experimental_rerun()

        if kpi_updates:
            st.write("### 📋 Modifiche Salvate nei KPI")
            df_updates = pd.DataFrame(kpi_updates)
            st.dataframe(df_updates, use_container_width=True)

        # Sezione per creare un nuovo KPI
        st.subheader("Aggiungi Nuovo KPI")
        new_kpi_name = st.text_input("Nome KPI")

        new_incentive_type = st.selectbox(
            "Tipo di Incentivo",
            ["Importo fisso", "% sul risultato", "% sul salario mensile", "Importo fisso x risultato"],
            key="new_incentive_type"
        )

        new_risultato_minimo = st.number_input(
            "Risultato Minimo",
            min_value=0.0,
            step=1.0,
            key="new_risultato_minimo"
        )

        new_premio = st.number_input("Valore Incentivo (o %)", min_value=0.0, step=10.0, key="new_premio")

        usa_scaglioni_new = st.checkbox("Attiva gestione a scaglioni", key="scaglioni_new")
        new_scaglioni = []
        if usa_scaglioni_new:
            num_scaglioni_new = st.number_input("Numero di Scaglioni", min_value=1, step=1, key="num_scaglioni_new")
            for i in range(num_scaglioni_new):
                col1, col2 = st.columns(2)
                soglia = col1.number_input(f"Soglia {i+1}", min_value=0.0, step=1.0, key=f"soglia_new_{i}")
                premio_scaglione = col2.number_input(f"Premio {i+1}", min_value=0.0, step=1.0, key=f"premio_scaglione_new_{i}")
                new_scaglioni.append((soglia, premio_scaglione, 0))  # Se vuoi anche la % puoi aggiungere un terzo input

        if st.button("Aggiungi KPI") and new_kpi_name:
            if "kpis" not in emp:
                emp["kpis"] = {}

            emp["kpis"][new_kpi_name] = {
                "incentive_type": new_incentive_type,
                "risultato_minimo": new_risultato_minimo,
                "premio": new_premio,
                "scaglioni": new_scaglioni if usa_scaglioni_new else []
            }
            save_data(data)
            st.success("✅ KPI aggiunto con successo!")
            st.experimental_rerun()

# ----------------------------------------------------------------------------
# INSERIMENTO RISULTATI
# ----------------------------------------------------------------------------
if page == "Inserimento Risultati":
    st.title("📅 Inserimento Risultati KPI")

    selected_emp = st.selectbox(
        "👤 Seleziona Dipendente", 
        list(data["employees"].keys()), 
        format_func=lambda x: data["employees"].get(x, {}).get("name", "Sconosciuto")
    )
    emp = data["employees"].get(selected_emp, {})

    if "kpis" not in emp:
        emp["kpis"] = {}

    if emp:
        kpi_list = list(emp["kpis"].keys())
        if kpi_list:
            selected_kpi = st.selectbox("📊 Seleziona KPI", kpi_list)

            data_risultato = st.date_input("📆 Data")
            valore_raggiunto = st.number_input("📊 Risultato ottenuto", min_value=0.0, step=1.0)

            kpi_details = emp["kpis"][selected_kpi]
            if "storico_risultati" not in kpi_details:
                kpi_details["storico_risultati"] = []
            
            date_list = [r["data"] for r in kpi_details["storico_risultati"]]

            if str(data_risultato) in date_list:
                st.warning("⚠️ Esiste già un valore per questa data. Modifica il valore nella tabella sottostante.")
            else:
                if st.button("✅ Salva Risultato"):
                    kpi_details["storico_risultati"].append({
                        "data": str(data_risultato),
                        "valore_raggiunto": valore_raggiunto
                    })
                    save_data(data)
                    st.success(f"✅ Risultato per **{selected_kpi}** salvato con successo!")
                    st.experimental_rerun()

            if "storico_risultati" in kpi_details and kpi_details["storico_risultati"]:
                st.write("### 📋 Riepilogo Risultati")
                df = pd.DataFrame(kpi_details["storico_risultati"])
                df["data"] = pd.to_datetime(df["data"])
                df = df.sort_values("data", ascending=False)

                # Se la tua versione di Streamlit NON supporta st.data_editor(), sostituisci con st.dataframe()
                edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

                if not df.equals(edited_df):
                    emp["kpis"][selected_kpi]["storico_risultati"] = edited_df.to_dict(orient="records")
                    save_data(data)
                    st.success("✅ Modifiche salvate con successo!")
                    st.experimental_rerun()

                st.write("### ❌ Elimina un Risultato")
                selected_index = st.selectbox("Seleziona la data da eliminare", df["data"].astype(str).tolist())

                if st.button("❌ Elimina Risultato"):
                    emp["kpis"][selected_kpi]["storico_risultati"] = [
                        r for r in kpi_details["storico_risultati"] if str(r["data"]) != selected_index
                    ]
                    save_data(data)
                    st.success("✅ Risultato eliminato con successo!")
                    st.experimental_rerun()
        else:
            st.warning("⚠️ Nessun KPI assegnato a questo dipendente.")

#  ----------------------------------------------------------------------------
# PAGINA: REPORT E ANALISI
# ----------------------------------------------------------------------------

if page == "Report e Analisi":
    st.title("📊 Report e Analisi Incentivi Mensili")

    selected_emp = st.selectbox(
        "👤 Seleziona Dipendente", 
        list(data["employees"].keys()), 
        format_func=lambda x: data["employees"].get(x, {}).get("name", "Sconosciuto")
    )
    emp = data["employees"].get(selected_emp, {})

    if "kpis" not in emp:
        emp["kpis"] = {}

    if emp:
        incentivi_mensili = {}

        # Calcoliamo gli incentivi
        for kpi_name, kpi_details in emp["kpis"].items():
            if "storico_risultati" in kpi_details:
                risultati_mensili = {}

                for entry in kpi_details["storico_risultati"]:
                    mese = entry["data"][:7]
                    valore = entry["valore_raggiunto"]

                    if mese not in risultati_mensili:
                        risultati_mensili[mese] = 0
                    risultati_mensili[mese] += valore

                for mese, valore_totale in risultati_mensili.items():
                    incentivo = 0
                    calcolo_dettagliato = []
                    valore_minimo = kpi_details.get("risultato_minimo", 0)

                    if valore_totale >= valore_minimo:
                        if kpi_details.get("scaglioni", []):
                            scaglioni_corretto = [
                                (s[0], s[1], s[2] if len(s) > 2 else 0) 
                                for s in kpi_details["scaglioni"]
                            ]
                            for soglia, premio_scaglione, percentuale_scaglione in sorted(scaglioni_corretto, key=lambda x: x[0]):
                                if valore_totale >= soglia:
                                    if kpi_details["incentive_type"] == "% sul risultato":
                                        incentivo = (valore_totale * percentuale_scaglione) / 100
                                        calcolo_dettagliato.append(f"{valore_totale} × {percentuale_scaglione}% = {incentivo} EUR")
                                    elif kpi_details["incentive_type"] == "% sul salario mensile":
                                        incentivo = (emp["salario_mensile"] * percentuale_scaglione) / 100
                                        calcolo_dettagliato.append(f"{emp['salario_mensile']} × {percentuale_scaglione}% = {incentivo} EUR")
                                    elif kpi_details["incentive_type"] == "Importo fisso":
                                        incentivo = premio_scaglione
                                        calcolo_dettagliato.append(f"Incentivo fisso per soglia {soglia}: {incentivo} EUR")
                                    # Eventualmente gestisci "Importo fisso x risultato" con scaglioni, se necessario
                        else:
                            if kpi_details["incentive_type"] == "Importo fisso x risultato":
                                incentivo = valore_totale * kpi_details["premio"]
                                calcolo_dettagliato.append(f"{valore_totale} × {kpi_details['premio']} = {incentivo} EUR")
                            elif kpi_details["incentive_type"] == "Importo fisso":
                                incentivo = kpi_details["premio"]
                                calcolo_dettagliato.append(f"Incentivo fisso: {incentivo} EUR")
                            elif kpi_details["incentive_type"] == "% sul risultato":
                                incentivo = (valore_totale * kpi_details["premio"]) / 100
                                calcolo_dettagliato.append(f"{valore_totale} × {kpi_details['premio']}% = {incentivo} EUR")
                            elif kpi_details["incentive_type"] == "% sul salario mensile":
                                incentivo = (emp["salario_mensile"] * kpi_details["premio"]) / 100
                                calcolo_dettagliato.append(f"{emp['salario_mensile']} × {kpi_details['premio']}% = {incentivo} EUR")
                    else:
                        calcolo_dettagliato.append(f"❌ Valore sotto soglia minima {valore_minimo}, nessun incentivo.")

                    if mese not in incentivi_mensili:
                        incentivi_mensili[mese] = {}

                    incentivi_mensili[mese][kpi_name] = {
                        "totale": incentivo,
                        "dettaglio": "\n".join(calcolo_dettagliato),
                        "valore_raggiunto": valore_totale
                    }

        # Mostriamo i risultati in ordine dal mese più recente al più vecchio
        if incentivi_mensili:
            st.write("### 📆 Incentivi Mensili per KPI")
            mesi_ordinati = sorted(incentivi_mensili.keys(), reverse=True)

            for mese in mesi_ordinati:
                kpi_data = incentivi_mensili[mese]
                totale_incentivi_mese = sum(info["totale"] for info in kpi_data.values() if isinstance(info, dict))
                st.subheader(f"📅 Mese: {mese}  (Totale Incentivi = {round(totale_incentivi_mese,2)} EUR)")

                for kpi_name, info in kpi_data.items():
                    with st.expander(f"📊 KPI: {kpi_name} - Incentivo Totale: {info['totale']} EUR"):
                        st.write(f"**Valore Totale Raggiunto:** {info['valore_raggiunto']}")
                        st.write("### 🔍 Dettaglio Calcolo:")
                        st.write(info["dettaglio"])

        # Dopo aver calcolato "incentivi_mensili" e prima della sezione che mostra i grafici:
        st.write("## Genera Riepilogo Mensile in PDF")

        # Ricaviamo la lista dei mesi con dati (es. 2023-07, 2023-08, ...)
        all_months = sorted(incentivi_mensili.keys())
        if all_months:
            selected_month = st.selectbox("Scegli il mese per generare il PDF", all_months)

            if st.button("Genera Riepilogo Mensile PDF"):
                pdf = genera_pdf_report_mensile_singolo_dipendente(emp, selected_month, incentivi_mensili)
                pdf_filename = f"Riepilogo_{emp['name']}_{selected_month}.pdf"
                pdf.output(pdf_filename)
        
                with open(pdf_filename, "rb") as f:
                    st.download_button("📥 Scarica PDF del Riepilogo Mensile", f, file_name=pdf_filename)
        else:
            st.info("Non ci sono mesi disponibili per generare il PDF in questo momento.")


            # Grafici KPI
            st.write("### 📈 Andamento Incentivi e Risultati per KPI")
            for kpi_name in emp["kpis"].keys():
                dati_kpi = {"Mese": [], "Incentivo (EUR)": [], "Valore Raggiunto": []}
                mesi_tutti = sorted(incentivi_mensili.keys())

                for mese in mesi_tutti:
                    if kpi_name in incentivi_mensili[mese]:
                        dati_kpi["Mese"].append(mese)
                        dati_kpi["Incentivo (EUR)"].append(incentivi_mensili[mese][kpi_name]["totale"])
                        dati_kpi["Valore Raggiunto"].append(incentivi_mensili[mese][kpi_name]["valore_raggiunto"])

                if dati_kpi["Mese"]:
                    df_kpi = pd.DataFrame(dati_kpi)
                    df_kpi["Mese_dt"] = pd.to_datetime(df_kpi["Mese"] + "-01", format="%Y-%m-%d")
                    df_kpi = df_kpi.sort_values("Mese_dt")

                    fig, ax = plt.subplots()
                    ax.plot(df_kpi["Mese_dt"], df_kpi["Valore Raggiunto"], marker="o", linestyle="-", label="Valore Raggiunto")
                    ax.plot(df_kpi["Mese_dt"], df_kpi["Incentivo (EUR)"], marker="s", linestyle="--", label="Incentivo (EUR)")
                    ax.set_ylabel("Valori e Incentivi")
                    ax.set_xlabel("Mese")
                    ax.set_title(f"Andamento KPI - {kpi_name}")
                    plt.xticks(rotation=45)
                    ax.legend()
                    st.pyplot(fig)
                else:
                        st.warning("⚠️ Nessun incentivo calcolato per questo dipendente.")

