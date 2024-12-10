import streamlit as st # helps creating interactive data applications
from geopy.geocoders import Nominatim # Locations, adresses to latitude and longitude coordinates (an in other direction)
from geopy.distance import geodesic # Calculates distance between two geographical points
import folium # Create the Map
from streamlit_folium import st_folium # Helps to integrate the Folim maps into streamlit
from datetime import datetime, timedelta # Represents the time frame, timedelta handels the differences
import requests # Getting the weather data form a link request 
import pandas as pd # Helps to configurate the datasets 
import matplotlib.pyplot as plt # For visualisation
import streamlit.components.v1 as components # For embeding the webcam
import json # JSON is a data format 
from sklearn.ensemble import RandomForestClassifier # Machine Learning tool
from sklearn.model_selection import train_test_split, cross_val_score # Splits datasets into training sets, performs cross-validation as a technique to assess model performance by training it on different subsets of the data
from sklearn.ensemble import RandomForestRegressor # Similar to the regression tasks (but predicts values)
from sklearn.metrics import mean_squared_error, r2_score, make_scorer # Calculates a metric for regression tasks
import numpy as np # Library for compuations in Python
from sklearn.model_selection import GridSearchCV # Helps optimize model performance
import matplotlib.dates as mdates # Provides functions for handling and formatting data
from joblib import load # To load previously trained models



# Define a debug flag to control wheter error messages are displayed
debug = False # By setting "debug = False", it will be assumed the code is error-free (the program will be executed normally)

# Set up the Geolocator 
geolocator = Nominatim(user_agent="location_app") 
# We set up an object, which transforms adresses in geographical coordinates 

# App Title and Logo
st.image("logo.jpg")
st.title("Breeze Buddy")
st.subheader("Your Swiss Watersport Companion")
# Here we set up a title at the top of our app's page, we use st.title() which displays "Location Finder with Nearby Lakes in Switzerland" as a header, so users know the main purpose of our app

# Check if a lake is selected
if "selected_lake" not in st.session_state:
    st.session_state.selected_lake = None
# This part of our code checks if the variable called selected_lake is already stored in st.session_state. which is a special storage in Streamlit
# If selected_lake isn't in st.session_state yet, it sets st.session_state.selected_lake to None (so no lake has been chosen)

