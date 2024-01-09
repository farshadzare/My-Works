def get_bus_line_frequency(
    gtfs_file_path,
    service_date,
     output_shapefile_path):

    # importing modules

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

    # Loading_gtfs_file

    with ZipFile(gtfs_file_path) as myzip:
        stops_df = pd.read_csv(myzip.open("stops.txt"), dtype={
        'stop_id': 'str',
        'stop_code': 'str',
        'stop_name': 'str',
        'stop_desc': 'str',
        'stop_lat': 'float',
        'stop_lon': 'float',
        'location_type': 'Int64',
        'parent_station': 'str',
        'wheelchair_boarding': 'str',
        'platform_code': 'str',
        'zone_id': 'str',
        'level_id': 'str'
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

    # getting services available in the date and filtering bus data
    show_date_str = service_date

    date = datetime.datetime.strptime(show_date_str, "%Y-%m-%d")
    date_string = date.strftime("%Y%m%d")
    day_of_week_name = date.strftime('%A').lower()

    services_for_day_1 = calendar_df[(calendar_df[day_of_week_name]) & (
        date_string >= calendar_df.start_date) & (date_string <= calendar_df.end_date)].service_id.to_numpy()

    services_added_for_day = calendar_dates_df[(calendar_dates_df.date == date_string) & (
        calendar_dates_df.exception_type == 1)].service_id.to_numpy()
    services_removed_for_day = calendar_dates_df[(calendar_dates_df.date == date_string) & (
        calendar_dates_df.exception_type == 2)].service_id.to_numpy()
    services_for_day_2 = np.concatenate(
        [services_for_day_1, services_added_for_day])
    services_for_day = np.setdiff1d(services_for_day_2, services_removed_for_day)

    trips_for_day = trips_df[trips_df.service_id.isin(services_for_day)]
    berlin_bus_route_ids = routes_df[(routes_df['route_type'] == 700) | (
        routes_df['route_type'] == 3)].route_id.unique()
    day_trip_buses = trips_for_day[trips_for_day.route_id.isin(
        berlin_bus_route_ids)]

    # creating GeoDataFrames for stops and shapes
    stops_gdf = gpd.GeoDataFrame(
    stops_df,
    geometry=gpd.points_from_xy(
        stops_df.stop_lon,
        stops_df.stop_lat)).set_crs(
            epsg=4326)
    shapes = shapes_df[["shape_id", "shape_pt_lat", "shape_pt_lon"]].groupby(
        "shape_id").agg(list).apply(lambda x: LineString(zip(x.iloc[1], x.iloc[0])), axis=1)
    shapes = gpd.GeoDataFrame(data=shapes.index, geometry=shapes.values, crs=4326)
    shapes['shape_id'] = shapes.shape_id.astype(str)
    shapes = shapes.rename(columns={'geometry': 'geometry_shapes'})
    stops_gdf = stops_gdf.rename(columns={'geometry': 'geometry_stops'})

    # merging data to get all info for shape_stop
    stop_data_shape = pd.merge(day_trip_buses, stop_times_df[[
                               'trip_id', 'stop_id', 'stop_sequence']], on='trip_id')
    stop_data_shape1 = pd.merge(stop_data_shape, stops_gdf[[
                                'stop_id', 'stop_name', 'geometry_stops']], on='stop_id')
    stop_data_shape2 = pd.merge(
        stop_data_shape1, routes_df[['route_id', 'route_short_name']], on='route_id')

    req_columns = ["shape_id", "stop_sequence", "stop_id", "geometry_stops"]
    add_columns = ["route_id", "route_short_name", "direction_id", "stop_name"]

    df_shape_stop = stop_data_shape2[req_columns + add_columns].drop_duplicates()

    # getting finall shapes of stops
    df_shape_stop = pd.merge(
        df_shape_stop, shapes[['shape_id', 'geometry_shapes']], on='shape_id')

    # getting_distance
    df_shape_stop["cut_distance_stop_point"] = df_shape_stop[["geometry_stops", "geometry_shapes"]].apply(
        lambda x: x.iloc[1].project(x.iloc[0], normalized=True), axis=1)
    df_shape_stop["projected_stop_point"] = df_shape_stop[["geometry_shapes", "cut_distance_stop_point"]].apply(
        lambda x: x.iloc[0].interpolate(x.iloc[1], normalized=True), axis=1)

    # calculate distances
    from shapely.geometry import LineString, MultiPoint

    df_shape = shapes[shapes.shape_id.isin(stop_data_shape2.shape_id.unique())]
    df_shape["list_of_points"] = df_shape.geometry_shapes.apply(
        lambda x: list(MultiPoint(x.coords).geoms))
    df_shape_exp = df_shape.explode("list_of_points")
    df_shape_exp["projected_line_points"] = df_shape_exp[["geometry_shapes", "list_of_points"]].apply(
        lambda x: x.iloc[0].project(x.iloc[1], normalized=True), axis=1)

    # renaming dataframes and concatenating
    df_shape_stop.rename({"projected_stop_point": "geometry",
    "cut_distance_stop_point": "normalized_distance_along_shape"},
    axis=1,
     inplace=True)
    df_shape_stop["cut_flag"] = True

    df_shape_exp = df_shape_exp[["shape_id",
        "list_of_points", "projected_line_points"]]
    df_shape_exp.rename({"list_of_points": "geometry",
    "projected_line_points": "normalized_distance_along_shape"},
    axis=1,
     inplace=True)
    df_shape_exp["cut_flag"] = False

    # combine stops and shape points
    gdf = pd.concat([df_shape_stop, df_shape_exp], ignore_index=False)
    gdf.sort_values(["shape_id", "normalized_distance_along_shape"], inplace=True)
    gdf.reset_index(inplace=True, drop=True)

    # drop all non stops
    cuts = gdf.where(gdf.cut_flag).dropna(subset="cut_flag")
    cuts = cuts.astype(
        {"shape_id": str, "stop_sequence": int, "direction_id": int})
    cuts[["end_stop_id", "end_stop_name"]] = cuts.groupby(
        "shape_id")[['stop_id', "stop_name"]].shift(-1)

    # create segments for buses
    segment_geometries = []
    for shape_id in cuts.shape_id.drop_duplicates():
        cut_idx = cuts[cuts.shape_id == shape_id].index
        for i, cut in enumerate(cut_idx[:-1]):
            segment_geometries.append(LineString(
                gdf.iloc[cut_idx[i]:cut_idx[i + 1] + 1].geometry))

    # creating bus_segments_gdf
    segment_df = cuts.dropna(subset="end_stop_id", axis=0)
    segment_gdf = gpd.GeoDataFrame(segment_df, geometry=segment_geometries)
    segment_gdf.drop(["geometry_shapes",
    "cut_flag",
    "normalized_distance_along_shape",
    "geometry_stops"],
    axis=1,
     inplace=True)
    segment_gdf.crs = "EPSG:4326"

    segment_gdf['segment_id'] = segment_gdf.stop_id.astype(
        str) + ' - ' + segment_gdf.end_stop_id.astype(str)
    segment_gdf['segment_name'] = segment_gdf.stop_name + \
        ' - ' + segment_gdf.end_stop_name

    segment_gdf.rename(
    columns=dict(
        stop_name='start_stop_name',
        stop_id='start_stop_id'),
         inplace=True)

    # making operation time

    index_ = ['route_id', 'route_short_name', 'stop_id']
    col = 'window'
    index_list = index_ + ['direction_id', col]

    time_windows = [0, 24]
    cutoffs = time_windows

    stop_times_df['arrival_time'] = pd.to_timedelta(stop_times_df['arrival_time'])
    stop_times_df['departure_time'] = pd.to_timedelta(
        stop_times_df['departure_time'])

    stop_times_df['arrival_time_in_seconds'] = stop_times_df['arrival_time'].dt.total_seconds()
    stop_times_df['departure_time_in_seconds'] = stop_times_df['departure_time'].dt.total_seconds()

    def fix_departure_time(times_to_fix):

        next_day = times_to_fix >= 24 * 3600
        times_to_fix[next_day] = times_to_fix[next_day] - 24 * 3600

        return times_to_fix

    if max(cutoffs) <= 24:
        stop_times_df['departure_time'] = fix_departure_time(
            stop_times_df.departure_time_in_seconds.values)
        stop_times_df['arrival_time'] = fix_departure_time(
            stop_times_df.arrival_time_in_seconds.values)

    def label_creation(cutoffs):

        labels = []
        if max(cutoffs) <= 24:
            for w in cutoffs:
                if float(w).is_integer():
                    label = str(w) + ':00'
                else:
                    n = math.modf(w)
                    label = str(int(n[1])) + ':' + str(int(n[0] * 60))
                labels.append(label)
        else:
            labels = []
            for w in cutoffs:
                if float(w).is_integer():
                    if w > 24:
                        w1 = w - 24
                        label = str(w1) + ':00'
                    else:
                        label = str(w) + ':00'
                    labels.append(label)
                else:
                    if w > 24:
                        w1 = w - 24
                        n = math.modf(w1)
                        label = str(int(n[1])) + ':' + str(int(n[0] * 60))
                    else:
                        n = math.modf(w)
                        label = str(int(n[1])) + ':' + str(int(n[0] * 60))
                    labels.append(label)

        labels = [labels[i] + '-' + labels[i + 1]
            for i in range(0, len(labels) - 1)]

        return labels

    labels = label_creation(cutoffs)

    departure_time = stop_times_df.departure_time / 3600
    stop_times_df['window'] = pd.cut(
    departure_time,
    bins=cutoffs,
    right=False,
     labels=labels)

    stop_times_df = stop_times_df.loc[~stop_times_df.window.isnull()]
    stop_times_df['window'] = stop_times_df.window.astype(str)

    # calculating line frequency
    day_trip_buses1 = pd.merge(day_trip_buses,
    stop_times_df[['trip_id',
    'stop_id',
    'arrival_time',
    'departure_time',
    'window']],
     on='trip_id')

    day_trip_buses2 = pd.merge(
        day_trip_buses1, routes_df[['route_id', 'route_short_name']], on='route_id')

    trips_agg = day_trip_buses2.pivot_table(
    'trip_id', index=index_list, aggfunc='count').reset_index()

    trips_agg.rename(columns={'trip_id': 'ntrips'}, inplace=True)

    start_time = trips_agg.window.apply(lambda x: cutoffs[labels.index(x)])

    end_time = trips_agg.window.apply(lambda x: cutoffs[labels.index(x) + 1])

    trips_agg['frequency'] = (trips_agg.ntrips / (end_time - start_time))\
    .astype(float)

    line_frequencies = trips_agg

    keep_these = [
    'route_id',
    'route_short_name',
    'segment_name',
    'start_stop_name',
    'end_stop_name',
    'segment_id',
    'start_stop_id',
    'end_stop_id',
    'direction_id',
     'geometry']

    line_frequencies = pd.merge(
    line_frequencies,
    segment_gdf[keep_these],
    left_on=[
        'route_id',
        'route_short_name',
        'stop_id',
        'direction_id'],
        right_on=[
            'route_id',
            'route_short_name',
            'start_stop_id',
            'direction_id'],
             how='left')

    line_frequencies.drop('stop_id', axis=1, inplace=True)

    # Remove duplicates after merging

    line_frequencies.drop_duplicates(inplace=True)

    # add all lines together

    def add_all_lines(line_frequencies, segments_gdf, labels, cutoffs):

        logging.info('adding data for all lines.')

        # Calculate sum of trips per segment with all lines
        all_lines = line_frequencies.pivot_table(
            ['ntrips'],
            index=['segment_id', 'window'],
            aggfunc='sum').reset_index()

        sort_these = ['direction_id', 'window', 'stop_sequence']

        data_all_lines = pd.merge(
            all_lines,
            segments_gdf.drop_duplicates(subset=['segment_id']),
            left_on=['segment_id'], right_on=['segment_id'],
            how='left').reset_index().sort_values(by=sort_these, ascending=True)

        data_all_lines.drop(['index'], axis=1, inplace=True)
        data_all_lines['route_id'] = 'ALL_LINES'
        data_all_lines['route_name'] = 'All lines'
        data_all_lines['direction_id'] = 'NA'

        # Add frequency for all lines
        start_time = data_all_lines.window.apply(
            lambda x: cutoffs[labels.index(x)])
        end_time = data_all_lines.window.apply(
            lambda x: cutoffs[labels.index(x) + 1])

        data_all_lines['min_per_trip'] = ((end_time - start_time) * 60 / data_all_lines.ntrips)\
            .astype(int)

        # Append data for all lines to the input df

        data_complete = pd.concat([line_frequencies, data_all_lines]).reset_index(drop=True)

        return data_complete

    all_lines = line_frequencies.pivot_table(['ntrips'], index=['segment_id', 'window'], aggfunc='sum').reset_index()
    sort_these = ['direction_id', 'window', 'stop_sequence']

    data_all_lines = pd.merge( all_lines, segment_gdf.drop_duplicates(subset=['segment_id']),
        left_on=['segment_id'], right_on=['segment_id'],
        how='left').reset_index().sort_values(by=sort_these, ascending=True)
    data_all_lines.drop(['index'], axis=1, inplace=True)
    data_all_lines['route_id'] = 'ALL_LINES'
    data_all_lines['route_short_name'] = 'All lines'
    data_all_lines['direction_id'] = 'NA'

    # Add frequency for all lines
    start_time = data_all_lines.window.apply(lambda x: cutoffs[labels.index(x)])
    end_time = data_all_lines.window.apply(lambda x: cutoffs[labels.index(x) + 1])

    data_all_lines['frequency'] = ( data_all_lines.ntrips / (end_time - start_time) )\
    .astype(float)

    # Append data for all lines to the input df
    data_complete = pd.concat([line_frequencies, data_all_lines]).reset_index(drop=True)

    #making GeoDataFrame and save the shapefile
    data_complete_gdf = gpd.GeoDataFrame( data=data_complete.drop('geometry', axis=1), geometry=data_complete.geometry)
    keep_these = [
            'route_id', 'route_short_name',
            'direction_id',
            'segment_name', 'start_stop_name', 'end_stop_name',
            'window', 'frequency', 'ntrips', 
            'start_stop_id', 'end_stop_id', 'segment_id',
            'geometry'
        ]
    data_complete_gdf = data_complete_gfd.loc[~data_complete_gfd.geometry.isnull()][keep_these]
    data_complete_gdf.to_file(output_shapefile_path, driver="ESRI Shapefile")













