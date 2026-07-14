import os
import urllib.request
import zipfile
import io
import pandas as pd
import sqlite3

def download_and_stage_full_data():
    """
    Step 1: Enterprise-Scale Extract & Load Pipeline
    Downloads the complete historical archive from Cricsheet and loops
    through every single historical IPL match file to build a massive warehouse.
    """
    print("🚀 Step 1: Starting Enterprise Bulk Data Ingestion...")
    
    RAW_DATA_DIR = os.path.join("data", "1_raw")
    PROCESSED_DATA_DIR = os.path.join("data", "2_processed")
    DB_PATH = os.path.join(PROCESSED_DATA_DIR, "cricket_analytics.db")
    
    CRICSHEET_URL = "https://cricsheet.org/downloads/ipl_csv2.zip"
    
    # --- FETCH & DOWNLOAD ARCHIVE ---
    print("📥 Connecting to Cricsheet to fetch the full historical IPL database...")
    try:
        response = urllib.request.urlopen(CRICSHEET_URL)
        zip_data = zipfile.ZipFile(io.BytesIO(response.read()))
        print("✅ Archive successfully loaded into system memory.")
    except Exception as e:
        print(f"❌ Network connection failed. Error: {e}")
        return

    # --- FILTER VALID MATCH FILES ---
    csv_files = [f for f in zip_data.namelist() if f.endswith('.csv') and not f.endswith('_info.csv')]
    total_matches = len(csv_files)
    print(f"📦 Total historical matches discovered in archive: {total_matches}")
    
    # --- FULL SCALE PROCESSING LOOP ---
    print(f"⏳ Bulk ingesting ALL {total_matches} matches into SQL Staging Layer...")
    
    conn = sqlite3.connect(DB_PATH)
    
    # Optimization: Speed up batch execution by turning off sync constraints temporarily
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("PRAGMA journal_mode = MEMORY")
    
    for idx, match_file in enumerate(csv_files):
        with zip_data.open(match_file) as f:
            df_match = pd.read_csv(f)
            
        df_match.columns = df_match.columns.str.strip().str.replace(' ', '_').str.lower()
        
        # Write to SQL: Replace on the first iteration, append for all others
        if idx == 0:
            df_match.to_sql('raw_deliveries', conn, if_exists='replace', index=False)
            
            # Save a single raw match sample onto disk for record keeping
            raw_output_path = os.path.join(RAW_DATA_DIR, match_file)
            with open(raw_output_path, 'wb') as f_out:
                f_out.write(zip_data.read(match_file))
        else:
            df_match.to_sql('raw_deliveries', conn, if_exists='append', index=False)
            
        # Log progression checkpoints every 100 matches
        if (idx + 1) % 100 == 0:
            print(f"|--- Progress Checkpoint: Ingested {idx + 1}/{total_matches} matches...")

    conn.close()
    print("🎉 Step 1 Complete: Entire historical IPL dataset warehouse-staged!")

if __name__ == "__main__":
    download_and_stage_full_data()