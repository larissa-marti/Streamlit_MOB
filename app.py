import streamlit as st
import pandas as pd
import os
import xlsxwriter
from io import BytesIO

# Seitentitel
st.title("Umformatierung MOB-Daten")

# Uploader
uploaded_file = st.file_uploader("Lade eine .txt Datei hoch", type=["txt"])

if uploaded_file:
  # Umwandlung des hochgeladenen Files in ein df
  df = pd.read_csv(uploaded_file, sep=';')
  
  # didok einlesen (im Repo abgelegt)
  didok = pd.read_csv('didok.csv', encoding='utf-8', sep=';')
  
  # Führende Nullen aus BPNUMBER[5] und numberShort entfernen
  df['BPNUMBER_clean'] = df['BPNUMBER[5]'].astype(str).str.lstrip('0')
  didok['numberShort_clean'] = didok['numberShort'].astype(str).str.lstrip('0')
  
  # Merge basierend auf beiden Bedingungen: BPUIC[2] == uicCountryCode und BPNUMBER_clean == numberShort_clean
  df = df.merge(
      didok[['numberShort_clean', 'uicCountryCode', 'abbreviation']],
      left_on=['BPNUMBER_clean', 'BPUIC[2]'],
      right_on=['numberShort_clean', 'uicCountryCode'],
      how='left'
  )
  
  # Unnötige Spalten löschen
  df.drop(columns=['BPNUMBER_clean', 'numberShort_clean', 'Unnamed: 17', 'uicCountryCode', 'ABKURZBP[5]'], inplace=True)
  
  # Spalten umbenennen
  df.rename(columns={'abbreviation': 'ABKURZBP[5]', '#ZUGNUMMERSCHEMA[3]': 'ZUGNUMMERSCHEMA[3]'}, inplace=True)
  
  # Datum auf drei Spalten aufteilen
  df['DATUM[8]'] = df['DATUM[8]'].astype(str)  # Sicherstellen, dass die Spalte als String vorliegt
  
  # Jahr, Monat und Tag extrahieren
  df['Jahr'] = df['DATUM[8]'].str[:4]   # Die ersten 4 Zeichen für das Jahr
  df['Monat'] = df['DATUM[8]'].str[4:6] # Zeichen 5-6 für den Monat
  df['Tag'] = df['DATUM[8]'].str[6:8]   # Zeichen 7-8 für den Tag
  df[['Jahr', 'Monat', 'Tag']] = df[['Jahr', 'Monat', 'Tag']].astype(int)
  df.drop(columns=['DATUM[8]'], inplace=True)
  
  # Die Spaltennamen in eine Liste extrahieren
  columns = list(df.columns)
  
  # Die neuen Spalten (Jahr, Monat, Tag) an die gewünschten Positionen verschieben
  new_order = columns[:2] + ['Jahr', 'Monat', 'Tag'] + columns[2:-3]  # Index 2, 3 und 4
  
  # DataFrame neu sortieren
  df = df[new_order]
  
  # Zugnummern des Debi 7022 löschen
  # Liste der Zahlen, die ausgeschlossen werden sollen
  zu_loeschende_zugnummern = [4056, 4058, 4059, 4060, 4061, 4062, 4063, 4070, 4073, 4076, 4081, 4083]
  
  # Bedingung: ZUGNUMMER_NEW[6] enthält entweder die genannten Zahlen oder eine dieser Zahlen + 70000
  bedingung = df['ZUGNUMMER_NEW[6]'].isin(zu_loeschende_zugnummern) | df['ZUGNUMMER_NEW[6]'].isin([x + 70000 for x in zu_loeschende_zugnummern])
  
  # Zeilen löschen, die die Bedingung erfüllen
  df = df[~bedingung].reset_index(drop=True)


  # Speichern des verarbeiteten Excels
  # Originaldateiname ohne Endung
  base_filename = os.path.splitext(uploaded_file.name)[0]

  # Datei-Exportfunktion
  def convert_to_excel(df):
      output = BytesIO()
      with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
          df.to_excel(writer, index=False, sheet_name="Sheet1")

          # Zugriff auf das Arbeitsblatt
          worksheet = writer.sheets["Sheet1"]

          # Spaltenbreiten anpassen
          for col_num, column_title in enumerate(df.columns):
              column_width = max(len(str(column_title)) + 2, 10)  # Mindestbreite 10
              worksheet.set_column(col_num, col_num, column_width)

          writer.close()

      output.seek(0)  # Wichtiger Schritt, um den Puffer auf den Anfang zu setzen
      return output

  # Datei exportieren
  excel_data = convert_to_excel(df)


  # Download-Button
  st.download_button("Download als Excel", data=excel_data, file_name=base_filename + '.xlsx')

