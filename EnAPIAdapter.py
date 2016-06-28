import json
import urllib2
import time
import yaml
global TOKEN
TOKEN = ""

BASE_URL_GOOGLE = "http://maps.google.com/maps/api/geocode/json?address="
TOKEN_BASE_URL = "https://thepulseapi.earthnetworks.com/oauth20/token?grant_type=client_credentials&client_id="
TEN_DAY_BASE_URL = "https://thepulseapi.earthnetworks.com/data/forecasts/v1/daily?location="
HOURLY_BASE_URL = "https://thepulseapi.earthnetworks.com/getHourly6DayForecast/data/forecasts/v1/hourly?location="
DEFAULT_HOURLY_PARAMS = ["forecastDateUtcStr", "cloudCoverPercent", "dewPoint", "precipCode", "precipProbability",
                         "relativeHumidity", "temperature", "thunderstormProbability", "windDirectionDegrees",
                         "windSpeed", "snowRate"]
DEFAULT_TEN_DAY_PARAMS = ["forecastDateUtcStr", "cloudCoverPercent", "dewPoint", "precipCode", "precipProbability",
                          "relativeHumidity", "temperature", "thunderstormProbability", "windDirectionDegrees",
                          "windSpeed", "snowAmountMm"]


def set_token(arg):
    global TOKEN
    TOKEN = arg


def get_json_data(final_url):
    """
    General function that takes and returns json data from given url
    """
    my_final_url = final_url + str(TOKEN)
    try:
        response = urllib2.urlopen(my_final_url)
    except urllib2.HTTPError:
        return_token()
        set_token(return_token())
        my_final_url = final_url + str(TOKEN)
        response = urllib2.urlopen(my_final_url)

    json_data = json.load(response)
    return json_data


def get_ten_day_forecast(infos, return_format, params=None):
    """
    Takes Json data from given parameters and returns it
    """
    final_url = TEN_DAY_BASE_URL + str(infos[4]) + "," + str(infos[5]) + \
        "&locationtype=latitudelongitude&units=metric&cultureinfo=en-en&verbose=true&access_token="

    json_data = get_json_data(final_url)
    if return_format == "JSON":
        return json_data
    elif return_format == "CSV":
        if params is None:
            params = DEFAULT_TEN_DAY_PARAMS
        return convert_to_csv_ten_day(infos, json_data, params)


def get_hourly_forecast(infos,return_format, params=None):
    final_url = HOURLY_BASE_URL + str(infos[4]) + "," + str(infos[5]) + \
        "&locationtype=latitudelongitude&units=metric&cultureinfo=en-en&verbose=true&access_token="

    json_data = get_json_data(final_url)

    if return_format == "JSON":
        return json_data
    elif return_format == "CSV":
        if params is None:
            params = DEFAULT_HOURLY_PARAMS
        return convert_to_csv_hourly(infos, json_data, params)


def return_token():
    """
    Because Earth Networks refreshes token after some point, this functions refreshes the token to avoid errors
    """
    yaml_file = open("secrets.yaml", 'r')
    yaml_dict = yaml.load(yaml_file)
    client_id = str(yaml_dict["client_id"])
    client_secret = str(yaml_dict["client_secret"])
    yaml_file.close()
    final_url = TOKEN_BASE_URL + client_id + "&client_secret=" + client_secret
    try:
        response = urllib2.urlopen(final_url)
    except:
        final_url = TOKEN_BASE_URL + client_id + "&client_secret=" + client_secret
        response = urllib2.urlopen(final_url)
    json_data = json.load(response)
    token = json_data["OAuth20"]["access_token"]["token"]
    refresh_token = json_data["OAuth20"]["access_token"]["refresh_token"]
    if token != refresh_token:
        return return_token()
    return  refresh_token


def convert_to_csv_ten_day(infos, json_data, params):
    """
    Creates a csv data from given parameters
    """
    json_data = json_data["dailyForecastPeriods"]
    csv_string = ""

    for count in range(len(params)):
        if count == 0:
            csv_string += "en_" + str(json_data[0][params[count]]) + ";"
        else:
            csv_string += str(json_data[0][params[count]])[0:len(str(json_data[0][params[count]]))-1] + ";"
    csv_string += "%s;%s;%s;%s;%s;%s" % (infos[0], infos[1], infos[2], infos[3], infos[4], infos[5])
    csv_string += "\n"
    return csv_string


def convert_to_csv_hourly(infos, json_data, params):
    json_data = json_data["hourlyForecastPeriod"]
    csv_string = ""

    for row in json_data:
        enter = False
        for p in range(len(params)):
            if p == 0:
                if int(str(row[params[p]][8:10])) <= int(time.strftime("%d")):
                    enter = True
                    csv_string += str(row[params[p]])[0:len(str(json_data[0][params[p]]))-1] + ";"
                else:
                    break
            elif enter:
                csv_string += str(row[params[p]]) + ";"
        if enter:
            csv_string += "%s;%s;%s;%s;%s;%s" % (infos[0], infos[1], infos[2], infos[3], infos[4], infos[5])
            csv_string += "\n"

    return csv_string
