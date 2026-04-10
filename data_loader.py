import pandas as pd
import os

folder = "datasets"
all_data = []

for file in os.listdir(folder):

    if file.endswith(".csv"):

        path = os.path.join(folder, file)

        df = pd.read_csv(path, skiprows=2)

        df = df.iloc[:, :8]

        df.columns = [
            "block",
            "annual_recharge",
            "natural_discharge",
            "net_groundwater",
            "irrigation_draft",
            "domestic_draft",
            "total_draft",
            "groundwater_development_percent"
        ]

        district = file.split("_")[7]

        df["district"] = district
        df["year"] = 2020

        all_data.append(df)

combined_df = pd.concat(all_data)

print(combined_df.head())
print("Total rows:", len(combined_df))

combined_df.to_csv("maharashtra_groundwater_2020_clean.csv", index=False)

print("Clean dataset saved.")