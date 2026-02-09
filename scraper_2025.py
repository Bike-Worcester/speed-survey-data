import pandas as pd
import re
import os
import math
from pathlib import Path
import warnings

# Suppress openpyxl warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

def parse_2025_speed_sheet(file_path):
    # Load the specific 'Data' sheet
    df = pd.read_excel(file_path, sheet_name="Data", header=None, dtype=str)
    df = df.fillna("").map(lambda x: str(x).strip())
    
    # Metadata extraction
    road_name = os.path.basename(file_path).replace(".xlsx", "")
    lat, lon = None, None
    speed_limit = None
    start_date, end_date = None, None

    clean_road_name = re.sub(r'^\d{8}\s+', '', road_name).strip()

    # Scan the first 20 rows for metadata (Road name, Lat/Lng, Limit, Dates)
    for i, row in df.iloc[:20].iterrows():
        row_text = " ".join(row)

        # Lat/Lng
        if "Lat/Lng" in row_text:
            match = re.search(r"Lat/Lng.*?([-+]?\d+\.\d+)[^\d-]+([-+]?\d+\.\d+)", row_text, re.IGNORECASE)
            if match:
                lat, lon = map(float, match.groups())

        # Speed limit
        if "Speed Limit" in row_text:
            match = re.search(r"Speed Limit (\d+)", row_text)
            if match:
                speed_limit = int(match.group(1))

        # Dates
        if "From" in row_text and "To" in row_text:
            match = re.search(r"From (\d{2}/\d{2}/\d{4}) To (\d{2}/\d{2}/\d{4})", row_text)
            if match:
                start_date, end_date = match.group(1), match.group(2)

    # --- Find the THIRD table (Bin headers) ---
    bin_header_indices = []
    for i, row in df.iterrows():
        if any(re.match(r"Bin \d+", str(cell)) for cell in row):
            bin_header_indices.append(i)
    
    if len(bin_header_indices) < 3:
        print(f"Warning: Could not find 3 tables in {file_path}. Found {len(bin_header_indices)}.")
        return []

    # Target the 3rd table index
    header_row_index = bin_header_indices[2] 
    header_row = df.iloc[header_row_index]
    
    # Identify bin columns
    bin_cols = [col for col in df.columns if re.match(r"Bin \d+", str(header_row[col]))]
    
    output = []
    # Iterate from the 3rd table's header downwards
    for _, row in df.iloc[header_row_index + 1:].iterrows():
        first_col = row.iloc[0]
        
        # Stop if we hit the end of this table
        if first_col.lower().startswith("total") or first_col == "nan" or first_col == "":
            break
            
        for col_idx in bin_cols:
            val = row.iloc[col_idx]
            if val != "" and val != "nan":
                output.append({
                    "road_name": clean_road_name,
                    "limit": speed_limit,
                    "speed_bin": header_row[col_idx],
                    "time": first_col,
                    "value": float(val),
                    "lat": lat, 
                    "lon": lon,
                    "start_date": start_date,
                    "end_date": end_date
                })
    return output

def create_speed_bins_labels(odf):
    if odf.empty: return odf
    
    # Clean the bin strings
    odf["speed_bin"] = odf["speed_bin"].str.replace(r"^Bin\s+\d+\n", "", regex=True)
    odf["speed_bin"] = odf["speed_bin"].str.replace("MPH", "", regex=False)

    # Extract Min/Max
    range_df = odf["speed_bin"].str.extract(r"(?P<speed_min>\d+)\s*-\s*<\s*(?P<speed_max>\d+)")
    lt_df = odf["speed_bin"].str.extract(r"(?<!=>)<\s*(?P<speed_max>\d+)")
    lt_df["speed_min"] = 0
    gt_df = odf["speed_bin"].str.extract(r"=>\s*(?P<speed_min>\d+)")
    gt_df["speed_max"] = pd.NA
    
    # Combine
    odf["speed_min"] = range_df["speed_min"].combine_first(gt_df["speed_min"]).combine_first(lt_df["speed_min"])
    odf["speed_max"] = range_df["speed_max"].combine_first(lt_df["speed_max"]).combine_first(gt_df["speed_max"])

    return odf

# --- Execution ---
data_2025_dir = Path("raw_data/2025")
locations_2025 = []

if data_2025_dir.exists():
    for file in data_2025_dir.glob("*.xlsx"):
        print(f"Processing 2025 file: {file.name}")
        try:
            data = parse_2025_speed_sheet(file)
            locations_2025.extend(data)
        except Exception as e:
            print(f"Error processing {file.name}: {e}")

if locations_2025:
    odf_2025 = pd.DataFrame(locations_2025)
    #odf_2025 = create_speed_bins_labels(odf_2025)
    
    # Ensure output directory exists
    output_path = Path("raw_data")
    output_path.mkdir(parents=True, exist_ok=True)
    
    odf_2025.to_csv(output_path / 'speed_data_2025_raw.csv', index=False)
    print("Done! Preview:")
    print(odf_2025.head())
else:
    print("No data extracted.")
