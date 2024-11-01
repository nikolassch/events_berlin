
import pandas as pd
import requests
from bs4 import BeautifulSoup

# URL of the Google Sheets published page
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmygydebEruBWt5L_vYwpexFqNXV511pkRKpPu5GWlezhK5LJPutCDOMxES3b4r52E8n9o5WbuDbVE/pubhtml"

# Get the webpage content
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Find all table rows
rows = soup.find_all('tr')

# Initialize lists to store data

dates = []
names = []

# Extract data from rows
for row in rows[1:]:  # Skip header row
    cells = row.find_all('td')
    if len(cells) >= 2:  # Ensure row has enough cells
        date = cells[0].text.strip()
        name = cells[1].text.strip()
        
        if date and name:  # Only add if both date and name exist
            dates.append(date)
            names.append(name)

# Create DataFrame
df = pd.DataFrame({
    'Date': dates,
    'Name': names
})

# Display the first few rows
print(df.head(10))

#################################################################
#################################################################
#################################################################
# Convert German dates to datetime objects
def convert_german_date(date_str):
    try:
        # Split the date string by dots
        parts = date_str.split('.')
        if len(parts) != 3:
            return pd.NA
            
        weekday, day, month = parts
        
        # Dictionary for German and English month abbreviations
        months = {
            # German
            'JAN': '01', 'FEB': '02', 'MÄR': '03', 'APR': '04',
            'MAI': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
            'SEP': '09', 'OKT': '10', 'NOV': '11', 'DEZ': '12',
            # English
            'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
            'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
            'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
        }
        
        # Convert month to number
        month = months[month.upper()]
        
        # Create date string in format DD-MM-YYYY HH:MM (assuming current year)
        current_year = pd.Timestamp.now().year
        date_string = f"{day}-{month}-{current_year} 20:30"
        
        # Convert to datetime including time
        return pd.to_datetime(date_string, format='%d-%m-%Y %H:%M')
    except (ValueError, KeyError, IndexError):
        return pd.NA

# Apply the conversion to the Date column
df['Date'] = df['Date'].apply(convert_german_date)
# Filter out rows where Date is NaT (Not a Time) - these are invalid dates
df = df.dropna(subset=['Date'])

# Add constant link column
df['Link'] = "http://www.donau115.de/"
# add venue name and geolocation
df['Venue'] = "Donau115"
df['Location'] = "Donau115, Donaustraße 115, 12043 Berlin"



#################################################################
#################################################################
#################################################################
# Try to load existing CSV if it exists
csv_filename = f"events_{df['Venue'].iloc[0].lower()}.csv"
try:
    existing_df = pd.read_csv(csv_filename)
    # Convert Date column in existing_df to datetime
    existing_df['Date'] = pd.to_datetime(existing_df['Date'])
    
    # Concatenate existing and new data
    combined_df = pd.concat([existing_df, df])
    
    # Drop duplicates based on Date only, keeping last occurrence (new entries)
    combined_df = combined_df.drop_duplicates(subset=['Date'], keep='last')
    
    # Sort by date
    combined_df = combined_df.sort_values('Date')
    
    # Save combined dataframe
    combined_df.to_csv(csv_filename, index=False)
    print(f"Updated existing data in {csv_filename}")
except FileNotFoundError:
    # If file doesn't exist, save new dataframe
    df.to_csv(csv_filename, index=False)
    print(f"Created new file {csv_filename}")



