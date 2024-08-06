
from bs4 import BeautifulSoup
import requests

print("start")

#Where do new city council agendas get uploaded? + In what format?
url_anaheim = "https://www.anaheim.net/2527/Agendas" #list of city council agenda links, + viewer
url_santa_ana = "https://www.santa-ana.org/agendas-and-minutes/" #list of ALL meetings, with links to agenda
url_garden_grove = "https://agendasuite.org/iip/gardengrove/agendaitem/list" #Not a list of agendas, but a list of agenda items
url_city_of_orange = "https://www.cityoforange.org/our-city/local-government/city-council/city-council-meetings/-selcat-32#eventcats_46_0_36" #List of city council meetings, agenda in each one
url_huntington_beach = "https://huntingtonbeach.legistar.com/Calendar.aspx" #List of all meetings with agenda links

page_anaheim = requests.get(url_anaheim)
page_santa_ana = requests.get(url_santa_ana)
page_garden_grove = requests.get(url_garden_grove)
page_city_of_orange = requests.get(url_city_of_orange)
page_huntington_beach = requests.get(url_huntington_beach)

soup_an = BeautifulSoup(page_anaheim.content, "lxml")
soup_sa= BeautifulSoup(page_santa_ana.content, "lxml")
soup_gg = BeautifulSoup(page_garden_grove.content, "lxml")
soup_co = BeautifulSoup(page_city_of_orange.content, "lxml")
soup_hb = BeautifulSoup(page_huntington_beach.content, "lxml")

an_results = soup_an.find(id="Meetings")
print(an_results)
print("end")