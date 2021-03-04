import csv

def translate_country_to_ISO3(country):
    """ Translates wrong emitter countries to ISO3 Standard """
    translated = ""

    # translate names
    if (country == "States"):
        translated = "USA"
    elif (country == "Kingdom"):
        translated = "GBR"
    elif (country == "Deutschland"):
        translated = "DEU"
    elif (country == "Belgien"):
        translated = "BEL"
    elif (country == "Schweiz/Suisse/Svizzera/Svizra"):
        translated = "CHE"
    elif (country == "Österreich"):
        translated = "AUT"
    elif (country == "România"):
        translated = "ROU"
    elif (country == "Ireland"):
        translated = "IRL"
    elif (country == "Portugal"):
        translated = "PRT"
    elif (country == "France"):
        translated = "FRA"
    elif (country == "Finland"):
        translated = "FIN"
    elif (country == "Canada"):
        translated = "CAN"
    elif (country == "Nederland"):
        translated = "ANT"
    elif (country == "Sverige"):
        translated = "SWE"
    else:
        translated = country

    return translated


country_list = {'DEU': 0,'USA': 0,'GBR': 0,'BEL': 0,'CHE': 0,'AUT': 0,'ROU': 0,'IRL': 0,'PRT': 0,'FRA': 0,'FIN': 0,'CAN': 0,'ANT': 0,'SWE': 0}
def count_countries(country):
    """ Counts amount of customers per country via customers_geo.csv """
    country_list[country] += 1


def save_csv():
    """ Writes country list dictionairy into top_countries.csv """

    # sort dict
    top_countries = {k: v for k, v in sorted(country_list.items(), key=lambda item: item[1])}

    # write to csv
    with open('top_countries.csv', 'w') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in top_countries.items():
            writer.writerow([key, value])
