import requests
import json
import csv
import pandas
from datetime import date
import ast

import geopy                # helper for lat/lon to country
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

import country_helper       # helper functions for country csv


""" CHANGE TO RUN ON SERVER """
#DATA_PATH = "/home/ubuntu/Analytics/Data/"
DATA_PATH = ""
""" ----------------------- """

""" Executes every 24 hours and updates .csv files

    Data will be:
    Atomic:                 If date has already been crawled, it wont add it again (no multiple entries)
    Error-Correcting:       Converts wrong formats like country names to ISO3 codes

    
    OUTPUT:
    customers_info.csv      amount of controllers, routers, senders, pestcams per customer sorted by id and name
    customers_geo.csv       geo location of customer (country, lat, lon) sorted by id
    total_customers.csv:    amount of total customer sorted by date 
    total_devices.csv:      amount of total controllers, routers, senders, pestcams sorted by date 
    top_countries.csv:      amount of customer per country sorted by top countries 
    alarms.csv:             amount of total alarms sorted by date

"""


def main():
    """ Parses API Calls from M2M Emitter System to a csv file with data """

    # get api key for access
    api_key = get_api_key()

    # total customers csv (date, amount)
    customer_list_json = get_customer_overview(api_key)

    # customer detail info (id, name, amount of controllers etc.)
    update_general_customer_info(customer_list_json)
    update_customer_amount_csv(customer_list_json)

    # customer location
    update_customer_location(customer_list_json)

    # create alarms over time
    update_alarms(customer_list_json)

def update_alarms(response):
    """ Creates csv with amount of alarms per day """

    # date for entries
    today = date.today()

    data_list = response.json()['data']

    alarm_counter = 0
    for index in range(len(data_list)):
        try:

            # get data
            last_alarm = data_list[index]['lastAlarm']

            # found new alarm today!!!
            if (str(today) == last_alarm[0:10]):
                alarm_counter += 1

        except Exception as e:
            print(e)

    # write alarms counted and date into csv
    fields = ['year', 'month', 'day', 'alarms']

    # data rows of csv file
    today = date.today()
    daterow_to_add = str(today.year) + "," + str(today.month) + "," + str(today.day) + "," + str(alarm_counter) + "\n"

    # check if date is already there
    last_line = ""
    with open(DATA_PATH + 'alarms.csv', 'r') as f:  # read last line
        last_line = f.readlines()[-1]
    if not (last_line == daterow_to_add):  # date is new:
        with open(DATA_PATH + 'alarms.csv', 'a') as fd:
            fd.write(daterow_to_add)  # add row to file




def update_general_customer_info(response):
    """ Generates costumer CSV with header:
    ID, amount of controllers, amount of routers, amount of senders, amount of pestcams and last alarm
    TODO: FIX ALARM """

    # read total response
    data = response.json()

    # vars for total devices
    total_controllers, total_routers, total_senders, total_pestcams = 0,0,0,0

    # header line
    fields = ['id','name', 'amount_controllers', 'amount_routers', 'amount_senders', 'amount_pestcams']

    # collect csv rows from json
    dataList = data['data']
    data_list_results = []
    for index in range(len(dataList)):
        try:

            # get data
            id = dataList[index]['id']
            name = dataList[index]['name']
            if (name == ""):
                name = name = dataList[index]['exterminatorName']
            amount_controllers = dataList[index]['countControllers']
            amount_routers = dataList[index]['countRouters']
            amount_sender = dataList[index]['countSenders']
            amount_pestcam = dataList[index]['countPestcams']

            # add to total
            total_controllers += amount_controllers
            total_routers += amount_routers
            total_senders += amount_sender
            total_pestcams += amount_pestcam

            # sort data in list as list
            new_data_row = [id, name, amount_controllers, amount_routers, amount_sender, amount_pestcam]
            data_list_results.append(new_data_row)

        except:
            pass

    # UPDATE CUSTOMER INFO CSV
    with open(DATA_PATH + "customers_info.csv", "w") as csv_file:
        writer = csv.writer(csv_file)  # , delimiter=',')
        writer.writerow(fields)
        writer.writerows(data_list_results)

    # APPEND TOTAL DEVICES INFO CSV
    today = date.today()
    new_data_row = [str(today.year),str(today.month), str(today.day), total_controllers, total_routers, total_senders, total_pestcams]

    # check if date is already there
    last_line = ""
    with open(DATA_PATH + 'total_devices.csv', 'r') as f:               # read last line
        last_line = f.readlines()[-1]

    last_line_list = last_line.split(',')                               # convert string to list
    if not (last_line_list[0:3] == new_data_row[0:3]):                  # date is new
        with open(DATA_PATH + "total_devices.csv", "a") as csv_file:    # append new row
            writer = csv.writer(csv_file)
            writer.writerow(new_data_row)




