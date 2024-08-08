
from bs4 import BeautifulSoup
import requests

print("start")

#Where do new city council agendas get uploaded? + In what format?
url_anaheim = "https://www.anaheim.net/2527/Agendas" #list of city council agenda links, + viewer
url_santa_ana = "https://www.santa-ana.org/agendas-and-minutes/" #list of ALL meetings, with links to agenda
url_garden_grove = "https://agendasuite.org/iip/gardengrove/agendaitem/list" #Not a list of agendas, but a list of agenda items
url_city_of_orange = "https://www.cityoforange.org/our-city/local-government/city-council/city-council-meetings/-selcat-32#eventcats_46_0_36" #List of city council meetings, agenda in each one
url_huntington_beach = "https://huntingtonbeach.legistar.com/Calendar.aspx" #List of all meetings with agenda links


def get_last_agenda_an():
    page_anaheim = requests.get(url_anaheim)
    soup_an = BeautifulSoup(page_anaheim.content, "lxml")
    agenda = soup_an.find('a', class_='Hyperlink', title='Print Current Agenda')
    print(agenda['href'])

#TODO website has two sections: "Current and Upcoming meetings" and "archived. I don't know how to navigate archive to most recent
def get_last_agenda_sa():
    page_santa_ana = requests.get(url_santa_ana)
    soup_sa= BeautifulSoup(page_santa_ana.content, "lxml")

#TODO
def get_last_agenda_gg():
    page_garden_grove = requests.get(url_garden_grove)
    soup_gg = BeautifulSoup(page_garden_grove.content, "lxml")

#TODO
def get_last_agenda_co():
    page_city_of_orange = requests.get(url_city_of_orange)
    soup_co = BeautifulSoup(page_city_of_orange.content, "lxml")

#TODO
def get_last_agenda_hb():
    page_huntington_beach = requests.get(url_huntington_beach)
    soup_hb = BeautifulSoup(page_huntington_beach.content, "lxml")

get_last_agenda_an()

