import pandas as pd
import psycopg2

# read cleaned dataset
df = pd.read_csv("datasets/maharashtra_groundwater_2020_clean.csv")

# connect database
conn = psycopg2.connect(
    database="groundwater_db",
    user="postgres",
    password="postgre123",
    host="localhost",
    port="5432"
)

cursor = conn.cursor()

for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO groundwater_resources
        (block, annual_recharge, natural_discharge, net_groundwater,
        irrigation_draft, domestic_draft, total_draft,
        groundwater_development_percent, district, year)

        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """,
    (
        row["block"],
        row["annual_recharge"],
        row["natural_discharge"],
        row["net_groundwater"],
        row["irrigation_draft"],
        row["domestic_draft"],
        row["total_draft"],
        row["groundwater_development_percent"],
        row["district"],
        row["year"]
    ))

conn.commit()
cursor.close()
conn.close()

print("Data inserted successfully.")