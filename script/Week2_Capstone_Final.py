#IBM Data Science Capstone Project Final Notebook
#Topic : Opening a new Bermese Restaurant in Toronto
#In this notebook, I will be creating clusters to find the most suitable location to open an authentic Burmese restaurant in Toronto, Canada.
#importing necessary libraries
import requests
import pandas as pd

#scrapping neighborhoods in Canada
url  = "https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_M"
page = requests.get(url)
if page.status_code == 200:
    print('Page download successful')
else:
    print('Page download error. Error code: {}'.format(page.status_code))

df_html = pd.read_html(url, header=0, na_values = ['Not assigned'])[0]
df_html.head()

#Drop the the rows on which the Borough is empty
df_html.dropna(subset=['Borough'], inplace=True)

#Check Neighborhood is empty but Borough exists
n_empty_neighborhood = df_html[df_html['Neighbourhood'].isna()].shape[0]
print('Number of rows on which Neighborhood column is empty: {}'.format(n_empty_neighborhood))

#Show which neighborhood is emtpy but Borough exists
df_html[df_html['Neighbourhood'].isna()]

#Replace empty Neighborhood with Borough name and check again
df_html['Neighbourhood'].fillna(df_html['Borough'], inplace=True)
n_empty_neighborhood = df_html[df_html['Neighbourhood'].isna()].shape[0]
print('Number of rows on which Neighborhood column is empty: {}'.format(n_empty_neighborhood))

#Confirm that Queen's Park Neighborhood is not empty now:
df_html[df_html['Borough']=="Queen's Park"]


#Group by Postcode / Borough
df_postcodes = df_html.groupby(['Postcode','Borough']).Neighbourhood.agg([('Neighbourhood', ', '.join)])
df_postcodes.reset_index(inplace=True)
df_postcodes.head(5)

#Drop the the rows on which the Borough is empty
df_html.dropna(subset=['Borough'], inplace=True)


#Check Neighborhood is empty but Borough exists
n_empty_neighborhood = df_html[df_html['Neighbourhood'].isna()].shape[0]
print('Number of rows on which Neighborhood column is empty: {}'.format(n_empty_neighborhood))

print('The shape of the dataset is:',df_postcodes.shape)

#to make it easier, we will store this in csv format.
#Export to .CSV
df_postcodes.to_csv('Toronto_Postcodes.csv')

import numpy as np

#Since GeoEncoder library is not working for me, I will use the csv file downloaded

#Read CSV file from link and load into dataframe
url_csv = 'http://cocl.us/Geospatial_data'
df_coordinates = pd.read_csv(url_csv)
df_coordinates.head()

#use the previously cleaned data
df_neighborhoods = pd.read_csv('Toronto_Postcodes.csv',index_col=[0])
df_neighborhoods.head()

# Make sure both dataframes have the same
df_coordinates.rename(columns={'Postal Code': 'PostalCode'}, inplace=True)
df_neighborhoods.rename(columns={'Postcode': 'PostalCode'}, inplace=True)

# Merge both datasets
df_neighborhoods_coordinates = pd.merge(df_neighborhoods, df_coordinates, on='PostalCode')
df_neighborhoods_coordinates.head()


# Check coordinates for a couple of neighborhoods
df_neighborhoods_coordinates[(df_neighborhoods_coordinates['PostalCode']=='M5G') |
                             (df_neighborhoods_coordinates['PostalCode']=='M2H') ]

#Export to .CSV
df_neighborhoods_coordinates.to_csv('Toronto_Postcodes_2.csv')

import folium
from sklearn.cluster import KMeans

# Read .csv file from above
df = pd.read_csv('Toronto_Postcodes_2.csv', index_col=0)
df.head()

print('The dataframe has {} boroughs and {} neighborhoods.'.format(
        len(df['Borough'].unique()),
        df.shape[0]
    )
)

df.rename(columns={'Neighbourhood': 'Neighborhood'}, inplace=True)

#count Bourough and Neighborhood
df.groupby('Borough').count()['Neighborhood']

