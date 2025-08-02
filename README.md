# Space Flights Updates

An interactive web app built with Flask, JavaScript, and Chart.js — track historical and upcoming space launches with a dynamic calendar and a customizable analytics chart.

## Live Demo
- www.timotyravoni.com/space-flights-updates

## Concept
- Visualize space launch data with a monthly or yearly breakdown.
- Choose a custom time range and toggle between detailed monthly data or broader yearly trends.
- All past and upcoming launches are also shown on an interactive calendar with status-based color coding.

<img width="1471" height="1238" alt="space_flights_updates" src="https://github.com/user-attachments/assets/1b2f0de4-1dbe-4639-89aa-eb2cb561fc04" />

## Built With
- **Flask** – backend server and data routing
- **Chart.js** – for dynamic charts with filters and custom ranges
- **gspread** – to store and retrieve data from google sheets
- **FullCalendar** – shows launches per day in a calendar layout
- **Flatpickr + monthSelectPlugin** – for smooth month/year date picking
- **JavaScript (vanilla)** – frontend interactivity and rendering
- **HTML/CSS** – layout and styling

## Features
- **Calendar View**
  - Color-coded launches by status:
    - 🟢 Successful
    - 🔴 Failed
    - 🟠 Partial
    - 🔵 Upcoming
  - Hover for launch name, location, provider, and status
- **Launch Chart**
  - View monthly stats for the past year by default
  - Select any time range using custom month pickers
  - Automatically switches to **yearly aggregation** for ranges over 25 months
  - Supports Total, Success, Failure, and Partial lines (dashed and color-coded)
- **Smart Range Detection**
  - Automatically chooses chart granularity based on selected date range
- **Quick Year Selector**
  - Enhanced Flatpickr with dropdown to quickly jump between years

### Thanks for Checking It Out!
Feel free to **download**, **modify**, and **use** this project however you'd like. Feedback or suggestions are always welcome!
