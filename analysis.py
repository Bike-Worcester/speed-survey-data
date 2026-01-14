#vehicles per hour speeding during 7 til 7pm
# % veichles speeding during 7 til 7pm
#
# vehicles speeding per hour by hour
# vehicles speeding per hour (24h avg)
# % vehicles speeding per hour (24h avg)
#

# given dataframe with name, limit, speed_min, value = number of vehicles per hour above speed_min and below speed_max
# group by name, sum values if speed_min is greater than speed_limit, sum all values for total vehicles
#
# run same analysis but filter times between 7am and 7pm onl
#
# run same analysis but filter times between 7am and 7pm onlyy
#
#    return {
    #     "name": name if name else sheet_name,
    #     "lat": lat,
    #     "lon": lon,
    #     "limit": speed_limit if speed_limit else 0,
    #     "dates": {"start": start_date, "end": end_date},
    #     "distribution": distribution,
    #     "total_volume": total_volume
    # }
#
#

import pandas as pd

df = pd.read_csv("raw_data/speed_data_raw.csv")

df["name"] = df["road_name"]

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

df = create_speed_bins_labels(df)



df["speed_min"] = df["speed_min"].astype(int)

# Mask for speeding vehicles
speeding_mask = df["speed_min"] >= df["limit"]

# Mask for 07:00–18:59
daytime_mask = df["time"].str.match(r"^(0[7-9]|1[0-8]):\d{2}")

# Total vehicles per road
total_vehicles = df.groupby("name")["value"].sum()/24/60

# Number of vehicles during 07:00 to 18:59
vehicles_7_7 = df[daytime_mask].groupby("name")["value"].sum()/12/60

# Vehicles speeding during 07:00–18:59
vehicles_speeding_7_7 = df[speeding_mask & daytime_mask].groupby("name")["value"].sum()/12/60

# Vehicles speeding (24h)
vehicles_speeding = df[speeding_mask].groupby("name")["value"].sum()/24/60



valid_bins = [
    '<5', '5-<10', '10-<15', '15-<20', '20-<25', '25-<30', '30-<35', '35-<40',
    '40-<45', '45-<50', '50-<55', '55-<60', '=>60'
]

filter_df = df[df["speed_bin"].isin(valid_bins)]

# Make speed_bin a categorical with the correct order
filter_df["speed_bin"] = pd.Categorical(filter_df["speed_bin"], categories=valid_bins, ordered=True)

pivot_df = filter_df.pivot_table(
    index=["name"],       # group by road
    columns="speed_bin",       # columns = speed bins
    values="value",            # values to sum
    aggfunc="sum",             # sum over times
    fill_value=0               # if a road has no vehicles in a bin
)

pivot_df["speed_values"] = pivot_df.apply(lambda row: row.values.tolist(), axis=1)


time_df = filter_df.pivot_table(
    index=["name"],
    columns="time",
    values="value",
    aggfunc="sum",
    fill_value=0
)

time_df['time_values'] = time_df.apply(lambda row: row.values.tolist(), axis=1)


# Combine into a single DataFrame
summary = pd.DataFrame({
    "total_vehicles_per_min": total_vehicles,
    "vehicles_7_7_per_min": vehicles_7_7,
    "vehicles_speeding_7_7_per_min": vehicles_speeding_7_7,
    "vehicles_speeding_per_min": vehicles_speeding,
    "distribution": pivot_df["speed_values"],
    "time": time_df["time_values"]
}).fillna(0)  # fill roads with no speeding vehicles

# Reset index if needed
summary = summary.reset_index(
)

summary = summary[summary["distribution"] != 0]


summary["percent_speeding_7_7"] = (summary["vehicles_speeding_7_7_per_min"] / summary["vehicles_7_7_per_min"]) * 100
summary["percent_speeding"] = (summary["vehicles_speeding_per_min"] / summary["total_vehicles_per_min"]) * 100

lat_lon = df.groupby("name").agg({"lat":"first","start_date": "first", "end_date": "first", "lon":"first", "limit": "first"})

summary = summary.merge(lat_lon, on="name", how="left")


print(summary[["name", "limit"]].head())

"""checks: 
    has speed limit data
    distribution has length 13
    distribution sums to total vehicles



parse: round distributon, round vehicle counts

save to json 

"""


roads_to_exclude = ['2024 Swinesherd Way','2024 Tolladine Rd (2)','2023 Worcester Rd (south)', '2022 Laugherne Rd']

summary = summary[~summary["name"].isin(roads_to_exclude)]

    # 1️⃣ Check all roads have speed_limit
missing_limit = summary["limit"].isna()
if missing_limit.any():
    print("Warning: some roads are missing speed_limit:", summary.loc[missing_limit, "name"].tolist())

# 2️⃣ Check distribution length == 13
invalid_length = summary["distribution"].apply(lambda x: len(x) != 13)
if invalid_length.any():
    print("Warning: distribution length not 13 for roads:",
          summary.loc[invalid_length, "name"].tolist())

# 3️⃣ Check distribution sums to total_vehicles_per_min
distribution_sum_check = summary.apply(
    lambda row: round(sum(row["distribution"]), 6) != round(row["total_vehicles_per_min"]*24*60, 6),
    axis=1
)
if distribution_sum_check.any():
    print("Warning: distribution sum mismatch for roads:",
          summary.loc[distribution_sum_check, "name"].tolist())

    # Round distribution and vehicle counts
summary["distribution"] = summary["distribution"].apply(lambda x: [int(round(v, 0)) for v in x])
summary["total_vehicles_per_min"] = summary["total_vehicles_per_min"].round(1)
summary["time"] = summary["time"].apply(lambda x: [round(v/60, 1) for v in x])
summary["vehicles_7_7_per_min"] = summary["vehicles_7_7_per_min"].round(1)
summary["vehicles_speeding_7_7_per_min"] = summary["vehicles_speeding_7_7_per_min"].round(2)
summary["vehicles_speeding_per_min"] = summary["vehicles_speeding_per_min"].round(1)
summary["percent_speeding_7_7"] = summary["percent_speeding_7_7"].round(1)
summary["percent_speeding"] = summary["percent_speeding"].round(1)
summary["start_date"] = pd.to_datetime(
    summary["start_date"], dayfirst=True
).dt.strftime("%Y-%m-%d")

summary["end_date"] = pd.to_datetime(
    summary["end_date"], dayfirst=True
).dt.strftime("%Y-%m-%d")


summary.to_json("data/locations.json", orient="records", indent=2)
print("Saved summary to speed_summary.json")
