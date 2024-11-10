import streamlit as st
from geopy.geocoders import Nominatim # Locations
from geopy.distance import geodesic # Distance for beginning and at the end for Maps
import folium # Create the Map
from streamlit_folium import st_folium #Helps integrate the Folim maps into streamlit
from datetime import datetime, timedelta 
import requests # getting the weahter data form a link request 
import pandas as pd
import matplotlib.pyplot as plt # for visualisation
import streamlit.components.v1 as components

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
    
    if response.status_code == 200 and "hourly" in data:
        times = data["hourly"]["time"]
        temperatures = data["hourly"]["temperature_2m"]
        wind_speeds = data["hourly"]["windspeed_10m"]
        
        weather_df = pd.DataFrame({
            "Time": times,
            "Temperature (°C)": temperatures,
            "Wind Speed (m/s)": wind_speeds
        })
        weather_df["Time"] = pd.to_datetime(weather_df["Time"])
        
        weather_df["Wind Speed > 3 m/s (suitable)"] = weather_df["Wind Speed (m/s)"].where(weather_df["Wind Speed (m/s)"] > 3)
        weather_df["Wind Speed ≤ 3 m/s"] = weather_df["Wind Speed (m/s)"].where(weather_df["Wind Speed (m/s)"] <= 3)
        
        weather_df = weather_df.set_index("Time").resample("1H").first()
        weather_df["3H Label"] = weather_df.index.to_series().where(weather_df.index.minute == 0).resample("3H").first()

        return weather_df, None
    else:
        return None, "Unable to retrieve weather data."

# Function to generate Google Maps directions, or jsut link for it, to help create this code we used ChatGPT, most for what and how to return something
def generate_directions_link(start_coords, end_coords):
    start_lat, start_lon = start_coords
    end_lat, end_lon = end_coords
    return f"https://www.google.com/maps/dir/{start_lat},{start_lon}/{end_lat},{end_lon}"

# If a lake has been selected, display its details on a new page and fetch weather
if st.session_state.selected_lake:
    selected_lake = st.session_state.selected_lake
    selected_date = st.session_state.selected_date

    st.header(f"Details for {selected_lake['name']}")
    st.write(f"**Coordinates:** Latitude {selected_lake['latitude']}, Longitude {selected_lake['longitude']}")
    st.write(f"**Selected Date:** {selected_date}")

    weather_data, error = fetch_weather_3_hour(selected_lake["latitude"], selected_lake["longitude"], selected_date)
    
    if weather_data is not None:
        st.subheader("Temperature and Wind Speed (3-Hour Intervals)")
        
        # Plot non-zoomable area chart with Matplotlib
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot temperature as the background layer
        ax.plot(weather_data.index, weather_data["Temperature (°C)"], color="skyblue", label="Temperature (°C)")
        
        # Plot green area up to the maximum wind speed for wind speeds ≤ 3 m/s
        ax.fill_between(weather_data.index, 0, weather_data["Wind Speed (m/s)"], 
                        color="green", alpha=0.5, label="Wind Speed ≤ 3 m/s")

        # Plot orange area only for wind speeds > 3 m/s, covering the green area where applicable
        ax.fill_between(weather_data.index, 0, weather_data["Wind Speed (m/s)"], 
                        where=weather_data["Wind Speed (m/s)"] > 3, 
                        color="orange", alpha=1, label="Wind Speed > 3 m/s (suitable)")

        # Set labels and title
        ax.set_xlabel("Time")
        ax.set_ylabel("Values")
        ax.set_title("Weather Data")
        ax.legend()
        
        # Display the plot in Streamlit without zoom functionality
        st.pyplot(fig)
        
        st.write("The chart shows temperature and wind speeds at 3-hour intervals.")
        st.write("Wind speeds above 3 m/s (suitable for sailing) are highlighted in the 'Wind Speed > 3 m/s (suitable)' series.")
    else:
        st.write(error)

    st.title("Lake Webcam Stream")
    st.write(f"Webcam view of {selected_lake['name']}") #f, is for the f-string, then afterwards with name we can put out the name of the selected lake
    st.components.v1.iframe(selected_lake['webcam_url'], height=600, scrolling=False)
    
    # Generate and display directions link, to help create this code we used ChatGPT, mostly for how to structure it correctly
    if "user_location" in st.session_state:
        directions_link = generate_directions_link(
            st.session_state["user_location"],
            (selected_lake["latitude"], selected_lake["longitude"])
        )
        st.markdown(f"[Get Directions to {selected_lake['name']}]({directions_link})")
    
    if st.button("Back to Map"):
        st.session_state.selected_lake = None
        st.experimental_rerun()

else:
    location = st.text_input("Enter a location (e.g., 'Zurich', 'St. Gallen', 'New York'):")

    today = datetime.now()
    selected_date = st.date_input("Select a date:", today, min_value=today, max_value=today + timedelta(days=14))
    st.session_state.selected_date = selected_date.strftime('%Y-%m-%d')

    radius = st.slider("Select radius (in kilometers):", min_value=1, max_value=100, value=10)

    swiss_lakes = [
        {"name": "Lake Zurich", "latitude": 47.232625, "longitude": 8.704907, "webcam_url": "https://rcz.ch/webcam"}, 
        {"name": "Lake Zug", "latitude": 47.143029, "longitude": 8.481866},
        {"name": "Lake Greifensee", "latitude": 47.349059, "longitude": 8.679752},
        {"name": "Lake Aegeri", "latitude": 47.121541, "longitude": 8.630019},
    ]

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

    if location:
        loc = geolocator.geocode(location)
        
        if loc:
            st.session_state["user_location"] = (loc.latitude, loc.longitude)
            
            st.write(f"**Location:** {loc.address}")
            st.write(f"**Latitude:** {loc.latitude}, **Longitude:** {loc.longitude}")
            st.write(f"**Selected Date:** {selected_date.strftime('%Y-%m-%d')}")
            
            zoom_level = calculate_zoom_level(radius)
            
            m = folium.Map(location=[loc.latitude, loc.longitude], zoom_start=zoom_level)
            folium.Marker([loc.latitude, loc.longitude], tooltip=loc.address, icon=folium.Icon(color="blue")).add_to(m)
            
            folium.Circle(
                location=[loc.latitude, loc.longitude],
                radius=radius * 1000,
                color="blue",
                fill=False
            ).add_to(m)
            
            for lake in swiss_lakes:
                lake_coords = (lake["latitude"], lake["longitude"])
                location_coords = (loc.latitude, loc.longitude)
                
                distance_to_lake = geodesic(location_coords, lake_coords).km
                
                if distance_to_lake <= radius:
                    marker = folium.Marker(
                        lake_coords,
                        tooltip=f"{lake['name']} ({distance_to_lake:.2f} km away)",
                        icon=folium.Icon(color="red")
                    )
                    
                    marker.add_child(folium.Popup(f"Click here to select {lake['name']}", parse_html=True))
                    marker.add_to(m)

            st_map = st_folium(m, width=700, height=500)

            if st_map["last_object_clicked"] is not None:
                clicked_coords = st_map["last_object_clicked"]["lat"], st_map["last_object_clicked"]["lng"]
                for lake in swiss_lakes:
                    if (lake["latitude"], lake["longitude"]) == clicked_coords:
                        st.session_state.selected_lake = lake
                        st.experimental_rerun()
                        break