# Function to get weather data at 3-hour-intervalls
def fetch_weather_3_hour(lat, lon, date): # Defines a new function which will take three inputs: lat (latitude), lon (longitude) and date
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["temperature_2m", "windspeed_10m", "precipitation", "surface_pressure", "relative_humidity_2m", "shortwave_radiation"],
        "timezone": "Europe/Zurich",
        "start_date": date,
        "end_date": date
    }
    # Set up the API's URL and create a dictionary called params with key details needed to get the weather data:
    #"latitude" and "longitude" specify the location 
    #"hourly" tells the API that we want temperature and wind speed data every hour
    #"timezone": "Europe/Zurich" ensures the data matches Switzerland's time zone
    #"start_date" and "end_date" limit the data to just one day - the date we provide it
    
    # We send a GET-Request to the API-URL 
    response = requests.get(url, params=params)
    data = response.json()
    #The response from the API is stored in a JSON format, which will then be transformed in a Python object (storerd in the variable "data") and used for further use

    # If the variable debug has the value "True" the code will be executed through "if" (this is useful if there is an error message and we want to look over the plain data sets)
    if debug:
        str=json.dumps(data, indent=4) # Stores the formatted JSON string, "indent=4" for easier reading, 4 spaces
        st.code(str, language="json") # Display the formatted JSON string from above, code should use JSON language


    # Checkpoint: here we ensure that the data retrieved from the API is usable and valid
    if response.status_code == 200 and "hourly" in data: # Response.status_sode == 200 checks if the HTTP request was successful (status code 200 means "OK")
    #"hourly" in data confirms that the expected hourly weather data is actually in the response

        # We pull out the specific weather details we want from the response data:
        times = data["hourly"]["time"] # "times" contains the time points of the weather readings
        temperatures = data["hourly"]["temperature_2m"] # "Temperature" has temperature data for each time point
        wind_speeds = data["hourly"]["windspeed_10m"] # "Temperature" has temperature data for each time point... 
        precip = data["hourly"]["precipitation"]
        press = data["hourly"]["surface_pressure"]
        humid = data["hourly"]["relative_humidity_2m"]
        radi = data["hourly"]["shortwave_radiation"]

        # We create a DataFrame called weather_df using pd.DataFrame(), which organizes the weather data in table format. This helps us to organize the data.
        weather_df = pd.DataFrame({
            "Time": times,
            "Temperature (°C)": temperatures,
            "Wind Speed (m/s)": wind_speeds
            # This table has three columns: Time, Temperature (°C) and wind speed (m/s)
        })
        # Here we convert the Time column in weather_df into a datetime format, making it easier to handle time-based data in the DataFrame
        weather_df["Time"] = pd.to_datetime(weather_df["Time"])
        weather_df = weather_df.set_index("Time")

        # New DataFrame that has the same structure as weather_df, but with different data.
        weather_df2 = pd.DataFrame({
            "Time": times,
            "Precipitation (mm)": precip,
            "Solar irradiation (watt)": radi
         }) #dictionary where keys column names and values are the data
        
        # New DataFrame 
        weather_df3 = pd.DataFrame({
            "Time": times,
            "Luftdruck (hPa)": press,
         })

        
        # New DataFrame 
        weather_df4 = pd.DataFrame({
            "Time": times,
            "rel. Luftfeuchtigkeit (%)": humid,
         })

        
            
        # Returning the data in an organized way through DataFrames
        return weather_df, weather_df2, weather_df3, weather_df4, None  # If it was possible to return the weather data the weater_df is returned, along with None for no error.
    else:
        return None, "Unable to retrieve weather data." # If it was not possible to return the weather data, the message will be sent: "Unable to retrieve weather data".
       
        
# Here we load the machine learning model 
model = load('wave_height_model.joblib')


# Here we use a function to generate Google Maps directions (to help create this code we used ChatGPT)
def generate_directions_link(start_coords, end_coords): # This function creates a link to Google Maps directions between two points: start_coords and end_coords
    start_lat, start_lon = start_coords # We separate the latitude and longitude for both starting and ending points, then return a link to Google Maps
    end_lat, end_lon = end_coords
    return f"https://www.google.com/maps/dir/{start_lat},{start_lon}/{end_lat},{end_lon}"



# Main App Logic

