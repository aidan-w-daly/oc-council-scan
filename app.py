import requests
from bs4 import BeautifulSoup
import io
from PyPDF2 import PdfFileReader

url_anaheim = "https://www.anaheim.net/2527/Agendas" #list of city council agenda links, + viewer
url_santa_ana = "https://www.santa-ana.org/agendas-and-minutes/" #list of ALL meetings, with links to agenda
url_garden_grove = "https://agendasuite.org/iip/gardengrove/agendaitem/list" #Not a list of agendas, but a list of agenda items
url_city_of_orange = "https://www.cityoforange.org/our-city/local-government/city-council/city-council-meetings/-selcat-32#eventcats_46_0_36" #List of city council meetings, agenda in each one
url_huntington_beach = "https://huntingtonbeach.legistar.com/Calendar.aspx" #List of all meetings with agenda links