df_toronto = df[df['Borough'].str.contains('Toronto')]
df_toronto.reset_index(inplace=True)
df_toronto.drop('index', axis=1, inplace=True)
df_toronto.head()

#Check the number of neighborhoods
print(df_toronto.groupby('Borough').count()['Neighborhood'])

#Create list with the Boroughs (to be used later)
boroughs = df_toronto['Borough'].unique().tolist()

#Obtain the coordinates from the dataset itself, just averaging Latitude/Longitude of the current dataset
lat_toronto = df_toronto['Latitude'].mean()
lon_toronto = df_toronto['Longitude'].mean()
print('The geographical coordinates of Toronto are {}, {}'.format(lat_toronto, lon_toronto))

borough_color = {}
for borough in boroughs:
    borough_color[borough]= '#%02X%02X%02X' % tuple(np.random.choice(range(256), size=3)) #Random color

map_toronto = folium.Map(location=[lat_toronto, lon_toronto], zoom_start=12)

# add markers to map
for lat, lng, borough, neighborhood in zip(df_toronto['Latitude'],
                                           df_toronto['Longitude'],
                                           df_toronto['Borough'],
                                           df_toronto['Neighborhood']):
    label_text = borough + ' - ' + neighborhood
    label = folium.Popup(label_text)
    folium.CircleMarker(
        [lat, lng],
        radius=5,
        popup=label,
        color=borough_color[borough],
        fill_color=borough_color[borough],
        fill_opacity=0.7).add_to(map_toronto)

map_toronto

#Getting Venues Data using Foursquare

CLIENT_ID = 'FA3UWXA2U22BVWCDRPK03KA4SVQE1G25TQMDNWFT0AT2QT4R' # Foursquare ID
CLIENT_SECRET = '1NG3HBLRHRTBJX52JFBST0KTIWTGGRIJMDNIHQNJEBM0RXDQ' # Foursquare Secret
VERSION = '' # Foursquare API version
LIMIT = 100 # limit of number of venues returned by Foursquare API
radius = 500 # define radius

def getNearbyVenues(names, latitudes, longitudes, radius=500):

    venues_list=[]
    for name, lat, lng in zip(names, latitudes, longitudes):
        print(name)

        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
            CLIENT_ID,
            CLIENT_SECRET,
            VERSION,
            lat,
            lng,
            radius,
            LIMIT)

        # make the GET request
        results = requests.get(url).json()["response"]['groups'][0]['items']

        # return only relevant information for each nearby venue
        venues_list.append([(
            name,
            lat,
            lng,
            v['venue']['name'],
            v['venue']['location']['lat'],
            v['venue']['location']['lng'],
            v['venue']['categories'][0]['name']) for v in results])

    nearby_venues = pd.DataFrame([item for venue_list in venues_list for item in venue_list])
    nearby_venues.columns = ['Neighborhood',
                  'Neighborhood Latitude',
                  'Neighborhood Longitude',
                  'Venue',
                  'Venue Latitude',
                  'Venue Longitude',
                  'Venue Category']

    return(nearby_venues)

#Get venues for all neighborhoods in our dataset
toronto_venues = getNearbyVenues(names=df_toronto['Neighborhood'],
                                latitudes=df_toronto['Latitude'],
                                longitudes=df_toronto['Longitude'])

#Check size of resulting dataframe
toronto_venues.shape

toronto_venues.head()

#Number of venues per neighborhood
toronto_venues.groupby('Neighborhood').count()

#Number of unique venue categories
print('There are {} uniques categories.'.format(len(toronto_venues['Venue Category'].unique())))

#print out the list of categories
toronto_venues['Venue Category'].unique()[:100]

# check if the results contain "Thai Restaurants"
#please note I changed the data to Thai because I was previously writing the code using Asian but the number is so small
"Thai Restaurant" in toronto_venues['Venue Category'].unique()

#Analyse each neighborhoods
# one hot encoding
to_onehot = pd.get_dummies(toronto_venues[['Venue Category']], prefix="", prefix_sep="")

