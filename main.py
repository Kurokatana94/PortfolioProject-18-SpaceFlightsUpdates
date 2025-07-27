import datetime
from time import sleep

from flask import Flask, render_template, jsonify, request
from flask_bootstrap import Bootstrap5
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import datetime as dt
import pandas as pd
import requests
import gspread
import json
import os

# Load env file
load_dotenv()
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
GOOGLE_CREDENTIALS_DICT = json.loads(GOOGLE_CREDENTIALS_JSON)

# Auth Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDENTIALS_DICT, scope)
client = gspread.authorize(creds)

sheet = client.open("Space Flights Database").sheet1

def past_launches_db_update():
    try:
        existing_records = sheet.get_all_records()
        existing_names = {row["Name"] for row in existing_records}
        existing_launch_dates = {row["Date"] for row in existing_records}
        current_time = dt.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        url = f"https://ll.thespacedevs.com/2.2.0/launch/?limit=100&ordering=-net&net__lte={current_time}"

        print("Fetching new launches data...")
        response = requests.get(url)
        response.raise_for_status()

        valid_status_ids = [3, 4, 5]  # Success, Failure, Partial
        data = response.json()
        recent_launches = [launch for launch in data['results'] if launch.get("status", {}).get("id") in valid_status_ids]

        print(recent_launches)

        new_records = []
        for launch in recent_launches[::-1]:
            name = launch.get("name")
            date = launch.get("window_start")
            if name not in existing_names and date not in existing_launch_dates:
                new_records.append([
                    name,
                    date,
                    launch.get("status", {}).get("name"),
                    launch.get("rocket", {}).get("configuration", {}).get("name"),
                    launch.get("launch_service_provider", {}).get("name"),
                    launch.get("pad", {}).get("location", {}).get("name"),
                ])
        print(new_records)
        if new_records:
            sheet.append_rows(new_records)
            print(f"Added {len(new_records)} new launches to the sheet.")
        else:
            print("No new launches to add.")
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            print("Failed to fetch launches: Error 429 - Too Many API calls")
        else:
            print(f"Failed to fetch launches:", e)

# all_launches = []
# url = "https://ll.thespacedevs.com/2.2.0/launch/?limit=100"
#
# while url:
#     try:
#         response = requests.get(url)
#         response.raise_for_status()
#         data = response.json()
#         all_launches.extend(data['results'])
#         print(f"Fetched: {len(all_launches)} launches")
#         url = data.get("next")
#     except requests.exceptions.HTTPError as e:
#         if response.status_code == 429:
#             print("Requests limit hit, sleeping for 3600s")
#             sleep(3600)
#         else:
#             print("Error raised while fetching:", e)
#
#
# print(f"Fetched a total of: {len(all_launches)} launches")
#
# records = []
#
# for launch in all_launches:
#     if launch.get("status", {}).get("id") in [3, 4, 5]:
#         records.append({
#             "Name": launch.get("name"),
#             "Date": launch.get("window_start"),
#             "Status": launch.get("status", {}).get("name"),
#             "Rocket": launch.get("rocket", {}).get("configuration", {}).get("name"),
#             "Provider": launch.get("launch_service_provider", {}).get("name"),
#             "Location": launch.get("pad", {}).get("location", {}).get("name"),
#         })
#
#
# df = pd.DataFrame(records)
#
# print("Uploading to Google Sheets...")
# sheet.clear()
# sheet.update([df.columns.values.tolist()] + df.values.tolist())
# print("Upload complete.")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
Bootstrap5(app)

@app.route("/")
def index():
    past_launches_db_update()
    return render_template("index.html", year=dt.datetime.now().year)

if __name__ == "__main__":
    app.run(debug=True)