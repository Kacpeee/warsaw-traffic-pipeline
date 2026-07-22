import os
from dotenv import load_dotenv
import warsaw_data_api

load_dotenv()
api_key = os.getenv("WARSAW_DATA_API_KEY")

ztm = warsaw_data_api.ztm(apikey=api_key)
buses = ztm.get_buses_location()

print(f"Pobrano {len(buses)} pojazdow")
print("Przykladowy rekord:")
print(buses[0])