def update_customer_location(response):
    """ Generates csv file with header (id,lat,lon) """

    # create data object out of json
    data = response.json()

    # header line
    fields = ['id', 'country', 'lat', 'lon']

    # collect csv rows from json
    dataList = data['data']
    data_list_results = []
    lat, lon = "0", "0"
    for index in range(len(dataList)):
        try:
            id = dataList[index]['id']

            try:
                lat = dataList[index]['lat']
                lon = dataList[index]['lon']
            except:
                print("Customer has no lat/lon entry: " + str(id))
                # TODO: ExterminatorIDs als kunden betrachten

            # get country out of lat/lon
            locator = Nominatim(user_agent="myGeocoder")
            coordinates = lat, lon
            location = locator.reverse(coordinates)
            words = location.address.split()
            country = words[-1]

            # translate names
            country = country_helper.translate_country_to_ISO3(country)

            # add customer count to country
            country_helper.count_countries(country)

            new_data_row = [id, country, lat, lon]
            data_list_results.append(new_data_row)

        except Exception as e:
            print("Error while getting country: " + str(e))

    # write data in csv
    with open(DATA_PATH + "customers_geo.csv", "w") as csv_file:
        writer = csv.writer(csv_file)  # , delimiter=',')
        writer.writerow(fields)
        writer.writerows(data_list_results)

    # write country count into top_countries.csv
    country_helper.save_csv()

def update_customer_amount_csv(response):
    """ Generates csv file with header (year,month,day,amount) """

    # date for entries
    today = date.today()

    # read total customers
    text = response.json()
    amount_customers_today = text['total']

    # field names
    fields = ['year', 'month', 'day', 'amount']

    # data rows of csv file
    today = date.today()
    daterow_to_add = str(today.year) + "," + str(today.month) + "," + str(today.day) + "," + str(amount_customers_today) + "\n"
    new_data_row = [str(today.year), str(today.month), str(today.day), str(amount_customers_today)]

    # check if date is already there
    last_line = ""
    with open(DATA_PATH + 'total_customers.csv', 'r') as f:               # read last line
        last_line = f.readlines()[-1]

    last_line_list = last_line.split(',')                               # convert string to list
    if not (last_line_list[0:3] == new_data_row[0:3]):                  # date is new
        with open(DATA_PATH + "total_customers.csv", "a") as csv_file:    # append new row
            writer = csv.writer(csv_file)
            writer.writerow(new_data_row)


def get_customer_overview(api_key):
    """ Retrieves the total list of customers
    Return: json file """

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        'X-Auth-Token': str(api_key)
    }
    url = "https://emitterapi.m2mgate.de/emitter-server/rest/customer/overview"

    print("Request customer list ...")
    r = requests.get(url, headers=headers)
    if (str(r) == str("<Response [200]>")):
        print("Successfully got customer list!")
    return r

def get_api_key():
    """ Returns the api key as a string """

    login = {
        "email": "tim@futura-germany.com",
        "password": "fisbu9-ziwqic-qavsoD",
    }
    headers = {
        "Accept": "text/plain",
        "Content-Type": "application/json",
    }
    url = "https://emitterapi.m2mgate.de/emitter-server/rest/webapp/login"
    print("Requesting API Key ...")
    r = requests.post(url, headers=headers, json=login)
    if (str(r) == str("<Response [200]>")):
        print("Successfully got API Key!")
    api_key = r.text

    return api_key

main()