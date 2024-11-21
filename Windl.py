import streamlit as st
from geopy.geocoders import Nominatim # Locations
from geopy.distance import geodesic # Distance for beginning and at the end for Maps
import folium # Create the Map
from streamlit_folium import st_folium #Helps integrate the Folim maps into streamlit
from datetime import datetime, timedelta 
import requests # getting the weahter data form a link request 
import pandas as pd
import matplotlib.pyplot as plt # for visualisation
import streamlit.components.v1 as components # for embeding the webcam

# Initialize the geolocator
geolocator = Nominatim(user_agent="location_app") 
#We set up a geolovator tool called Nominatim, which is part of a package called geopy. The geolocator helps us find the latitude and longitude for a place name, or find a place name on the basis of coordinates.

# Title of the app
st.title("Location Finder with Nearby Lakes in Switzerland")
#Here we set up a title at the top of our app's page, we use st.title() which displays "Location FInder with Nearby Lakes in Switzerland" as a header, so users know the main purpose of our app.

# Check if there is already a selected lake stored in the session state
if "selected_lake" not in st.session_state:
    st.session_state.selected_lake = None
#This part of our code checks if a variable called selected_lake is already stored in st.session_state. which is a special storage in Streamlit that keeps values between user actions, like clicks or page refreshes.
#If selected_lake isn't in st.session_state yet, it sets st.session_state.selected_lake to None (meaning that no lake has been chosen)

# Function to fetch weather data from Open-Meteo API with 3-hour intervals
def fetch_weather_3_hour(lat, lon, date): #This line defines a new function which will take three inputs: lat (latitude), lon (longitude) and date. The function is designed to fetch weather data from our online source based on these inputs.
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["temperature_2m", "windspeed_10m"],
        "timezone": "Europe/Zurich",
        "start_date": date,
        "end_date": date
    }
    #we set up the API's URL and create a dictionary called params with key details needed to get the weather data:
    #"latitude" and "longitude" specify the location of interest.
    #"hourly" tells the API that we want temperature and wind speed data every hour.
    #"timezone": "Europe/Zurich" ensures the data matches Switzerland's time zone.
    #"start_date" and "end_date" limit the data to just one day - the date we pass in.
    
    response = requests.get(url, params=params)
    #We send a GET request to the API using the requests.get() method, passing in the URL and the parameters.
    data = response.json()
    #The response from the API is stored in response and we convert it to JSON format with response.json() so it's easy to work with as data.
    
    if response.status_code == 200 and "hourly" in data:
    #Here we check two things to make sure the data was retrieved successfully:
    #response.status_sode == 200 checks if the request qas successful (status code 200 means "OK")
    #"hourly" in data confirms that the expected hourly weather data is actually in the response.
        #in the next step we pull out the specific weather details we want from the response data:
        times = data["hourly"]["time"]
        #times contains the time points of the weather readings.
        temperatures = data["hourly"]["temperature_2m"]
        #temperature has temperature data for each time point.
        wind_speeds = data["hourly"]["windspeed_10m"]
        #wind_speeds holds the wind speed data for each time point.
        
        weather_df = pd.DataFrame({
        #We create a DataFrame called weather_df using pd.DataFrame(), which organizes the weather data in table format.
            "Time": times,
            "Temperature (°C)": temperatures,
            "Wind Speed (m/s)": wind_speeds
            #This table has three columns: Time, Temperature (°C) and wind speed (m/s).
        })
        weather_df["Time"] = pd.to_datetime(weather_df["Time"])
        #Here we convert the Time column in weather_df into a datetime format, making it easier to handle time-based data in the DataFrame.

        #In these lines we create two new columns to categorize the wind speed:
        weather_df["Wind Speed > 3 m/s (suitable)"] = weather_df["Wind Speed (m/s)"].where(weather_df["Wind Speed (m/s)"] > 3)
        #"Wind Speed > 3 m/s (suitable)" only keeps wind speeds greater than 3 m/s (suitable for some water activities), leaving other values blank.
        weather_df["Wind Speed ≤ 3 m/s"] = weather_df["Wind Speed (m/s)"].where(weather_df["Wind Speed (m/s)"] <= 3)
        #"Wind Speed < 3 m/s (suitable)" does the opposite, keeping values 3 m/s or less and leaving other values blank.
        
        weather_df = weather_df.set_index("Time").resample("1H").first()
        #We resample the data to 1-hour intervals to organize it neatly by hour.
        weather_df["3H Label"] = weather_df.index.to_series().where(weather_df.index.minute == 0).resample("3H").first()
        #The 3HLabel column marks times every 3 hours to make it easy to check data at 3-hour intervals.

        return weather_df, None
    else:
        return None, "Unable to retrieve weather data."
        #If the data fetch was successful, weater_df is returned, along with None for no error.
        #If it was unsuccessful, it returns None for the data and a message saying "Unable to retrieve weather data".