if st.session_state.selected_lake: # This section checks if selected_lake has a value
    selected_lake = st.session_state.selected_lake # If a lake is selected, we display its details and weather data
    selected_date = st.session_state.selected_date
    st.header(f"Details for {selected_lake['name']}") # Next up we display the name, coordinates and date chosen for the selected lake using Streamlit functions to show text on the app page
    st.write(f"**Coordinates:** Latitude {selected_lake['latitude']}, Longitude {selected_lake['longitude']}")
    st.write(f"**Selected Date:** {selected_date}")
    # This line calls the fetch_weather_3_hour function using the latitude, longitude and date of the selected lake
    weather_data, weather_data2, weather_data3, weather_data4,  error = fetch_weather_3_hour(selected_lake["latitude"], selected_lake["longitude"], selected_date) # It tries to get the weather data for the chosen lake and date storing it in weather_data. If there's an error, error will hold an error message

        # Display Temperature and Wind Speed 
    if weather_data is not None: # This checks if weather_data was successfully retrieved

        # Creating a subheader
        st.subheader("Temperature and Wind Speed")

        # Set up the dark theme
        plt.style.use('dark_background')

        # Plot the data
        fig, ax = plt.subplots(figsize=(12, 6)) # Creates figure and axes object for plotting
        ax.plot(
            weather_data.index, weather_data["Temperature (°C)"], marker='o', markersize=5, label='Temperature (°C)', linestyle='-', linewidth=2, color="cyan", alpha =0.9)
        # Marker 'o' creates a point in the graph

        ax.plot(
            weather_data.index, weather_data["Wind Speed (m/s)"], marker='o',  markersize=5, label='Wind Speed (m/s)', linestyle='-', linewidth=2, color="#8000ff", alpha =0.9)

        # Here we customize the displayed font
        
        ax.set_xlabel("Time (hours)", fontsize=12)
        ax.set_ylabel('Values', fontsize=14)

        # Format the x-axis using mdates
        locator = mdates.HourLocator(interval=3)  # Adjust to show ticks every 3 hours
        formatter = mdates.DateFormatter('%Y-%m-%d %H:%M')  # Format time labels
        ax.xaxis.set_major_locator(locator) # Sets positions
        ax.xaxis.set_major_formatter(formatter) 

        ax.tick_params(axis='x', rotation=45, labelsize=12)
        ax.tick_params(axis='y', labelsize=12)
        ax.grid(visible=True, alpha=0.3, linestyle='--') # Adds a grid and ensures the graph is displayed, alpha for transparency
        ax.legend(fontsize=14, loc='upper left', facecolor='black', edgecolor='white') #

        # Here we addjust the layout for a better fit
        plt.tight_layout()

        # Here we render the plot in Streamlit
        st.pyplot(fig)
        st.write("The chart shows Temperature (°C) and Windspeed (m/s) across the day at 1-hour intervals.")

        st.text("")  # Adds an empty line
        st.text("")  # Adds another empty line

        # Here we ensure that the 'Time' column is datetime
        weather_data2["Time"] = pd.to_datetime(weather_data2["Time"])


        # Creating a subheader for the plots
        st.subheader("Precipitation")

        # Here we plot the precipitation category
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        ax1.plot(weather_data2["Time"], weather_data2["Precipitation (mm)"], marker='o', markersize=5,
            label='Precipitation (mm)', linestyle='-', linewidth=2, color='lightblue')
        
        ax1.set_xlabel("Time (hours)", fontsize=12)
        ax1.set_ylabel('Precipitation (mm)', fontsize=14)
        locator = mdates.HourLocator(interval=3)  # Tick every 3 hours
        formatter = mdates.DateFormatter('%H:%M')  # Time format
        ax1.xaxis.set_major_locator(locator)
        ax1.xaxis.set_major_formatter(formatter)
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        ax1.tick_params(axis='x', labelsize=10)
        ax1.tick_params(axis='y', labelsize=12)
        ax1.grid(visible=True, alpha=0.3, linestyle='-')
        plt.tight_layout()
        st.pyplot(fig1)

        st.write("This chart shows Precipitation (mm) across the day at 1-hour intervals.")

        st.text("")  # Adds an empty line
        st.text("")  # Adds another empty line



        st.subheader("Solar Irradiation")
        # Here we plot the solar irradiation
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        ax2.plot(weather_data2["Time"], weather_data2["Solar irradiation (watt)"], marker='o', markersize=5,
            label='Solar irradiation (watt)', linestyle='-', linewidth=2, color='orange')
        
        ax2.set_xlabel('Time (hours)', fontsize=14)
        ax2.set_ylabel('Solar Irradiation (watt)', fontsize=14)
        ax2.xaxis.set_major_locator(locator)
        ax2.xaxis.set_major_formatter(formatter)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        ax2.tick_params(axis='x', labelsize=10)
        ax2.tick_params(axis='y', labelsize=12)
        ax2.grid(visible=True, alpha=0.3, linestyle='--')
        plt.tight_layout()
        st.pyplot(fig2)
        st.write("This chart shows Solar Irradiation (watt) across the day at 1-hour intervals.")

        st.text("")  # Adds an empty line
        st.text("")  # Adds another empty line


        # Here we display the air pressure category
        st.subheader("Air Pressure")  #Creates a subheading

        # We are ensuring that 'Time' is included as the index or column in weather_data3
        weather_data3["Time"] = pd.to_datetime(weather_data3["Time"])
        weather_data3 = weather_data3.set_index("Time")

        # Calculate dynamic limits for y-axis
        min_pressure = weather_data3["Luftdruck (hPa)"].min()
        max_pressure = weather_data3["Luftdruck (hPa)"].max()
        margin = 2  # Add a margin of ±2 hPa
        ylim_lower = max(800, min_pressure - margin)  # Ensure lower limit is not below 800
        ylim_upper = min(1050, max_pressure + margin)  # Ensure upper limit is not above 1050

        # Plot (visual representation of data) for Air Pressure
        plt.style.use("dark_background")
        plt.figure(figsize=(10, 5))
        plt.plot(weather_data3.index, weather_data3["Luftdruck (hPa)"], color="skyblue", linewidth=2, marker='o',  markersize=5)
        
        plt.xlabel("Time (hours)", fontsize=12)
        plt.ylabel("Air Pressure (hPa)", fontsize=12)
        plt.ylim(ylim_lower, ylim_upper)
        plt.xticks(rotation=45)
        plt.grid(visible=True, alpha=0.3, linestyle='--')

        # Display the plot in the Streamlit app
        st.pyplot(plt)
        st.write("The chart shows the Air Pressure (hPa) across the day at 1-hour intervals.")

        st.text("")  # Adds an empty line
        st.text("")  # Adds another empty line

        # Here we ensure that the 'Time' column is datetime
        weather_data4["Time"] = pd.to_datetime(weather_data4["Time"])

        # Display relative humidity
        st.subheader("Relative Humidity") # Creates subheading (Assuming weather_data4 is a pandas DataFrame)
        x_ticks = weather_data4["Time"][::3] # Extract every third value from the "Time" column for the x-tick labels
        plt.style.use("dark_background")
        # Plot for relative humidity
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(weather_data4["Time"], weather_data4["rel. Luftfeuchtigkeit (%)"], color="#1f77b4", linewidth=2, marker='o',  markersize=5)
        
        ax.set_xlabel("Time (hours)", fontsize=12)
        ax.set_ylabel("Relative Humidity (%)", fontsize=12)
        ax.set_ylim(0, 105)  # Assuming relative humidity is between 0% and 105%
        ax.set_xticks(x_ticks)  # Set x-ticks every 3 hours
        ax.set_xticklabels(x_ticks, rotation=45)  # Label x-ticks with rotated text
        ax.grid(visible=True, alpha=0.3, linestyle='--')
        st.pyplot(fig) # Display the plot in Streamlit
        st.write("The chart shows the Relative humidity (%) across the day at 1-hour intervals.") 
    
    # if the function cannot be executed, an error message will appear 
    else:
        st.write(error)   

    current_time = datetime.now().time()# Extract only the time component and store it in the variable current_time 
    
    #Creating an if statement to check wheter the current time is between 00.00 and 22.59 because the API's last Datapoint for the features is 23.00 
    # The Waveheight prediciton therefore is not availabe between 23.00 and 23.59
    if datetime.strptime("00:00", "%H:%M").time() <= current_time < datetime.strptime("23:00", "%H:%M").time():

        # Here we are doing the data preparation 
        weather_data.index = pd.to_datetime(weather_data.index) # Ensure the index is a datetime object
        weather_data2['Time'] = pd.to_datetime(weather_data2['Time']) # Ensure the 'Time' column is in datetime format
        weather_data3.index = pd.to_datetime(weather_data3.index) # Ensure the index is a datetime object
        weather_data4['Time'] = pd.to_datetime(weather_data4['Time']) # Ensure the 'Time' column is in datetime format

        # Here we calculate mean values for next 3 hours
        current_time = datetime.now() # Accessing the current time and storing it in a variable
        time_range_end = current_time + timedelta(hours=3) # Define the time range (next 3 hours)
        
        # Next up we filter weather_data for the next 3 hours
        next_3_hours_data = weather_data[(weather_data.index > current_time) & (weather_data.index <= time_range_end)] 

        # Here we calculate the mean temperature and wind speed
        mean_temperature_next_3_hours = next_3_hours_data['Temperature (°C)'].mean() # Calculate the mean temperature for the next 3 hours
        mean_wind_speed_next_3_hours = next_3_hours_data['Wind Speed (m/s)'].mean()  # Calculate the mean wind speed for the next 3 hours

        # Next up we filter weather_data2 for the next 3 hours
        next_3_hours_data_weather2 = weather_data2[
            (weather_data2['Time'] > current_time) & (weather_data2['Time'] <= time_range_end)]

        # Here we calculate mean precipitation and solar irradiation
        mean_precipitation_next_3_hours = next_3_hours_data_weather2['Precipitation (mm)'].mean() # Calculate the mean precipitation for the next 3 hours
        mean_solar_irradiation_next_3_hours = next_3_hours_data_weather2['Solar irradiation (watt)'].mean() # Calculate the mean solar irradiation for the next 3 hours

        time_range_end = current_time + timedelta(hours=3) # Define the time range (next 3 hours)
        

        # Next up we filter weather_data3 for the next 3 hours
        next_3_hours_data_weather3 = weather_data3[(weather_data3.index > current_time) & (weather_data3.index <= time_range_end)] # Filter the DataFrame for the next 3 hours

        # Here we alculate mean pressure for the next 3 hours
        mean_pressure_next_3_hours = next_3_hours_data_weather3['Luftdruck (hPa)'].mean() # Calculate the mean pressure for the next 3 hours

        # Next up we filter weather_data4 for the next 3 hours
        next_3_hours_data_weather4 = weather_data4[
            (weather_data4['Time'] > current_time) & (weather_data4['Time'] <= time_range_end) # Filter the DataFrame for the next 3 hours based on the 'Time' column
        ]
        # Here calculate mean humidity for the next 3 hours
        mean_humidity_next_3_hours = next_3_hours_data_weather4['rel. Luftfeuchtigkeit (%)'].mean() # Calculate the mean relative humidity for the next 3 hours

    
        # Here we predict the wave height
        prediction = model.predict([[mean_temperature_next_3_hours, mean_humidity_next_3_hours, mean_solar_irradiation_next_3_hours, mean_wind_speed_next_3_hours, mean_precipitation_next_3_hours, mean_pressure_next_3_hours]])  # Replace with actual feature values

        # Displaying the calculated wave Prediction
        st.text("")  # Adds an empty line
        st.text("")  # Adds another empty line
        st.text("")
        # Displaying the prediction in a styled dark box with a white title
        st.markdown(f"""
            <div style="border: 1px solid #333; padding: 15px; border-radius: 10px; background-color: #222; text-align: center;">
                <h3 style="color: #fff; margin: 0;">Wave Height Prediction</h3>
                <p style="font-size: 18px; color: #fff; margin: 5px 0;">The predicted wave height in the next 3 hours is:</p>
                <p style="font-size: 24px; font-weight: bold; color: #fff; margin: 0;">{prediction[0]:.2f} meters</p>
            </div>
        """, unsafe_allow_html=True)

    # If the current_time is between 23.00 and 00.00 the Wave height is not available because the API's last Datapoint for the features is 23.00 
    # The Waveheight prediciton therefore is not availabe between 23.00 and 23.59
    #Therefore we display a message that adresses that issue (This wont really be a problem for a User because usually people do not go to the Lake in the night)
    else:
        st.markdown(f"""
<div style="border: 1px solid #333; padding: 15px; border-radius: 10px; background-color: #222; text-align: center;">
    <p style="font-size: 18px; color: #fff; margin: 5px 0;">Wave height predictions are available only between 00:00 and 23:00. Thank you for your understanding.</p>
</div>
""", unsafe_allow_html=True)
    

    st.text("")  # Adds an empty line
    st.text("")  # Adds another empty line
    
    if selected_lake["name"] == "Lake Silvaplanersee":
        # We set up a custom title and description for Silvaplanersee, because we wanted to implement the Silvaplanersee but the webcame link couldn't be displayed
        st.subheader("Link to Webcam")
        st.write("View the Silvaplana Lake Webcam [here](https://www.skylinewebcams.com/de/webcam/schweiz/graubunden/silvaplana/silvaplana-switzerland.html).")
    else:
        # We default the title and embed iframe for other lakes
        st.subheader("Lake Webcam Stream")
        st.write(f"Webcam view of {selected_lake['name']}") # "f", is for the f-string, afterwards with the name we can put out the name of the selected lake
        st.components.v1.iframe(selected_lake["webcam_url"], height=600, scrolling=False) # Let's you embed the website, in our case the webcam, code created with help of discuission platform: (https://discuss.streamlit.io/t/how-do-i-embed-an-existing-non-streamlit-webpage-to-my-streamlit-app/50326/3)

    
    # We generate and display directions link (for this code we used ChatGPT, for proper structuring)
    if "user_location" in st.session_state: # If the user's location is available in session_state, this creates a link to get directions to the selected lake
        directions_link = generate_directions_link( # The gernerate_directions_link function creates the URL using the user's coordinates and the lake's
            st.session_state["user_location"],
            (selected_lake["latitude"], selected_lake["longitude"])
        )
        st.markdown(f"[Get Directions to {selected_lake['name']}]({directions_link})") #displays a clickable link labeled with the lake's name, leading to Google Maps.

    # "Back to Map" button
    # When clicked, it resets selected_lake to None and reloads the page to show the map again
    if st.button("Back to Map"):
        st.session_state.selected_lake = None
        st.experimental_rerun()

