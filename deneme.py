# -*- coding: utf-8 -*-
import utm
import csv
import EnAPIAdapter
import time
import os
import schedule
import logging
import urllib2
import json

_OUTPUT_DIR = "output"


logger = logging.getLogger('yenitay')
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
hdlr = logging.FileHandler(os.getcwd() + '/logs.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)

def get_elevation(lat, lng, sensor=False):
        """
        Args:
            @param lat: latitude (float)
            @param lng: longitude (float)
            @param sensor: sensor (boolean)

        Returns the elevation of a specific location on earth using the Google
        Maps API.

        lat : The latitude of the location in degrees. Latitudes can
        take any value between -90 and 90.
        lng : The longitude of the location in degrees. Longitudes
        can take any value between -180 and 180.
        sensor : This parameter is required by the Google maps API
        and indicates whether the application that requests the elevation data is
        using a sensor (such as a GPS device). Default value is 'False'.

        @return: A tuple (elevation, lat, lng, status):
          * elevation (float): The requested elevation in meters. If the location is
            on the sea floor the returned elevation has a negative value.
          * lat, lng (float): The latitude and longitude of the location (for testing
            purposes: must be equal to the input values).
          * status (str): Error code:
            "OK": the API request was successful.
            "INVALID_REQUEST": the API request was malformed.
            "OVER_QUERY_LIMIT": the requester has exceeded quota.
            "REQUEST_DENIED": the API did not complete the request, likely because
            of an invalid 'sensor' parameter.
            "UNKNOWN_ERROR": other error
          * If the error code 'status' is not 'OK' then all other members of the
            returned tuple are set to 'None'.

        @note: More information about the Google elevation API and its usage limits
        can be found in https://developers.google.com/maps/documentation/elevation/.

        @example:
        >>> round(get_elevation(-38.407, -25.297)[0], 2) == -3843.86
        True
        >>> round(get_elevation(37.32522, -104.98470)[0], 2) == 2934.24
        True
        """
        # build the url for the API call
        elevation_base_url = 'http://maps.google.com/maps/api/elevation/json'
        url_params = "locations=%.7f,%.7f&sensor=%s" % (float(lat), float(lng), "true" if sensor else "false")
        url = elevation_base_url + "?" + url_params

        # make the call (ie. read the contents of the generated url) and decode the
        # result (note: the result is in json format).
        # with urllib.request.urlopen(url) as f:
        # response = json.loads(f.read().decode())
        req = urllib2.Request(url)
        opener = urllib2.build_opener()
        f = opener.open(req)
        response = json.loads(f.read().decode())
        status = response["status"]
        if status == "OK":
            result = response["results"][0]
            elevation = float(result["elevation"])
            # lat = float(result["location"]["lat"])
            # lng = float(result["location"]["lng"])
        else:
            raise Exception("Error _m")
            # elevation = lat = lng = None
        return int(elevation)


"""

Columns for hourly CSV file:

0 - date(%d.%m.%Y), 1 - weekday, 2- localtime, 3 - temperature(C), 4 - windspeed(km/h),
5 - winddirection from S=1 to SE=8, 6 - relativehumidity(%), 7 - pictocode, 8 - precipitation(mm),
9 - precip probability(%), 10 - Shortwave radiation(W/m2), 11 - sunshinetime, 12 - lat, 13 - lng
14 - elevation 15 - weight

"""


def convert_utm_to_lat_long():
    """
    add new 2 column which are lat and long, create a new csv file
    """
    f = open('res_list.csv', 'a+')
    csv_data = csv.reader(f, delimiter=';')
    new_csv_data = ""
    for item in csv_data:
        lat_lng = utm.to_latlon(float(float(item[2])), float(float(item[3])), 35, 'S')
        elevation = get_elevation(lat_lng[0],lat_lng[1])
        item.append(lat_lng[0])
        item.append(lat_lng[1])
        item.append(elevation)
        for idx, i in enumerate(item):
            new_csv_data += str(i)
            if idx != len(item)-1:
                new_csv_data += ";"
        new_csv_data += "\n"
    f.close()
    target = open("rest_list_with_lat_long.csv", 'a+')
    target.write(new_csv_data)
    target.close()


def write_forecast_to_csv():
    """
    Write both daily and hourly forecast data of turbins to csv file, with their properties such as name,lat,long
    """
    try:
        f = open('res_list_with_lat_long.csv', 'r+')
        csv_data = csv.reader(f, delimiter=';')

        file_name_hourly = _OUTPUT_DIR + "/en_%s_hourly.csv" % time.strftime("%Y%m%d")
        file_name_daily = _OUTPUT_DIR + "/en_%s_10_day.csv" % time.strftime("%Y%m%d")
        if not os.path.exists(os.path.dirname(file_name_hourly)):
            os.makedirs(os.path.dirname(file_name_hourly))
        target_h = open(file_name_hourly, 'a+')
        target_d = open(file_name_daily, 'a+')
        for i in csv_data:
            logger.info(str(i[0]) + "," + str(i[1]) + " aliniyor.")
            line_h = EnAPIAdapter.get_hourly_forecast(i, "CSV")
            target_h.write(line_h)
            line_d = EnAPIAdapter.get_ten_day_forecast(i, "CSV")
            target_d.write(line_d)
        target_h.close()
        target_d.close()
        return True
    except:
        return False


def run_script():
    logger.info("Transferring process has began.")
    t0 = time.clock()
    result = write_forecast_to_csv()
    if not result:
        logger.error("A problem occured ! Mission failed !")
    print
    logger.info("Process finished in " + str(time.clock()-t0) + " seconds.")


def find_center():
    centers_str = ""
    f = open('aliaga.csv', 'a+')
    csv_data = csv.reader(f, delimiter=';')
    center_E = 0
    center_N = 0
    for item in csv_data:
        center_E += float(item[2])
        center_N += float(item[3])
    center_E = center_E / 46
    center_N = center_N / 46
    lat_lng = utm.to_latlon(float(center_E), float(center_N), 35, 'S')
    elevation = get_elevation(lat_lng[0],lat_lng[1])
    centers_str += "Aliağa;C;" + str(center_E) + ";" + str(center_N) + ";" + str(lat_lng[0])+ ";" + str(lat_lng[1])\
                   +";" + str(elevation) + "\n"
    f.close()

    f = open('bandirma.csv', 'a+')
    csv_data = csv.reader(f, delimiter=';')
    center_E = 0
    center_N = 0
    for item in csv_data:
        center_E += float(item[2])
        center_N += float(item[3])
    center_E = center_E / 27
    center_N = center_N / 27
    lat_lng = utm.to_latlon(float(center_E), float(center_N), 35, 'T')
    elevation = get_elevation(lat_lng[0],lat_lng[1])
    centers_str += "Bandırma;C;" + str(center_E) + ";" + str(center_N) + ";" + str(lat_lng[0])+ ";" + str(lat_lng[1])\
                   +";" + str(elevation) + "\n"
    f.close()

    f = open('mazi.csv', 'a+')
    csv_data = csv.reader(f, delimiter=';')
    center_E = 0
    center_N = 0
    for item in csv_data:
        center_E += float(item[2])
        center_N += float(item[3])
    center_E = center_E / 21
    center_N = center_N / 21
    lat_lng = utm.to_latlon(float(center_E), float(center_N), 35, 'S')
    elevation = get_elevation(lat_lng[0],lat_lng[1])
    centers_str += "Mazi;C;" + str(center_E) + ";" + str(center_N) + ";" + str(lat_lng[0])+ ";" + str(lat_lng[1])\
                   +";" + str(elevation) + "\n"
    f.close()

    f = open('soma.csv', 'a+')
    csv_data = csv.reader(f, delimiter=';')
    center_E = 0
    center_N = 0
    for item in csv_data:
        center_E += float(item[2])
        center_N += float(item[3])
    center_E = center_E / 46
    center_N = center_N / 46
    lat_lng = utm.to_latlon(float(center_E), float(center_N), 35, 'S')
    elevation = get_elevation(lat_lng[0],lat_lng[1])
    centers_str += "Soma;C;" + str(center_E) + ";" + str(center_N) + ";" + str(lat_lng[0])+ ";" + str(lat_lng[1])\
                   +";" + str(elevation) + "\n"
    f.close()

    f = open('zeytineli.csv', 'a+')
    csv_data = csv.reader(f, delimiter=';')
    center_E = 0
    center_N = 0
    for item in csv_data:
        center_E += float(item[2])
        center_N += float(item[3])
    center_E = center_E / 20
    center_N = center_N / 20
    lat_lng = utm.to_latlon(float(center_E), float(center_N), 35, 'S')
    elevation = get_elevation(lat_lng[0],lat_lng[1])
    centers_str += "Zeytineli;C;" + str(center_E) + ";" + str(center_N) + ";" + str(lat_lng[0])+ ";" + str(lat_lng[1])\
                   +";" + str(elevation) + "\n"
    f.close()


    f = open('dinar.csv', 'a+')
    csv_data = csv.reader(f, delimiter=';')
    center_E = 0
    center_N = 0
    for item in csv_data:
        center_E += float(item[2])
        center_N += float(item[3])
    center_E = center_E / 50
    center_N = center_N / 50
    lat_lng = utm.to_latlon(float(center_E), float(center_N), 36, 'S')
    elevation = get_elevation(lat_lng[0],lat_lng[1])
    centers_str += "Dinar;C;" + str(center_E) + ";" + str(center_N) + ";" + str(lat_lng[0])+ ";" + str(lat_lng[1])\
                   +";" + str(elevation) + "\n"
    f.close()

    f = open('senkoy.csv', 'a+')
    csv_data = csv.reader(f, delimiter=';')
    center_E = 0
    center_N = 0
    for item in csv_data:
        center_E += float(item[2])
        center_N += float(item[3])
    center_E = center_E / 12
    center_N = center_N / 12
    lat_lng = utm.to_latlon(float(center_E), float(center_N), 37, 'S')
    elevation = get_elevation(lat_lng[0],lat_lng[1])
    centers_str += "Eolos-Şenköy;C;" + str(center_E) + ";" + str(center_N) + ";" + str(lat_lng[0])+ ";" + str(lat_lng[1])\
                   +";" + str(elevation) + "\n"
    f.close()

    f = open('kanije.csv', 'a+')
    csv_data = csv.reader(f, delimiter=';')
    center_E = 0
    center_N = 0
    for item in csv_data:
        center_E += float(item[2])
        center_N += float(item[3])
    center_E = center_E / 20
    center_N = center_N / 20
    lat_lng = utm.to_latlon(float(center_E), float(center_N), 35, 'S')
    elevation = get_elevation(lat_lng[0],lat_lng[1])
    centers_str += "Kanije;C;" + str(center_E) + ";" + str(center_N) + ";" + str(lat_lng[0])+ ";" + str(lat_lng[1])\
                   +";" + str(elevation) + "\n"
    f.close()


    target = open("centers.csv", 'a+')
    target.write(centers_str)
    target.close()



def main():
    convert_utm_to_lat_long()
    #find_center()
    """
    logger.info("Main is starting to run.")
    schedule.every(30).minutes.do(run_script)
    while 1:
        schedule.run_pending()
        time.sleep(1)
    """
if __name__ == '__main__':
    main()