# Function to generate Google Maps directions, or jsut link for it, to help create this code we used ChatGPT, most for what and how to return something
#This function creates a link to Google Maps directions between two points: start_coords and end_coords.
#We separate the latitude and longitude for both starting and ending points, then return a link to Google Maps.
def generate_directions_link(start_coords, end_coords):
    start_lat, start_lon = start_coords
    end_lat, end_lon = end_coords
    return f"https://www.google.com/maps/dir/{start_lat},{start_lon}/{end_lat},{end_lon}"

# If a lake has been selected, display its details on a new page and fetch weather
#This section checks if selected_lake has a value.
#If yes, it saves the selected lake's data and date to variables selected_lake and selected_date.
if st.session_state.selected_lake:
    selected_lake = st.session_state.selected_lake
    selected_date = st.session_state.selected_date
    
#Next up we display the name, coordinates and date chosen for the selected lake using Streamlit functions to show text on the app page.
    st.header(f"Details for {selected_lake['name']}")
    st.write(f"**Coordinates:** Latitude {selected_lake['latitude']}, Longitude {selected_lake['longitude']}")
    st.write(f"**Selected Date:** {selected_date}")

#This line calls the fetch_weather_3_hour function using the latitude, longitude and date of the selected lake
#It tries to get the weather data for the chosen lake and date storing it in weather_data. If there's an error, error will hold an error message.
    weather_data, error = fetch_weather_3_hour(selected_lake["latitude"], selected_lake["longitude"], selected_date)

#This checks if weather_data was successfully retrieved-
#If yes, a subheader "Temperature and Wind Speed (3-Hour Intervals)" is displayed to introduce the chart.
    if weather_data is not None:
        st.subheader("Temperature and Wind Speed (3-Hour Intervals)")
        
        # Plot non-zoomable area chart with Matplotlib
        #Here we create a new plot using matplotlib.
        #The figsize(10,6) makes the plot 10 units wide and 6 units tall.
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot temperature as the background layer
        #This plots the temperature data from weather_data on the graph, setting it as the background layer.
        #The line color is set to "sky blue" and it's labeled as "Temperature (°C)" so it appears in the legend.
        ax.plot(weather_data.index, weather_data["Temperature (°C)"], color="skyblue", label="Temperature (°C)")
        
        # Plot green area up to the maximum wind speed for wind speeds ≤ 3 m/s
        #This shades the area under the wind speed data in green where wind speeds are 3 m/s or below.
        #The alpha=0.5 makes the shading partially transparent.
        ax.fill_between(weather_data.index, 0, weather_data["Wind Speed (m/s)"], 
                        color="green", alpha=0.5, label="Wind Speed ≤ 3 m/s")

        # Plot orange area only for wind speeds > 3 m/s, covering the green area where applicable
        #This shades the area in orange for wind speeds above 3 m/s, overlapping the green shade if needed.
        #Wind speeds above 3 m/s are marked as suitable for specific activities, as shown in the label.
        ax.fill_between(weather_data.index, 0, weather_data["Wind Speed (m/s)"], 
                        where=weather_data["Wind Speed (m/s)"] > 3, 
                        color="orange", alpha=1, label="Wind Speed > 3 m/s (suitable)")

        # Set labels and title
        ax.set_xlabel("Time")  #adds a label "Time" for the x-axis.
        ax.set_ylabel("Values") #labels the y-asis as "Values" (since it includes both temperature and wind speed)
        ax.set_title("Weather Data") #gives the chart a title.
        ax.legend() #displays the legend, so users know what each color represents.
        
        # Display the plot in Streamlit without zoom functionality
        st.pyplot(fig)

        #These st.write lines give a brief description of the chart for the user.
        st.write("The chart shows temperature and wind speeds at 3-hour intervals.")
        st.write("Wind speeds above 3 m/s (suitable for sailing) are highlighted in the 'Wind Speed > 3 m/s (suitable)' series.")
    else:
        #If weather_data is None, meaning there was an issue retrieving it, this line displays the error message instead.
        st.write(error)
    #Shows a title indicating that there's a live webcam stream.
    st.title("Lake Webcam Stream")
    #displays the lake's name using a f-string.
    st.write(f"Webcam view of {selected_lake['name']}") #f, is for the f-string, then afterwards with name we can put out the name of the selected lake
    st.components.v1.iframe(selected_lake['webcam_url'], height=600, scrolling=False) # lets you embed the the website, in our case the webcam, code created with help of discuission platfor, (https://discuss.streamlit.io/t/how-do-i-embed-an-existing-non-streamlit-webpage-to-my-streamlit-app/50326/3)
    
    # Generate and display directions link, to help create this code we used ChatGPT, mostly for how to structure it correctly
    #if the user's location is available in session_state, this creates a link to get directions to the selected lake.
    #the gernerate_directions_link function creates the URL using the user's coordinates and the lake's.
    if "user_location" in st.session_state:
        directions_link = generate_directions_link(
            st.session_state["user_location"],
            (selected_lake["latitude"], selected_lake["longitude"])
        )
        st.markdown(f"[Get Directions to {selected_lake['name']}]({directions_link})") #displays a clickable link labeled with the lake's name, leading to Google Maps.

    #This adds a "Back to Map" button.
    #When clicked, it resets selected_lake to None and reloads the page to show the map again.
    if st.button("Back to Map"):
        st.session_state.selected_lake = None
        st.experimental_rerun()
