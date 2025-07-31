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

spreadsheet = client.open("Space Flights Database")
past_launches_sheet = spreadsheet.worksheet("past_launches")
upcoming_launches_sheet = spreadsheet.worksheet("upcoming_launches")

def fetch_upcoming_launches():
    upcoming_launches = []
    current_time = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    upcoming_launches_url = f"https://ll.thespacedevs.com/2.2.0/launch/?limit=100&ordering=net&net__gte={current_time}"
    print("Fetching upcoming launches data...")

    while upcoming_launches_url:
        try:
            response = requests.get(upcoming_launches_url)
            response.raise_for_status()

            data = response.json()
            upcoming_launches.extend(data['results'])
            print(f"Fetched: {len(upcoming_launches)} launches")
            upcoming_launches_url = data.get('next')
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                print("Failed to fetch launches: Error 429 - Too Many API calls")
                return upcoming_launches
            else:
                print(f"Failed to fetch launches:", e)
    print(f"Fetched a total of: {len(upcoming_launches)} launches")
    return upcoming_launches

def fetch_past_launches():
    existing_records = past_launches_sheet.get_all_records()
    existing_names = {row["Name"] for row in existing_records}
    existing_launch_dates = {row["Date"] for row in existing_records}
    current_time = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    past_launches_url = f"https://ll.thespacedevs.com/2.2.0/launch/?limit=100&ordering=-net&net__lte={current_time}"

    print("Fetching new launches data...")
    new_records = []
    try:
        response = requests.get(past_launches_url)
        print(response)
        response.raise_for_status()

        valid_status_ids = [3, 4, 5]  # Success, Failure, Partial
        data = response.json()
        recent_launches = [launch for launch in data['results'] if launch.get("status", {}).get("id") in valid_status_ids]

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
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            print("Failed to fetch launches: Error 429 - Too Many API calls")
        else:
            print(f"Failed to fetch launches:", e)
    return new_records

def past_launches_db_update():
    new_records = fetch_past_launches()
    if new_records:
        past_launches_sheet.append_rows(new_records)
        print(f"Added {len(new_records)} new launches to the sheet.")
    else:
        print("No new launches to add.")

def upcoming_launches_db_update():
    upcoming_launches = fetch_upcoming_launches()
    records = []

    for launch in upcoming_launches:
        records.append({
            "Name": launch.get("name"),
            "Date": launch.get("window_start"),
            "Status": launch.get("status", {}).get("name"),
            "Rocket": launch.get("rocket", {}).get("configuration", {}).get("name"),
            "Provider": launch.get("launch_service_provider", {}).get("name"),
            "Location": launch.get("pad", {}).get("location", {}).get("name"),
        })
    if records:
        df = pd.DataFrame(records)
        print("Uploading to Google Sheets...")
        upcoming_launches_sheet.clear()
        upcoming_launches_sheet.update([df.columns.values.tolist()] + df.values.tolist())
        print("Upload complete.")


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
# past_launches_sheet.clear()
# past_launches_sheet.update([df.columns.values.tolist()] + df.values.tolist())
# print("Upload complete.")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
Bootstrap5(app)

@app.route("/")
def index():
    past_launches_db_update()
    upcoming_launches_db_update()

    upcoming_launches = upcoming_launches_sheet.get_all_records()
    records = past_launches_sheet.get_all_records()

    # Organize data for chart (launches per year)
    past_year_data = {}

    for row in records:
        try:
            date_str = row["Date"]
            year = dt.datetime.fromisoformat(date_str).year
            status = row["Status"]

            if year not in past_year_data:
                past_year_data[year] = {"total": 0, "success": 0, "failure": 0, "partial": 0}

            past_year_data[year]["total"] += 1
            if "success" in status.lower():
                past_year_data[year]["success"] += 1
            elif "fail" in status.lower():
                past_year_data[year]["failure"] += 1
            elif "partial" in status.lower():
                past_year_data[year]["partial"] += 1
        except Exception as e:
            print("Skipping row due to:", e)
            continue  # Skip malformed rows

    years = sorted(past_year_data.keys())
    chart_data = {
        "years": years,
        "total": [past_year_data[y]["total"] for y in years],
        "success": [past_year_data[y]["success"] for y in years],
        "failure": [past_year_data[y]["failure"] for y in years],
        "partial": [past_year_data[y]["partial"] for y in years]
    }

    return render_template("index.html",
                           year=dt.datetime.now().year,
                           chart_data=chart_data,
                           raw_data=records,
                           upcoming_launches=upcoming_launches)

if __name__ == "__main__":
    app.run(debug=True)