# add neighborhood column back to dataframe
to_onehot['Neighborhoods'] = toronto_venues['Neighborhood']

# move neighborhood column to the first column
fixed_columns = [to_onehot.columns[-1]] + list(to_onehot.columns[:-1])
to_onehot = to_onehot[fixed_columns]

print(to_onehot.shape)
to_onehot.head()

#Next, let's group rows by neighborhood and by taking the mean of the frequency of occurrence of each category

to_grouped = to_onehot.groupby(["Neighborhoods"]).mean().reset_index()

print(to_grouped.shape)
to_grouped

len(to_grouped[to_grouped["Thai Restaurant"] > 0])

#Create a new dataframe to find Asian Restaurants only

to_asian = to_grouped[["Neighborhoods","Thai Restaurant"]]
to_asian.head()

#Cluster Neighborhoods
#Run k-means to cluster the neighborhoods in Toronto into 3 clusters.

# set number of clusters
toclusters = 3

to_clustering = to_asian.drop(["Neighborhoods"], 1)

# run k-means clustering
kmeans = KMeans(n_clusters=toclusters, random_state=0).fit(to_clustering)

# check cluster labels generated for each row in the dataframe
kmeans.labels_[0:10]

# create a new dataframe that includes the cluster as well as the top 10 venues for each neighborhood.
to_merged = to_asian.copy()

# add clustering labels
to_merged["Cluster Labels"] = kmeans.labels

to_merged.rename(columns={"Neighborhoods": "Neighborhood"}, inplace=True)
to_merged.head()

# merge toronto_grouped with toronto_data to add latitude/longitude for each neighborhood
to_merged = to_merged.join(toronto_venues.set_index("Neighborhood"), on="Neighborhood")

print(to_merged.shape)
to_merged.head()

# sort the results by Cluster Labels
print(to_merged.shape)
to_merged.sort_values(["Cluster Labels"], inplace=True)
to_merged

#Visualize the cluster
# Matplotlib and associated plotting modules
import matplotlib.cm as cm
import matplotlib.colors as colors

# create map
map_clusters = folium.Map(location=[lat_toronto, lon_toronto], zoom_start=11)

# set color scheme for the clusters
x = np.arange(toclusters)
ys = [i+x+(i*x)**2 for i in range(toclusters)]
colors_array = cm.rainbow(np.linspace(0, 1, len(ys)))
rainbow = [colors.rgb2hex(i) for i in colors_array]

# add markers to the map
markers_colors = []
for lat, lon, poi, cluster in zip(to_merged['Neighborhood Latitude'], to_merged['Neighborhood Longitude'], to_merged['Neighborhood'], to_merged['Cluster Labels']):
    label = folium.Popup(str(poi) + ' - Cluster ' + str(cluster))
    folium.CircleMarker(
        [lat, lon],
        radius=5,
        popup=label,
        color=rainbow[cluster-1],
        fill_color=rainbow[cluster-1],
        fill_opacity=0.7).add_to(map_clusters)

map_clusters

# save the map as HTML file
map_clusters.save('map_clusters.html')

#Examine the clusters
#Cluster 0
to_merged.loc[to_merged['Cluster Labels'] == 0]

#Cluster 1
to_merged.loc[to_merged['Cluster Labels'] == 1]

#Cluster 2
to_merged.loc[to_merged['Cluster Labels'] == 2]

#Observations
#Most of Thai restaurants are in Cluster 2 which is around Adelaide, King, Richmond areas and lowest (close to zero) in Cluster 1 areas which are North Toronto West and
#Parkdale areas. Also, there are good opportunities to open near Chinatown, St James town as the competition seems to be low. Looking at nearby venues, it seems Cluster 1
# might be a good location as there are not a lot of Asian restaurants in these areas. Therefore, this project recommends the entrepreneur to open an authentic Burmese
#restaurant in these locations with little to no competition. Nonetheless, if the food is authentic, affordable and good taste, I am confident that it will have great
# following everywhere =)