#This creates a text input, where users can enter a location name.
else:
    location = st.text_input("Enter a location (e.g., 'Zurich', 'St. Gallen', 'Lucerne'):")

    #This sets up a date picker that limits choices from today up to 14 days ahead.
    today = datetime.now()
    selected_date = st.date_input("Select a date:", today, min_value=today, max_value=today + timedelta(days=14))
    #This line stores the selected date in the YYYY-MM-DD format.
    st.session_state.selected_date = selected_date.strftime('%Y-%m-%d')

    #Here we create a slider allowing users to choose a radius (20 to 140km) for the lake search area.
    radius = st.slider("Select radius (in kilometers):", min_value=20, max_value=140, value=20)

    #This is a list of lake dictionaries each containing the lake's name, coordinates and webcam URL (if available).
    swiss_lakes = [
        {"name": "Lake Zurich", "latitude": 47.232625, "longitude": 8.704907, "webcam_url": "https://rcz.ch/webcam"}, 
        {"name": "Lake Zug", "latitude": 47.177770, "longitude": 8.493900},
        {"name": "Lake Greifensee", "latitude": 47.349059, "longitude": 8.679752},
        {"name": "Lake Aegeri", "latitude": 47.121541, "longitude": 8.630019},
        {"name": "Lake Silvaplanersee", "latitude": 46.455214, "longitude": 9.790747, "webcam_url": "https://www.skylinewebcams.com/de/webcam/schweiz/graubunden/silvaplana/silvaplana-surfcenter.html"},
        {"name": "Lake Vierwaldstettersee", "latitude": 47.000890, "longitude": 8.580360, "webcam_url": "https://www.foto-webcam.eu/webcam/brunnen/"},
        {"name": "Lake Murtensee", "latitude": 46.933720, "longitude": 7.120470 , "webcam_url": "https://morat.roundshot.com/"},
        {"name": "Lake Sempachersee", "latitude": 47.047300, "longitude": 8.317306, "webcam_url": "http://seeland.ddns.net:8080/view/view.shtml?id=31445&imagepath=%2Fmjpg%2Fvideo.mjpg%3Fcamera%3D1&size=1"},
        {"name": "Lake Thunersee", "latitude": 46.714520, "longitude": 7.694180, "webcam_url": "https://content.meteobridge.com/cam/77be13b2a74ad2b8bd21d5101c18b18d/camplus.jpg"},
        {"name": "Lake Bielersee Ipsach", "latitude": 47.117030, "longitude": 7.224540, "webcam_url": "https://www.baspomedia.ch/webcam/ipsach/webcam_mega.jpg"},
        {"name": "Lake Urnsersee", "latitude": 46.917750, "longitude": 8.595310, "webcam_url": ""},

        ]

    #This function returns an appropriate zoom level for the map, depending on the chosen radius.
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

    #If a location name was entered, we can here use geolocator.geocode to get its coordinates.
    if location:
        loc = geolocator.geocode(location)

        #If a location was found, it's saved in session_state and displayed with its coordinates and the selected date.
        if loc:
            st.session_state["user_location"] = (loc.latitude, loc.longitude)
            
            st.write(f"**Location:** {loc.address}")
            st.write(f"**Latitude:** {loc.latitude}, **Longitude:** {loc.longitude}")
            st.write(f"**Selected Date:** {selected_date.strftime('%Y-%m-%d')}")

            #Here we create a folium map centered on the user's location, with a zoom level calculated by calculate_zoom_level.
            #It adds a blue marker showing the user's location.
            zoom_level = calculate_zoom_level(radius)
            
            m = folium.Map(location=[loc.latitude, loc.longitude], zoom_start=zoom_level)
            folium.Marker([loc.latitude, loc.longitude], tooltip=loc.address, icon=folium.Icon(color="blue")).add_to(m)

            #A circle showing the search area (in blue) is drawn around the user's location in the map.
            folium.Circle(
                location=[loc.latitude, loc.longitude],
                radius=radius * 1000,
                color="blue",
                fill=False
            ).add_to(m)

            #This loop calculates the distance between the user's location and each lake.
            #If a lake is within the radius, a red marker for that lake is added to the map, with a tooltip showing its name and distance.
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
            #The map is displayed in the app with a width of 700 and a height of 500.
            st_map = st_folium(m, width=700, height=500)
            
            #If the user clicks on a lake marker, this checks if any lake in swiss_lake matches the clicked coordinates.
            #If a match is found, st.session_state.selected_lake is set to that lake's data and the st.experimental_rerun() reloads the app to show details for the selected lake.
            if st_map["last_object_clicked"] is not None:
                clicked_coords = st_map["last_object_clicked"]["lat"], st_map["last_object_clicked"]["lng"]
                for lake in swiss_lakes:
                    if (lake["latitude"], lake["longitude"]) == clicked_coords:
                        st.session_state.selected_lake = lake
                        st.experimental_rerun()
                        break
