def get_bus_stop_frequency(gtfs_file_path, service_date, output_shapefile_path):

	#importing_modules
	import pandas as pd
	import geopandas as gpd
	import matplotlib.pyplot as plt
	import seaborn as sns
	import numpy as np
	import contextily as ctx
	import pyproj
	from shapely.geometry import Point, LineString
	from zipfile import ZipFile, Path
	import datetime

	#Loading_gtfs_file

	with ZipFile(gtfs_file_path) as myzip:

	    stops_df = pd.read_csv(myzip.open("stops.txt"), dtype={ 
	    'stop_id': 'str', 
	    'stop_code': 'str',
	    'stop_name': 'str',
	    'stop_desc' : 'str',                                              
	    'stop_lat': 'float',
	    'stop_lon': 'float',
	    'location_type': 'Int64',
	    'parent_station': 'str',
	    'wheelchair_boarding': 'str', 
	    'platform_code': 'str',
	    'zone_id': 'str',
	    'level_id' : 'str'
	    })
	    
	    
	    stop_times_df = pd.read_csv(myzip.open("stop_times.txt"), dtype={
	        'trip_id': 'str',
	        'arrival_time': 'str',
	        'stop_id': 'str', 
	        'departure_time': 'str', 
	        'stop_id': 'str',
	        'stop_sequence': 'Int64',
	        'stop_headsign': 'str',
	        'pickup_type': 'Int64',
	        'drop_off_type': 'Int64',
	    })

	    routes_df = pd.read_csv(myzip.open("routes.txt"), dtype={
	        'route_id': 'str',  
	        'agency_id': 'str',  
	        'route_short_name': 'str',  
	        'route_long_name': 'str', 
	        'route_desc': 'str', 
	        'route_type': 'Int64',
	        'route_color': 'str',  
	        'route_text_color': 'str', 
	        'rout_desc': 'str'
	    })
	    
	    trips_df = pd.read_csv(myzip.open("trips.txt"), dtype={
	        'route_id': 'str', 
	        'service_id': 'str',  
	        'trip_id': 'str',
	        'shape_id': 'str', 
	        'trip_headsign': 'str',
	        'trip_short_name': 'str',
	        'direction_id': 'Int64',  
	        'block_id': 'str',
	        'shape_id': 'str',
	        'wheelchair_accessible': 'str',  
	        'bikes_allowed': 'str'
	    })
	    
	    shapes_df = pd.read_csv(myzip.open("shapes.txt"), dtype={
	        'shape_id': 'str', 
	        'shape_pt_lat': 'float', 
	        'shape_pt_lon': 'float',  
	        'shape_pt_sequence': 'Int64'
	    })

	    calendar_df = pd.read_csv(myzip.open("calendar.txt"), dtype={
	        'service_id': 'str',  
	        'monday': 'bool',  
	        'tuesday': 'bool',  
	        'wednesday': 'bool',  
	        'thursday': 'bool',  
	        'friday': 'bool', 
	        'saturday': 'bool',  
	        'sunday': 'bool',  
	        'start_date': 'str', 
	        'end_date': 'str',
	    })
	    
	    calendar_dates_df = pd.read_csv(myzip.open("calendar_dates.txt"), dtype={
	        'service_id': 'str',  
	        'date': 'str',
	        'exception_type': 'Int64',
	    })
	    
	    agency_df = pd.read_csv(myzip.open("agency.txt"), dtype={
	        'agency_id': 'str', 
	        'agency_name': 'str', 
	        'agency_url': 'str',  
	        'agency_timezone': 'str',
	        'agency_lang': 'str', 
	        'agency_phone': 'str',
	    })

	#getting services available in the date and filtering bus data

	show_date_str = service_date

	date = datetime.datetime.strptime(show_date_str, "%Y-%m-%d")
	date_string = date.strftime("%Y%m%d")
	day_of_week_name = date.strftime('%A').lower()

	services_for_day_1 = calendar_df[(calendar_df[day_of_week_name]) & (date_string >= calendar_df.start_date) & (date_string <= calendar_df.end_date)].service_id.to_numpy()

	services_added_for_day = calendar_dates_df[(calendar_dates_df.date == date_string) & (calendar_dates_df.exception_type == 1)].service_id.to_numpy()
	services_removed_for_day = calendar_dates_df[(calendar_dates_df.date == date_string) & (calendar_dates_df.exception_type == 2)].service_id.to_numpy()
	services_for_day_2 = np.concatenate([services_for_day_1, services_added_for_day])
	services_for_day = np.setdiff1d(services_for_day_2, services_removed_for_day)

	trips_for_day = trips_df[trips_df.service_id.isin(services_for_day)]
	berlin_bus_route_ids = routes_df[(routes_df['route_type'] == 700) | (routes_df['route_type'] == 3) ].route_id.unique()
	day_trip_buses = trips_for_day[trips_for_day.route_id.isin(berlin_bus_route_ids)]

	# defining operation hours

	time_windows = [0,24]
	cutoffs = time_windows

	stop_times_df['arrival_time'] = pd.to_timedelta(stop_times_df['arrival_time'])
	stop_times_df['departure_time'] = pd.to_timedelta(stop_times_df['departure_time'])

	stop_times_df['arrival_time_in_seconds'] = stop_times_df['arrival_time'].dt.total_seconds()
	stop_times_df['departure_time_in_seconds'] = stop_times_df['departure_time'].dt.total_seconds()

	def fix_departure_time(times_to_fix):
    
	    next_day = times_to_fix >= 24*3600
	    times_to_fix[next_day] = times_to_fix[next_day] - 24 * 3600
	    
	    return times_to_fix

    
	stop_times_df['departure_time'] = fix_departure_time(stop_times_df.departure_time_in_seconds.values)
	stop_times_df['arrival_time'] = fix_departure_time(stop_times_df.arrival_time_in_seconds.values)

	def label_creation(cutoffs):
    
	    labels = []
	    if max(cutoffs) <= 24:
	        for w in cutoffs:
	            if float(w).is_integer():
	                label = str(w) + ':00'
	            else:
	                n = math.modf(w)
	                label = str(int(n[1])) + ':' + str(int(n[0]*60))
	            labels.append(label)
	    else:
	        labels = []
	        for w in cutoffs:
	            if float(w).is_integer():
	                if w > 24:
	                    w1 = w-24
	                    label = str(w1) + ':00'
	                else:
	                    label = str(w) + ':00'
	                labels.append(label)
	            else:
	                if w > 24:
	                    w1 = w-24
	                    n = math.modf(w1)
	                    label = str(int(n[1])) + ':' + str(int(n[0]*60))
	                else:
	                    n = math.modf(w)
	                    label = str(int(n[1])) + ':' + str(int(n[0]*60))
	                labels.append(label)
	    labels = [labels[i] + '-' + labels[i+1] for i in range(0, len(labels)-1)]

	    return labels

	labels = label_creation(cutoffs)
	departure_time = stop_times_df.departure_time / 3600
	stop_times_df['window'] = pd.cut(departure_time, bins=cutoffs, right=False, labels=labels)

	stop_times_df = stop_times_df.loc[~stop_times_df.window.isnull()]
	stop_times_df['window'] = stop_times_df.window.astype(str)

	#getting bus numbers for each stop and calculating frrequency:

	day_trip_buses1 = pd.merge(day_trip_buses, stop_times_df[['trip_id','stop_id','arrival_time','departure_time','window']], on='trip_id')
	day_trip_buses2 = pd.merge(day_trip_buses1, routes_df[['route_id','route_short_name']], on='route_id')
	trip_agg1 = day_trip_buses2.groupby(['stop_id','window','route_short_name'])['trip_id'].nunique().reset_index()

	def join_bus_numbers(group):
		return ", ".join(sorted(set(group)))

	trip_agg1['BusNum'] = trip_agg1.groupby('stop_id')['route_short_name'].transform(join_bus_numbers)
	bus_trips = trip_agg1.groupby(['stop_id','window','BusNum'])['trip_id'].sum().reset_index()
	stops_gdf = gpd.GeoDataFrame(stops_df, geometry = gpd.points_from_xy(stops_df.stop_lon, stops_df.stop_lat)).set_crs(epsg=4326)
	bus_trips.rename(columns={'trip_id': 'ntrips'}, inplace=True)

	start_time = bus_trips.window.apply(lambda x: cutoffs[labels.index(x)])
	end_time = bus_trips.window.apply(lambda x: cutoffs[labels.index(x) + 1])

	bus_trips['headway'] = ((end_time - start_time)*60 / bus_trips.ntrips)\
	.astype(int)

	bus_trips['frequency'] = (bus_trips.ntrips / (end_time - start_time))\
	.astype(float)

	bus_stop_frequency = pd.merge(bus_trips, stops_gdf[['stop_id','stop_name','geometry']], on='stop_id')

	#getting output shapefile for trip frequency:

	bus_stop_frequency_gdf = gpd.GeoDataFrame(pd.DataFrame(bus_stop_frequency), geometry='geometry')

	bus_stop_frequency_gdf.to_file( output_shapefile_path, driver='ESRI Shapefile')