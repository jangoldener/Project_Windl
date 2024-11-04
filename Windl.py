import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import requests
import pandas as pd

# Initialize the geolocator
geolocator = Nominatim(user_agent="location_app")

# Title of the app
st.title("Location Finder with Nearby Lakes in Switzerland")

# Check if there is already a selected lake stored in the session state
if "selected_lake" not in st.session_state:
    st.session_state.selected_lake = None

# Function to fetch weather data from Open-Meteo API with 3-hour intervals
def fetch_weather_3_hour(lat, lon, date):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["temperature_2m", "windspeed_10m"],
        "timezone": "Europe/Zurich",
        "start_date": date,
        "end_date": date
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if response.status_code == 200 and "hourly" in data: #status code, if successfully its 200
        # Extract temperature and wind speed data
        times = data["hourly"]["time"]
        temperatures = data["hourly"]["temperature_2m"]
        wind_speeds = data["hourly"]["windspeed_10m"]
        
        # Create a DataFrame with 3-hour intervals, json object
        weather_df = pd.DataFrame({
            "Time": times,
            "Temperature (°C)": temperatures,
            "Wind Speed (m/s)": wind_speeds
        })
        weather_df["Time"] = pd.to_datetime(weather_df["Time"])
        weather_df = weather_df.set_index("Time").resample("3H").first()
        
        # Separate wind speeds based on the 3 m/s threshold for sailing suitability
        weather_df["Wind Speed > 3 m/s (suitable)"] = weather_df["Wind Speed (m/s)"].where(weather_df["Wind Speed (m/s)"] > 3)
        weather_df["Wind Speed ≤ 3 m/s"] = weather_df["Wind Speed (m/s)"].where(weather_df["Wind Speed (m/s)"] <= 3)

        return weather_df, None
    else:
        return None, "Unable to retrieve weather data."

# If a lake has been selected, display its details on a new page and fetch weather
if st.session_state.selected_lake:
    selected_lake = st.session_state.selected_lake
    selected_date = st.session_state.selected_date

    st.header(f"Details for {selected_lake['name']}")
    st.write(f"**Coordinates:** Latitude {selected_lake['latitude']}, Longitude {selected_lake['longitude']}")
    st.write(f"**Selected Date:** {selected_date}")
    
    # Fetch and display weather information
    weather_data, error = fetch_weather_3_hour(selected_lake["latitude"], selected_lake["longitude"], selected_date)
    
    if weather_data is not None:
        st.subheader("Temperature and Wind Speed (3-Hour Intervals)")
        
        # Display temperature and wind speed with conditional suitability for sailing
        st.area_chart(weather_data[["Temperature (°C)", "Wind Speed > 3 m/s (suitable)", "Wind Speed ≤ 3 m/s"]])
        
        st.write("The chart shows temperature and wind speeds at 3-hour intervals.")
        st.write("Wind speeds above 3 m/s (suitable for sailing) are highlighted in the 'Wind Speed > 3 m/s (suitable)' series.")
        
    else:
        st.write(error)
    
    # Option to go back to the main page
    if st.button("Back to Map"):
        st.session_state.selected_lake = None  # Reset the selected lake
        st.experimental_rerun()  # Reload the app to go back to the map page

else:
    # Main page for location and map
    location = st.text_input("Enter a location (e.g., 'Zurich', 'St. Gallen', 'New York'):")

    # Date picker for the selected date, limited to 14 days from today
    today = datetime.now()
    selected_date = st.date_input("Select a date:", today, min_value=today, max_value=today + timedelta(days=14))
    st.session_state.selected_date = selected_date.strftime('%Y-%m-%d')  # Store selected date in session state

    # Slider for radius selection (in kilometers)
    radius = st.slider("Select radius (in kilometers):", min_value=1, max_value=100, value=10)

    # List of major lakes in Switzerland with their coordinates
    swiss_lakes = [
        {"name": "Lake Zurich", "latitude": 47.232625, "longitude": 8.704907}, 
        {"name": "Lake Zug", "latitude": 47.143029, "longitude": 8.481866},
        {"name": "Lake Greifensee", "latitude": 47.349059, "longitude": 8.679752},
        {"name": "Lake Aegeri", "latitude": 47.121541, "longitude": 8.630019},
    ]

    # Calculate zoom level based on radius
    def calculate_zoom_level(radius_km):
        if radius_km <= 1:
            return 15
        elif radius_km <= 5:
            return 13
        elif radius_km <= 10:
            return 12
        elif radius_km <= 20:
            return 11
        elif radius_km <= 50:
            return 10
        else:
            return 8

    # Geocode the location and display on map
    if location:
            # Geocode the location
            loc = geolocator.geocode(location)
            
            if loc:
                # Display location details and selected date
                st.write(f"**Location:** {loc.address}")
                st.write(f"**Latitude:** {loc.latitude}, **Longitude:** {loc.longitude}")
                st.write(f"**Selected Date:** {selected_date.strftime('%Y-%m-%d')}")
                
                # Calculate zoom level based on radius
                zoom_level = calculate_zoom_level(radius)
                
                # Create a map centered on the location with the calculated zoom level
                m = folium.Map(location=[loc.latitude, loc.longitude], zoom_start=zoom_level)
                
                # Add marker for the selected location
                folium.Marker([loc.latitude, loc.longitude], tooltip=loc.address, icon=folium.Icon(color="blue")).add_to(m)
                
                # Add an unfilled circle with the specified radius (converted to meters)
                folium.Circle(
                    location=[loc.latitude, loc.longitude],
                    radius=radius * 1000,  # Convert kilometers to meters
                    color="blue",
                    fill=False  # Set fill to False for an unfilled circle
                ).add_to(m)
                
                # Check each lake to see if it falls within the specified radius
                for lake in swiss_lakes:
                    lake_coords = (lake["latitude"], lake["longitude"])
                    location_coords = (loc.latitude, loc.longitude)
                    
                    # Calculate distance between the selected location and the lake
                    distance_to_lake = geodesic(location_coords, lake_coords).km
                    
                    # If the lake is within the specified radius, add a clickable red marker
                    if distance_to_lake <= radius:
                        marker = folium.Marker(
                            lake_coords,
                            tooltip=f"{lake['name']} ({distance_to_lake:.2f} km away)",
                            icon=folium.Icon(color="red")
                        )
                        
                        # Add a popup with a selection option
                        marker.add_child(folium.Popup(f"Click here to select {lake['name']}", parse_html=True))
                        marker.add_to(m)

                # Display the map
                st_map = st_folium(m, width=700, height=500)

                # Check if a marker was clicked by examining the returned data from st_folium
                if st_map["last_object_clicked"] is not None:
                    clicked_coords = st_map["last_object_clicked"]["lat"], st_map["last_object_clicked"]["lng"]
                    for lake in swiss_lakes:
                        if (lake["latitude"], lake["longitude"]) == clicked_coords:
                            st.session_state.selected_lake = lake
                            st.experimental_rerun()  # Reload the app to go to the selected lake page
                            break