#Import Python Libraries
import pandas as pd
import numpy as np
import datetime as dt
import folium
import geopandas as gpd
import streamlit as st
from streamlit_folium import folium_static

@st.cache_data
def read_csv(path):
    return pd.read_csv(path, compression='gzip', sep='\t', quotechar='"')

housing_price_df = read_csv('./input/state_market_tracker.tsv000.gz')
housing_price_df = housing_price_df[['period_begin','period_end','period_duration','property_type','median_sale_price','median_sale_price_yoy','homes_sold','state_code']]
#housing_price_df = housing_price_df[(housing_price_df['period_begin']>='2022-07-01') & (housing_price_df['period_begin']<='2023-07-01')]

@st.cache_data
def read_file(path):
    return gpd.read_file(path)

#Read the geojson file
gdf = read_file('./input/georef-united-states-of-america-state.geojson')

#Merge the housing market data and geojson file into one dataframe
df_final = gdf.merge(housing_price_df, left_on="ste_stusps_code", right_on="state_code", how="outer").reset_index(drop=True) #, inplace=True)
df_final = df_final.drop(['ste_code','ste_name','ste_area_code','ste_type','ste_fp_code'], axis=1)
df_final = df_final.rename(columns={'period_begin':"Period",'property_type':"Type of Property",'median_sale_price':"Median Sale Price",
                                    'median_sale_price_yoy':"Median Sale Price YoY",'homes_sold':"Homes Sold",'state_code':"State"})

#### MUST KEEP AS FLOATS, NO INT
# df_final["Median Sale Price"] = df_final["Median Sale Price"].astype(int)   
# df_final["Median Sale Price YoY"] = df_final["Median Sale Price YoY"].astype(int)
# df_final["Homes Sold"] = df_final["Homes Sold"].astype(int)
#### MUST KEEP AS FLOATS, NO INT
df_final["Month"] = pd.to_datetime(df_final["Period"], format='%Y-%m-%d').dt.to_period('M')
#df_final["Month"] = df_final["Month"].astype(str) ##(int) ####pd.to_datetime(df_final['Month'], format='%b %Y')

#Add sidebar to the app
st.sidebar.markdown("# Redfin Housing Data")
##st.sidebar.markdown("## July 2022 to July 2023")
st.sidebar.markdown("""## Developed by Artificial Intelligentsia, LLC
                       ## AI/ML Technology & Modernization Specialists""")
#st.sidebar.markdown("## AI/ML Technology & Modernization Specialists")
st.sidebar.markdown("https://artificialintelligentsia.com/")
st.sidebar.markdown("public github repo:  https://github.com/schellrw/streamlit_redfin")
st.sidebar.markdown("RW Schell github:    https://github.com/schellrw/")
st.sidebar.markdown("RW Schell linkedIn:  https://linkedin.com/in/schellr/")
st.sidebar.markdown("Data provided by Redfin, a national real estate brokerage:  https://www.redfin.com/news/data-center")
st.sidebar.markdown("This app was built using Python and Streamlit to visualize activity in the United States real estate market.")
##st.sidebar.markdown("MIT License Copyright (c) 2023 Robert W Schell")

# st.sidebar.markdown("Email: schell.rw@gmail.com")
#Add title and subtitle to the main interface of the app
st.title("Redfin U.S. Real Estate Heatmap")

#st.markdown("## Competitive intelligence and easy-to-use technology platforms are just a click away.") # Hover over the map to view more details.")
st.subheader("Insights from public data resources coupled with your proprietary business information.")
st.markdown("#### What markets are you in?  What metrics matter to you?  How do you want your business to grow?  How far do you want to go?")
st.markdown("#### Competitive intelligence for your business from streamlined and affordable technology solutions are just a click away:  https://artificialintelligentsia.com/") ## FIX CONTACT PAGE NAME:: https://artificialintelligentsia.com/?page_id=21")
st.markdown("##### MIT License Copyright (c) 2023 Robert W Schell")

#Create three columns/filters
col1, col2, col3 = st.columns(3) ########), col4 = st.columns(4)

with col1:
     period_list = df_final['Month'].unique().tolist()
     period_list.sort(reverse=True)
     year_month = st.selectbox("Select Year-Month", period_list, index=0)

# with col2:
#      state_list = df_final['State'].astype(str).unique().tolist()
#      state_sorted = sorted(state_list) # state_list.sort(reverse=False)
#      state = st.selectbox("Select State", state_sorted, index=0)

with col2:
     prop_type = st.selectbox("View by Property Type", ['All Residential','Single Family Residential','Townhouse',
                                                'Condo/Co-op','Single Units Only','Multi-Family (2-4 Unit)'], index=0)

with col3:
     metrics = st.selectbox("Select Housing Metrics", ["Median Sale Price","Median Sale Price YoY", "Homes Sold"], index=0)

# update data frame based on user selections
df_final = df_final[df_final["Month"]==year_month]
#df_final = df_final[df_final["State"]==state]
df_final = df_final[df_final["Type of Property"]==prop_type]
df_final = df_final[["Month", 'ste_stusps_code', "Type of Property", metrics,'geometry']] #,'ste_stusps_code']]

# @st.cache_data
# def write_df(df):
#     dfx = st.write(df)
#     return dfx

# # Output write info
# df_io = write_df(df_final) 
# df_io

#Initiate a folium map
m = folium.Map(location=[40, -96], zoom_start=4,tiles=None)
folium.TileLayer('CartoDB positron', name="Light Map", control=False).add_to(m)
## Other map layers:
##folium.TileLayer('DarkMatter',name="Dark Map",control=False).add_to(m) #### folium.TileLayer('OpenStreetMap').add_to(m)

#Plot Choropleth map using folium
choropleth1 = folium.Choropleth(
    geo_data='./input/georef-united-states-of-america-state.geojson', ##df_final.to_json(),  ####  # Geojson file for the United States
    name="Choropleth (Heat Map) of U.S. Housing Prices",
    data=df_final, # df from the data preparation and user selection
    columns=['ste_stusps_code', metrics], # Or "State" now is key? # 'state code' and 'metrics' to get the median sales price for each state
    key_on='feature.properties.ste_stusps_code',  # key in the geojson file that we use to grab each state boundary layers
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
               data=df_final['geometry'],
               name='United States Housing Prices',
               smooth_factor=2,
               style_function=lambda x: {'color':'black','fillColor':'transparent','weight':0.5},
               tooltip=folium.features.GeoJsonTooltip(
                   fields=["Month",
                           "state_code",
                           metrics,],
                   aliases=['Period',
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

#st.write(df_final) 