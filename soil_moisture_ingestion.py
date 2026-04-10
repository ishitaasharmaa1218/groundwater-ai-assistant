import requests
import psycopg2

conn = psycopg2.connect(
    database="groundwater_db",
    user="postgres",
    password="postgre123",
    host="localhost",
    port="5432"
)

cursor = conn.cursor()

districts = [
    "Pune",
    "Amravati",
    "Nashik",
    "Aurangabad",
    "Akola",
    "Thane",
    "Mumbai"
]

for district in districts:

    url = f"https://indiawris.gov.in/Dataset/Soil Moisture?stateName=Maharashtra&districtName={district}&agencyName=NRSC%20VIC%20MODEL&startdate=2016-01-01&enddate=2026-03-03&download=false&page=0&size=1000"

    response = requests.get(url)
    data = response.json()

    for row in data["data"]:

        date = row["date"]
        value = row["value"]

        cursor.execute(
        """
        INSERT INTO soil_moisture_data(district,date,value)
        VALUES(%s,%s,%s)
        """,
        (district,date,value)
        )

conn.commit()
cursor.close()