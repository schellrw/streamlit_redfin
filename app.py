#Import Python Libraries
import pandas as pd
import datetime as dt
import folium
import geopandas as gpd
from folium.features import GeoJsonPopup, GeoJsonTooltip
import streamlit as st
from streamlit_folium import folium_static

@st.cache_data
def read_csv(path):
    return pd.read_csv(path, compression='gzip', sep='\t', quotechar='"')

housing_price_df = read_csv('./input/state_market_tracker.tsv000.gz')
housing_price_df = housing_price_df[['period_begin','period_end','period_duration','property_type','median_sale_price','median_sale_price_yoy','homes_sold','state_code']]
housing_price_df = housing_price_df[(housing_price_df['period_begin']>='2022-09-01') & (housing_price_df['period_begin']<='2023-09-01')]

@st.cache_data
def read_file(path):
    return gpd.read_file(path)

#Read the geojson file
# gdf = read_file('./input/georef-united-states-of-america-state.geojson')
gdf = read_file('./input/georef-united-states-of-america-state.geojson')

#Merge the housing market data and geojson file into one dataframe
df_final = gdf.merge(housing_price_df, left_on="ste_stusps_code", right_on="state_code", how="outer").reset_index(drop=True)
df_final = df_final[['period_begin','period_end','period_duration','property_type','median_sale_price','median_sale_price_yoy',
                     'homes_sold','state_code','geometry']] #'ste_code','ste_name','ste_area_code','ste_type','ste_stusps_code'
df_final = df_final[~df_final['period_begin'].isna()].reset_index(drop=True)


####df = df_final.drop(['ste_code', 'ste_name', 'ste_area_code', 'ste_type', 'ste_stusps_code'], axis=1)
df_final = df_final.rename(columns={'period_begin':"Month",'property_type':"Type of Property",'median_sale_price':"Median Sale Price",
                                    'median_sale_price_yoy':"Median Sale Price YoY",'homes_sold':"Homes Sold",'state_code':"State",
                                    'geometry':"Location"})
df_final['Month'] = pd.to_datetime(df_final['Month'], format='%Y-%m')

#Add sidebar to the app
st.sidebar.markdown("### Redfin Housing Data")
st.sidebar.markdown("This app is built using Streamlit to help visualize activity in the U.S. real estate market. Data provided by Redfin, a national real estate brokerage: https://www.redfin.com/news/data-center/")
st.sidebar.markdown("Developed by Robert Schell: https://github.com/schellrw")
#Add title and subtitle to the main interface of the app
st.title("U.S. Real Estate Activity Heatmap")
st.markdown("Where are the hottest housing markets in the U.S.?  Select the housing market metrics you are interested in and your insights are just a couple clicks away.") # Hover over the map to view more details.")

#Create three columns/filters
col1, col2, col3, col4 = st.columns(4)

with col1:
     period_list = df_final['Month'].unique().tolist()
     period_list.sort(reverse=True)
     year_month = st.selectbox("Select Year-Month", period_list, index=0)

with col2:
     state_list = df_final['State'].unique().tolist()
     state = st.selectbox("Select State", state_list, index=0)

with col3:
     prop_type = st.selectbox(
                "View by Property Type", ['All Residential', 'Single Family Residential', 'Townhouse','Condo/Co-op','Single Units Only','Multi-Family (2-4 Unit)'] , index=0)

with col4:
     metrics = st.selectbox("Select Housing Metrics", ["Median Sale Price","Median Sale Price YoY", "Homes Sold"], index=0)

#Update the data frame accordingly based on user input
df_final = df_final[df_final["Month"]==year_month]
df_final = df_final[df_final["State"]==state]
df_final = df_final[df_final["Type of Property"]==prop_type]
df_final = df_final[["Month", "State", "Type of Property", "Median Sale Price", "Median Sale Price YoY", "Homes Sold", metrics]] #,'geometry']]

#st.write(df_final)

#Initiate a folium map
m = folium.Map(location=[40, -100], zoom_start=4,tiles=None)
folium.TileLayer('CartoDB positron',name="Light Map",control=False).add_to(m)

#Plot Choropleth map using folium
choropleth1 = folium.Choropleth(
    geo_data='./input/georef-united-states-of-america-state.geojson',       # Geojson file for the United States
    name='Choropleth Map of U.S. Housing Prices',
    data=df_final,                                                          # df from the data preparation and user selection
    columns=["State", metrics],                                             # 'state code' and 'metrics' to get the median sales price for each state
    key_on='feature.properties.State', #.ste_stusps_code',                            # key in the geojson file that we use to grab each state boundary layers
    fill_color='YlGn',
    nan_fill_color="White",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Housing Market Metrics',
    highlight=True,
    line_color='black').geojson.add_to(m)

folium_static(m)

#Add tooltips to the map
geojson1 = folium.features.GeoJson(
               data=df_final,
               name='United States Housing Prices',
               smooth_factor=2,
               style_function=lambda x: {'color':'black','fillColor':'transparent','weight':0.5},
               tooltip=folium.features.GeoJsonTooltip(
                   fields=["Month",
                           "State",
                           metrics+':',],
                   aliases=['period_begin',
                           'ste_stusps_code',
                            metrics+':'],
                   localize=True,
                   sticky=False,
                   labels=True,
                   style="""
                       background-color: #F0EFEF;
                       border: 2px solid black;
                       border-radius: 3px;
                       box-shadow: 3px;
                   """,
                   max_width=800,),
                    highlight_function=lambda x: {'weight':3,'fillColor':'grey'},
                   ).add_to(m)