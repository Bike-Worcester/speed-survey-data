
import pandas as pd
import re
from pathlib import Path
import json

#vehicles per hour speeding during 7 til 7pm
# % veichles speeding during 7 til 7pm

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


def parse_speed_sheet(excel_file, sheet_name):
    # Load sheet without headers
    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None, dtype=str)

    # Convert all cells to string and strip whitespace

    df = df.fillna("").map(lambda x: str(x).strip())
    # --- 1. Extract metadata ---
    road_name = None
    speed_limit = None
    lat, lon = None, None
    start_date, end_date = None, None

    for i, row in df.iterrows():
        row_text = " ".join(row)

        # Road name: usually row after Site No. / Site Ref.
        if re.search(r"^[Uu]\d+", row[0]):
            road_name = row[0] if row[0] else row[1]

        # Lat/Lng
        if "Lat/Lng" in row_text:
            match = re.search(
                r"Lat/Lng.*?([-+]?\d+\.\d+)[^\d-]+([-+]?\d+\.\d+)",
                row_text,
                re.IGNORECASE
    )

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

    # --- 2. Find header row for bins ---
    header_row_index = None
    for i, row in df.iterrows():
        if any(re.match(r"Bin \d+", str(cell)) for cell in row):
            header_row_index = i
            break

    if header_row_index is None:
        raise ValueError("Could not find bin header row.")

    # Bin columns
    header_row = df.iloc[header_row_index]
    bin_cols = [col for col in df.columns if re.match(r"Bin \d+", str(header_row[col]))]
    #create a blank dataframe with columns: road_name, lat, lon, speed_bin, time, value
    output = []

    # --- 3. Aggregate distribution ---
    distribution = [0] * len(bin_cols)
    for _, row in df.iloc[header_row_index + 1:].iterrows():
        first_col = row.iloc[0]
        if first_col.lower().startswith("total") or first_col == "":
            break
        for i, col in enumerate(bin_cols):
            val = row.iloc[col]
            if val != "":
                distribution[i] += float(val)
                output.append({
                    "road_name": sheet_name,
                    "limit": speed_limit,
                    "speed_bin": header_row[bin_cols[i]],
                    "time": first_col,
                    "value": float(val),
                    "lat":lat, 
                    "lon": lon,
                    "start_date": start_date,
                    "end_date": end_date
                })
    
    total_volume = sum(distribution)

    return output

    # return {
    #     "name": road_name if road_name else sheet_name,
    #     "lat": lat,
    #     "lon": lon,
    #     "limit": speed_limit if speed_limit else 0,
    #     "dates": {"start": start_date, "end": end_date},
    #     "distribution": distribution,
    #     "total_volume": total_volume
    # }

def create_speed_bins_labels(odf):
    odf["speed_bin"] = odf["speed_bin"].str.replace(r"^Bin\s+\d+\n", "", regex=True)
    
    odf["speed_bin"] = odf["speed_bin"].str.replace("MPH", "", regex=False)

    range_df = odf["speed_bin"].str.extract(
    r"(?P<speed_min>\d+)\s*-\s*<\s*(?P<speed_max>\d+)"
    )


    lt_df = odf["speed_bin"].str.extract(
        r"(?<!=>)<\s*(?P<speed_max>\d+)"
    )
    lt_df["speed_min"] = 0
    
    gt_df = odf["speed_bin"].str.extract(
        r"=>\s*(?P<speed_min>\d+)"
    )
    gt_df["speed_max"] = pd.NA
    

    odf["speed_min"] = (
        range_df["speed_min"]
        .combine_first(gt_df["speed_min"])
        .combine_first(lt_df["speed_min"])
    )

    odf["speed_max"] = (
        range_df["speed_max"]
        .combine_first(lt_df["speed_max"])
        .combine_first(gt_df["speed_max"])
    )

    return odf

