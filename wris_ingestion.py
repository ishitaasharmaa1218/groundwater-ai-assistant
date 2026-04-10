import requests
import psycopg2

url = "https://indiawris.gov.in/Dataset/Soil Moisture"

params = {
    "stateName": "Maharashtra",
    "districtName": "Pune",
    "agencyName": "NRSC VIC MODEL",
    "startdate": "2016-01-01",
    "enddate": "2026-01-01",
    "download": "false",
    "page": 0,
    "size": 1000
}

response = requests.post(url, params=params)
data = response.json()

conn = psycopg2.connect(
    database="groundwater_db",
    user="postgres",
    password="postgre123",
    host="localhost",
    port="5432"
)

cursor = conn.cursor()

for record in data["data"]:

    cursor.execute(
        """
        INSERT INTO soil_moisture_data
        (state, district, date, value)
        VALUES (%s,%s,%s,%s)
        """,
        (
            record["stateName"],
            record["districtName"],
            record["date"],
            record["dataValue"]
        )
    )

conn.commit()
cursor.close()
conn.close()

print("WRIS soil moisture data inserted.")