# User Input and Map Display (if no lake is selected)
else:
    location = st.text_input("Enter a location (e.g., 'Zurich', 'St. Gallen', 'Lucerne'):")

    
    today = datetime.now() #This sets up a date picker that limits choices from today up to 14 days ahead
    selected_date = st.date_input("Select a date:", today, min_value=today, max_value=today + timedelta(days=14))
    st.session_state.selected_date = selected_date.strftime('%Y-%m-%d') # This line stores the selected date in the YYYY-MM-DD format 

    #Here we created a slider allowing users to choose a radius (20 to 140km) for the lake search area
    radius = st.slider("Select radius (in kilometers):", min_value=20, max_value=140, value=20)

    #This is a list of lake dictionaries each containing the lake's name, coordinates and webcam URL (if available).
    swiss_lakes = [
        {"name": "Lake Zurich", "latitude": 47.232625, "longitude": 8.704907, "webcam_url": "https://rcz.ch/webcam"}, 
        {"name": "Lake Zug", "latitude": 47.177770, "longitude": 8.493900, "webcam_url": "https://zug-stadt.roundshot.com/"},
        {"name": "Lake Aegeri", "latitude": 47.121541, "longitude": 8.630019, "webcam_url": "https://wildspitz.roundshot.com/"},
        {"name": "Lake Vierwaldstettersee", "latitude": 47.000890, "longitude": 8.580360, "webcam_url": "https://www.foto-webcam.eu/webcam/brunnen/"},
        {"name": "Lake Murtensee", "latitude": 46.933720, "longitude": 7.120470 , "webcam_url": "https://morat.roundshot.com/"},
        {"name": "Lake Sempachersee", "latitude": 47.134330, "longitude": 8.192780, "webcam_url": "https://luks-sursee.roundshot.com/"},
        {"name": "Lake Thunersee", "latitude": 46.714520, "longitude": 7.694180, "webcam_url": "https://content.meteobridge.com/cam/77be13b2a74ad2b8bd21d5101c18b18d/camplus.jpg"},
        {"name": "Lake Bielersee Ipsach", "latitude": 47.117030, "longitude": 7.224540, "webcam_url": "https://boezingenberg.roundshot.com/"},
        {"name": "Lake Neuchatel", "latitude": 46.804900, "longitude": 6.734640, "webcam_url": "https://lacdeneuchatel.roundshot.com/"},
        {"name": "Lake Daubensee", "latitude": 46.383659, "longitude": 7.625390, "webcam_url": "https://gemmi.roundshot.com/"},
        {"name": "Lake Bodensee", "latitude": 47.572220, "longitude": 9.377610, "webcam_url": "https://romanshorn.roundshot.com/"},
        {"name": "Lake Luganersee", "latitude": 45.905722, "longitude": 8.972891, "webcam_url": "https://casaberno.roundshot.com/"},
        ]

    #This function returns an appropriate zoom level for the map, depending on the chosen radius
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

    #If a location name was entered, we can use geolocator.geocode to get its coordinates
    if location:
        loc = geolocator.geocode(location)

        # If a location was found, it's saved in session_state and displayed with its coordinates and the selected date
        if loc:
            st.session_state["user_location"] = (loc.latitude, loc.longitude)
            
            st.write(f"**Location:** {loc.address}")
            st.write(f"**Latitude:** {loc.latitude}, **Longitude:** {loc.longitude}")
            st.write(f"**Selected Date:** {selected_date.strftime('%A, %d %B %Y')}")

            # Here we create a folium map centered on the user's location, with a zoom level calculated by calculate_zoom_level 
            zoom_level = calculate_zoom_level(radius)
            
            m = folium.Map(location=[loc.latitude, loc.longitude], zoom_start=zoom_level) # It adds a blue marker showing the user's location
            folium.Marker([loc.latitude, loc.longitude], tooltip=loc.address, icon=folium.Icon(color="blue")).add_to(m)

            # A circle showing the search area (in blue) is drawn around the user's location in the map
            folium.Circle(location=[loc.latitude, loc.longitude],
                radius=radius * 1000,
                color="blue",
                fill=False).add_to(m)

            # This loop calculates the distance between the user's location and each lake
            # If a lake is within the radius, a red marker for that lake is added to the map, with a tooltip showing its name and distance
            for lake in swiss_lakes:
                lake_coords = (lake["latitude"], lake["longitude"])
                location_coords = (loc.latitude, loc.longitude)
                
                distance_to_lake = geodesic(location_coords, lake_coords).km
                
                if distance_to_lake <= radius:
                    marker = folium.Marker(lake_coords,tooltip=f"{lake['name']} ({distance_to_lake:.2f} km away)",
                        icon=folium.Icon(color="red"))
                    
                    marker.add_child(folium.Popup(f"Click here to select {lake['name']}", parse_html=True))
                    marker.add_to(m)
            st_map = st_folium(m, width=700, height=500) # The map is displayed in the app with a width of 700 and a height of 500
            
            # If the user clicks on a lake marker, this checks if any lake in swiss_lake matches the clicked coordinates
            # If a match is found, st.session_state.selected_lake is set to that lake's data and the st.experimental_rerun() reloads the app to show details for the selected lake
            if st_map["last_object_clicked"] is not None:
                clicked_coords = st_map["last_object_clicked"]["lat"], st_map["last_object_clicked"]["lng"] # Tuple containing lat and lng of the choosen location
                for lake in swiss_lakes:
                    if (lake["latitude"], lake["longitude"]) == clicked_coords: # If the lake's coordinates and the clicked coordinates are the same, then the code is executed
                        st.session_state.selected_lake = lake # Storing the lake
                        st.experimental_rerun()
                        break
