# GTFS Data
The GTFS (General Transit Feed Specification) format stands as an inclusive and cooperative standard dedicated to delineating the fundamental components of a public transport network. Within the GTFS framework, files, commonly known as feeds, are encapsulated in compressed .zip format. These feeds are essentially compilations of tables, each stored in individual .txt files, offering comprehensive information on various facets of the public transport network—ranging from the locations of stops and stations to trip frequencies and itinerary paths. Just like in a relational database, tables in a feed have key columns that allow one to link information described in one table to the data described in another one.
This note serves as a user-friendly introduction to a specialized Python package tailored to expedite common GTFS spatial analyses. Purpose-built for swift and efficient handling of Geographic and Transportation data, this package streamlines the process of exporting layers directly from GTFS. What sets this tool apart is its seamless integration with Python, enabling users to conduct analyses effortlessly and visualize results in a straightforward manner.
It's essential to highlight that the primary output of the package is structured in GeoDataFrames, a deliberate choice made to cater to users' visualization requirements, especially when translating analysis outcomes onto maps.
To run the package seamlessly, it mandates Python version 3.8 or higher. Creating a dedicated environment with this specific version is easily achievable through conda. Additionally, the successful execution of the package necessitates the installation of the following modules: pandas, geopandas, matplotlib.pyplot, seaborn, numpy, contextily, ctx, pyproj, shapely.geometry, zipfile, and datetime.

*For the article, I downloaded the GTFS zipfile from Berlin VBB GTFS.

# When employing the functions within this package, the workflow unfolds as follows:
1.	Read GTFS Files:
Utilize the functions to seamlessly read GTFS files into both Pandas DataFrames and GeoPandas GeoDataFrames. This initial step lays the groundwork for subsequent analyses.
2.	Calculate Stop Frequency:
Leverage the package's functionalities to compute frequency metrics per stop. The results are then organized into a GeoDataFrame, utilizing Points for spatial representation.
3.	Segment Routes:
Employ the package's capabilities to segment routes into discrete segments, each delineated from one stop to another. The results are compiled into a GeoDataFrame, utilizing LineStrings for spatial representation.
4.	Export to Spatial File:
Conclude the analysis by exporting the synthesized insights to a spatial file, particularly in ESRI Shapefile format. This step ensures that the outcomes of the GTFS spatial analyses are readily accessible and can be seamlessly integrated into broader GIS workflows.


# Loading Data into pandas data frame:
The usage of ZipFile to directly read data from a zip file into a DataFrame without the need for prior unpacking to the local disk is an efficient approach. To further enhance load performance and facilitate accurate joins between data frames, it's crucial to specify the data type for each column. Additionally, considering that shape_pt_lat and shape_pt_lon contain geographical coordinates, a prudent step is to convert them into a GeoPandas GeoDataFrame, introducing a geometry column.
Furthermore, designating the coordinate system is imperative for accurate spatial representation. In this context, utilizing ESPG 4326 is recommended, as it signifies that the coordinates are in the WGS-84 format, denoting geographical latitude and longitude.

# Finding which services run on specific date:
Considering the variability in scheduled services based on weekdays, weekends, specific weekdays, or dates, it's essential to define a specific date for constructing the network visualization. In this scenario, the chosen date is November 27, 2023.. We also needed to include services running on specific dates or remove cancelled ones from calender_dates text file.

# Calculate Public transports stop frequencies:
Now equipped with the data file for the specified day, we're poised to delve into analysis. The function stops_freq proves invaluable in this exploration, requiring three key arguments:
•	stop_times: A GeoDataFrame crafted in earlier steps, serving as the foundation for computing trip counts per stop. This dataset likely encompasses essential trip details such as times, stop sequences information.
•	stops: Another GeoDataFrame forged in preceding steps, pinpointing the precise geographic locations of the stops. This information is vital for spatially situating the stops within the analysis.
•	cutoffs: time windows we want to aggregate the data by.

# Running the Package:
1.	Activate your virtual environment (if applicable):
2.	Navigate to the directory containing the package:
3.	Run the Python 
4.	Run the Package and call function as follows.
- from pt_stops  import pt_stop_frequency
- pt_stop_frequency(gtfs_file_path, service_date, output_shapefile_path)
  
*Just for buses:
- from stop_frequency import get_bus_stop_frequency
- get_bus_stop_frequency(gtfs_file_path, service_date, output_shapefile_path)
  
# The resulting output from the pt_stop_frequency function manifests as a comprehensive GeoDataFrame, encompassing several critical columns:
1.	stop_id (from GTFS): Identifies the unique identifier for each stop within the GTFS data, aiding in precise location referencing.
2.	window: Represents the service window defined by the "cutoffs" input, signifying a 24-hour duration (one day). 
3.	BusNum: Designates the Bus Numbers associated with each stop within the given service window. This information provides insights into the specific buses serving each stop during the defined time intervals.
4.	ntrips: Quantifies the number of trips recorded within the designated service window. This metric serves as a fundamental indicator of transit activity at each stop during the specified time intervals.
5.	frequency: Expresses the transit frequency in terms of vehicles per hour (veh/hr). This measure elucidates the rate at which vehicles, in this case buses, traverse the stop within the given time intervals.
6.	Headway: Captures the duration between vehicles in the transit system, measured in minutes (min/veh). This temporal metric provides valuable insights into the temporal spacing of buses serving each stop.
7.	stop_name (from GTFS): Retrieves the stop names from the GTFS data, offering descriptive information about each stop.
8.	geometry: Incorporates the spatial component, providing the geometric representation of each stop within the GeoDataFrame.

# Get stop to stop bus line layer:
Each route has shape_id assigned. Data frame shapes_df contains coordinates of each point along this route. Sometimes, looking at the variables at the stop or line-level is not the best solution, and we need to go at the segment level. We want to know what is going on between stop A and stop B and how it is different from what is going on between stop C and stop D. In order to convert sequence of points into set of straight lines we need to convert it into numpy array of points and roll it (shift it) by one position, so point with sequence ID 1 becomes staring point and point with sequence ID 2 end point. Segment with end point sequence equal 1 should be removed, since it’s stating point contains point from another route.
 
# Running the Package:
1.	Activate your virtual environment (if applicable):
2.	Navigate to the directory containing the package:
3.	Run the Python 
4.	Run the Package and call function as follows.
- from line_frequency  import get_bus_line_frequency
- get_bus_line_frequency ( gtfs_file_path, service_date, output_shapefile_path)
  
# Attributes for each segment include:
•	BusNum: BusNumbers, representing the bus service associated with the segment.
•	Dir: Direction of the segment, aligned with GTFS data.
•	Seq: Stop_sequence of the initial stop for the segment based on GTFS data.
•	start_nm: Start_stop_name derived from GTFS records.
•	end_nm: End_stop_name derived from GTFS records.
•	start_id: Start_stop_id sourced from GTFS data.
•	end_id: End_stop_id sourced from GTFS data.
•	seg_id: Segment_id, formed by concatenating start_stop_id and end_stop_id.
•	geometry: LineString representing the geometric shape of the segment.
This description provides a clearer and more concise explanation of each attribute, making it easier for readers to understand the purpose and source of each data field.



