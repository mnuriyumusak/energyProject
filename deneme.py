import utm
import csv
import EnAPIAdapter
import time
import os

_OUTPUT_DIR = "output"


def convert_utm_to_lat_long():
    """
    add new 2 column which are lat and long, create a new csv file
    """
    f = open('res_list.csv', 'a+')
    csv_data = csv.reader(f, delimiter=';')
    new_csv_data = ""
    for item in csv_data:
        lat_lng = utm.to_latlon(float(item[2]), float(item[3]), 35, 'U')
        item.append(lat_lng[0])
        item.append(lat_lng[1])
        for idx, i in enumerate(item):
            new_csv_data += str(i)
            if idx != len(item)-1:
                new_csv_data += ";"
        new_csv_data += "\n"
    f.close()
    target = open("res_list_with_lat_long.csv", 'a+')
    target.write(new_csv_data)
    target.close()


def write_forecast_to_csv():
    """
    Write both daily and hourly forecast data of turbins to csv file, wtih their properties such as name,lat,long
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
            line_h = EnAPIAdapter.get_hourly_forecast(i, "CSV")
            target_h.write(line_h)
            line_d = EnAPIAdapter.get_ten_day_forecast(i, "CSV")
            target_d.write(line_d)
        target_h.close()
        target_d.close()
        return True
    except:
        return False


def main():
    t0 = time.clock()
    result = write_forecast_to_csv()
    if not result:
        print "A problem occured ! Mission failed !"
    print str(time.clock()-t0)

if __name__ == '__main__':
    main()
