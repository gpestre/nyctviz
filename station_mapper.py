import json
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.patches import Polygon

__version__ = '2.0'

class StationMapper:

    """
        Produce maps on the New York City Transit routes and stations (represented by a circle of the specificed size).
    """

    def __init__(self):

        """
            Initialize a mapper of NYC boroughs, subway routes, and stations.
        """
       
        # Read basemap data:
        with open("nyctviz/data/basemap/BoroughBoundaries.geojson") as json_file:
            geo_json = json.load(json_file) # or geojson.load(json_file)
       
        # Prepare basemap data:
        boroughs = {}
        for f in range(len(geo_json['features'])):
            feature = geo_json['features'][f]
            boro_name = feature['properties']['boro_name']
            assert feature['type']=='Feature'
            for m in range(len(feature['geometry']['coordinates'])):
                multipoly = feature['geometry']['coordinates'][m]
                assert feature['geometry']['type']=='MultiPolygon'
                for poly in multipoly:
                    if boro_name not in boroughs: 
                        boroughs[boro_name] = []
                    boroughs[boro_name].append(poly)
       
        # Read GTFS data:
        shapes = pd.read_csv('nyctviz/data/gtfs/shapes.csv')
        trips = pd.read_csv('nyctviz/data/gtfs/trips.csv')
        routes = pd.read_csv('nyctviz/data/gtfs/routes.csv')
        stops = pd.read_csv('nyctviz/data/gtfs/stops.csv')
       
        # Prepare GTFS data:
        corridors = shapes.copy()
        corridors['route_id'] = [shape_id.split('.')[0] for shape_id in corridors['shape_id']]
        corridors = corridors.merge(routes,left_on=['route_id'],right_on=['route_id'],how='left')
        #corridors['route_color'] = ["" if pd.isnull(route_color) else "#"+route_color.replace('#','') for route_color in corridors['route_color']]
        ## Get colors from GTFS:
        #route_colors = routes.set_index(['route_id'])['route_color'].to_dict()
        #route_colors = {k:("#000000" if pd.isnull(v) else "#"+v) for k,v in route_colors.items()}
        # Use hard-coded colors:
        route_colors = {
            "1"  : "#EE352E",
            "2"  : "#EE352E",
            "3"  : "#EE352E",
            "4"  : "#00933C",
            "5"  : "#00933C",
            "5X" : "#00933C",
            "6"  : "#00933C",
            "6X" : "#00A65C",
            "7"  : "#B933AD",
            "7X" : "#B933AD",
            "A"  : "#2850AD",
            "C"  : "#2850AD",
            "E"  : "#2850AD",
            "B"  : "#FF6319",
            "D"  : "#FF6319",
            "F"  : "#FF6319",
            "M"  : "#FF6319",
            "V"  : "#FF6319",
            "G"  : "#6CBE45",
            "J"  : "#996633",
            "Z"  : "#996633",
            "L"  : "#A7A9AC",
            "N"  : "#FCCC0A",
            "Q"  : "#FCCC0A",
            "R"  : "#FCCC0A",
            "W"  : "#FCCC0A",
            "GS" : "#6D6E71",
            "FS" : "#6D6E71",
            "H"  : "#6D6E71",
            "S"  : "#6D6E71",
            "SI" : "#0F2B51",
        }
        corridors['route_color'] = [route_colors[route_id] for route_id in corridors['route_id']]
        corridors = corridors[['shape_id','shape_pt_sequence','shape_pt_lat','shape_pt_lon','route_id','route_color']].drop_duplicates()
       
        # Prepare location data:
        locations = stops[stops['location_type']==1][['stop_id','stop_name','stop_lat','stop_lon']].reset_index(drop=True)
        locations = locations.rename(columns={'stop_id':'location_id','stop_name':'location_name','stop_lat':'location_lat','stop_lon':'location_lon'})
       
        # Store internal data:
        self._boroughs = boroughs
        self._corridors = corridors
        self._locations = locations

        return None

    def draw(self,sizes=None,colors=None,fig=None,ax=None,route_list=None,location_list=None,location_labels=None):

        """
            Draw a basemap with subway routes, and represent data about each station with a disc of the specified size.

            `sizes` (optional) :
                A dictionary where each key is a location_id and each value is a number (corresponding to the radius of the marker).

            `colors` (optional) :
                A dictionary where each key is a location_id and each value is a string (corresponding to the color of the marker).

            `fig`, `ax` (optional) : 
                A figure and axes in which to plot 

        """

        # Load internal data:
        boroughs = self._boroughs
        corridors = self._corridors
        locations = self._locations

        # Default: Draw all routes:
        if route_list is None:
            route_list = corridors['route_id'].unique()
        elif route_list is True:
            route_list = corridors['route_id'].unique()
        elif route_list is False:
            route_list = []

        # Default: Draw all locations:
        if location_list is None:
            location_list = locations['location_id'].unique()
        elif location_list is True:
            location_list = locations['location_id'].unique()
        elif location_list is False:
            location_list = []

        # Default: If no labels are specified, label all points for which data is specified (or none if no data is specified)
        if location_labels is None:
            if sizes is None:
                location_labels = []
            else:
                location_labels = [location_id for location_id in sizes]
        
        # Default: If no data is specified, plot equal-sized dots (radius=1) for all locations:
        if sizes is None:
            sizes = {location_id:1 for location_id in locations['location_id']}
        
        # Default: If no data is specified, use default color:
        if colors is None:
            colors = {}

        # Build data frame:
        data = []
        for i,row in locations.iterrows():
            location_id = row['location_id']
            lon = row['location_lon']
            lat = row['location_lat']
            color = colors[location_id] if (location_id in colors) else "gray"
            area = sizes[location_id] if (location_id in sizes) else 0
            radius = math.sqrt(area/math.pi)
            label = row['location_name'] if (location_id in location_labels) else ""
            data.append({
                'location_id' : location_id,
                'lon' : lon,
                'lat' : lat,
                'area' : area,
                'radius' : radius,
                'color' : color,
                'label' : label,
            })
        data = pd.DataFrame(data,columns=[
            'location_id',
            'lon',
            'lat',
            'area',
            'radius',
            'color',
            'label',
        ])
        data = data.sort_values(['radius'],ascending=False).reset_index(drop=True)  # Plot largest circles first.

        # Create plot:
        if (ax is not None):
            fig = ax.figure
        elif (fig is not None):
            ax = fig.axes[0]
        else:
            fig,ax = plt.subplots(1,1,figsize=(20,20))

        # Adjust axes:
        ax.axis('off')
        ax.set_aspect(aspect='equal')
        #ax.set_aspect(aspect='equal',adjustable='datalim')
       
        # Plot basemap:
        for feature_id in boroughs:
            multipoly = boroughs[feature_id]
            for poly in multipoly:
                patch = Polygon(poly,closed=True,facecolor='whitesmoke',edgecolor='black',alpha=1,zorder=1)
                ax.add_patch( patch )
       
        # Plot corridors:
        for i,grp in corridors.groupby(['shape_id']):
            route_id = grp['route_id'].iloc[0]
            route_color = grp['route_color'].iloc[0]
            if route_id in route_list:
                ax.plot( grp['shape_pt_lon'],grp['shape_pt_lat'], color=route_color,linewidth=1.5,alpha=1,zorder=2 )

        # Add background layer and masking layer:
        #xmin,xmax = ax.get_xlim()
        #ymin,ymax = ax.get_ylim()
        xmin = -74.283370478116183
        xmax = -73.672229948907159
        ymin = 40.475144526128858
        ymax = 40.936503645041562
        ax.add_patch( Polygon( [(xmin,ymin),(xmin,ymax),(xmax,ymax),(xmax,ymin)] ,closed=True,facecolor='aliceblue',alpha=1,zorder=0) )
        ax.add_patch( Polygon( [(xmin,ymin),(xmin,ymax),(xmax,ymax),(xmax,ymin)] ,closed=True,facecolor='white',alpha=0.5,zorder=2.5) )
       
        # Plot stations:
        for i,row in data.iterrows():
            lon = row['lon']
            lat = row['lat']
            radius = row['radius']/400
            color = row['color']
            label = row['label']
            ax.add_patch( Circle((lon,lat),radius=radius,facecolor=color,edgecolor='black',alpha=1,zorder=3) )
            ax.text( lon+0.002+radius,lat, label, ha='left',va='center',color='black',fontsize=8,alpha=1,zorder=4 )

        # Adjust extents:
        #max.autoscale_view()
        ax.set_xlim((xmin,xmax))
        ax.set_ylim((ymin,ymax))

        # Store data tables as figure properties:
        fig.data = data

        return fig

    @property
    def corridors(self):
        """Returns a pandas dataframe of the NYCT route corridors."""
        return self._corridors

    @property
    def locations(self):
        """Returns a pandas dataframe of the NYCT locations (stations)."""
        return self._locations