# Example usage
if __name__ == "__main__":
    excel_file = "raw_data/Worcestershire Traffic Data - Master.xlsx"

    # get sheet names
    sheets  = ['2024 Oldbury Rd', 
               '2024 Merrimans Hill Rd', 
               '2024 Hallow Rd', 
               '2024 Henwick Rd (St Clements)', 
               '2024 Millwood Dr', 
               '2024 Plantation Dr', 
               '2024 Hastings Dr', 
               '2024 Dugdale Dr', 
               '2024 Bromwich Rd', 
               '2024 Tolladine Rd (2)', 
               '2024 Thornloe Rd', 
               '2024 Stephenson Rd', 
               '2024 Cantebury Rd', 
               '2024 Swinesherd Way', 
               '2024 Bath Road (2)', 
               '2024 Hollymount', 
               '2024 Tolladine Rd', 
               '2024 Drake Av', 
               '2024 Tudor Way', 
               '2024 Bath Rd', 
               '2024 Droitwich Rd (S)', 
               '2024 Droitwich Rd (N)', 
'2024 John Comyn Dr', 
'2024 Grenville Rd', 
'2024 London Rd (N)', 
'2024 London Rd (S)', 
'2022 Diglis Rd (Angel)', 
'2022 Diglis Rd', 
'2024 Tunnel Hill', 
'2024 Wylds Lane', 
'2024 Astwood Rd', 
'2024 Fort Royal Hill', 
'2024 Park St', 
'2024 Belmont St', 
'2023 Vincent Rd', 
'2023 Comer Rd', 
'2023 Hindlip Lane', 
'2023 Stanley Rd', 
'2023 143 Tudor Way', 
'2023 45 Tudor Way', 
'2023 4 Barneshall Av', 
'2023 Pope Iron Rd', 
'2023 Bransford Rd (2)', 
'2023 Newtown Rd', 
'2023 Henwick Rd', 
'2023 Raglan St', 
'2023 Worcester Rd (north)', 
'2023 Worcester Rd (south)', 
'2023 Fairburn Av', 
'2023 Lowesmoor', 
'2023 Windsor Av', 
'St Peters Dr', 
'2023 69 Timberdine Av', 
'2023 21 Timberdine Av', 
'2023 Cranham Dr', 
'2023 Fort Royal Hill', 
'2023 Ombersley Rd', 
'2023 180 Astwood Rd', 
'2023 Astwood Rd', 
'2023 Bilford Rd', 
'2023 Thornloe Walk', 
'2023 60 Spetchley Rd', 
'2023 Lansdowne Cr', 
'2023 Elbury Park Rd', 
'2023 Windermere Dr', 
'2023 120 Henwick Rd', 
'2023 97 Henwick Rd', 
'2023 Canada Way', 
'2023 Astwood Rd (cem)', 
'2023 New Bank', 
'2023 St Peters Dr 2', 
'2023 Drovers Way', 
'2023 Bath Rd - Aldi', 
'2023 Laugherne Rd', 
'2023 Cranham Drive', 
'2023 74 Bransford Rd', 
'2023 Malvern Rd', 
'2023 Swinton Lane', 
'2023 Bransford Rd', 
'2022 Norton Rd (2)', 
'2022 Foregate St', 
'2022 Foregate St (Station)', 
'2022 St Marks Cl', 
'2022 Norton Rd (E of Ald)', 
'2022 Winchester Av', 
'2022 Malvern Rd, LW (S)', 
'2022 Malvern Rd, LW (N)', 
'2022 Tetbury Dr', 
'2022 Park St', 
'2022 Solitaire Ave', 
'2022 Tennis Walk', 
'2022 Woodstock Rd', 
'2022 Ashley Rd', 
'2022 Norton Rd', 
'2022 Chestnut Walk', 
'2022 Plimsoll Rd', 
'2022 Medway Rd', 
'2022 Perdiswell St',
'2022 Newcastle Cl', 
'2022 Chelmsford Dr', 
'2022 Liverpool Rd', 
'2022 Cantebury Rd (108)', 
'2022 Cantebury Rd (132)', 
'2022 Kilbury Rd', 
'2022 Canada Way', 
'2022 Waverley St', 
'2022 Foley Rd', 
'2022 Diglis Rd (north)', 
'2022 Diglis Rd (basin)', 
#'2011 Hylton Road', 
#'2016 Henwick Rd (79)', 
'2016 Henwick Rd (petrol)', 
'2019 Hylton Rd', 
'2020 Henwick Rd (school)', 
'2021 Droitwich Rd', 
'2022 Bath Rd', 
'2022 Brickfields Rd', 
'2022 Bromwich Rd', 
'2022 Gresham Rd', 
'2022 Henwick Rd', 
'2022 Henwick Rd 2', 
'2022 Hylton Rd', 
'2022 Lansdowne Rd', 
'2022 Laugherne Rd', 
'2022 London Rd', 
'2022 Oldbury Rd', 
'2022 Tolladine Rd (260)', 
'2022 Tolladine Rd (181)', 
'2022 Woodgreen Dr']

import math

def is_valid_lat_lon(lat, lon):
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return False

    if math.isnan(lat) or math.isnan(lon):
        return False

    return -90 <= lat <= 90 and -180 <= lon <= 180

locations = []

for sheet in sheets:
    print("Processing sheet: ", sheet)
    location_data = parse_speed_sheet(excel_file, sheet)
    # if not is_valid_lat_lon(location_data.get("lat"), location_data.get("lon")):
    #     print(f"Skipping {sheet}: invalid lat/lon")
    #     continue
    
    if location_data:  # optional safety check
        locations.extend(location_data)  # 👈 flatten here

odf = pd.DataFrame(locations)

#set the limit for 2024 Droitwich Rd (N) to 40
odf.loc[odf['road_name'] == '2024 Droitwich Rd (N)', 'limit'] = 40

#set the limit for 2023 Bransford Rd to 40
odf.loc[odf['road_name'] == '2023 Bransford Rd', 'limit'] = 40


odf.to_csv('raw_data/speed_data_raw.csv', index=False)

# ensure output directory exists
output_path = Path("data")
output_path.mkdir(parents=True, exist_ok=True)



# write JSON
#with open(output_path / "locations.json", "w", encoding="utf-8") as f:
    #json.dump(locations, f, indent=2)
