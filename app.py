
import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By


print("start")

#Where do new city council agendas get uploaded? + In what format?
url_anaheim = "https://www.anaheim.net/2527/Agendas" #list of city council agenda links, + viewer
url_santa_ana = "https://santa-ana.primegov.com/public/portal?" #iframe, taken from https://www.santa-ana.org/agendas-and-minutes/
url_garden_grove = "https://agendasuite.org/iip/gardengrove/agendaitem/list" #Not a list of agendas, but a list of agenda items
url_city_of_orange = "https://www.cityoforange.org/our-city/local-government/city-council/city-council-meetings/-selcat-32#eventcats_46_0_36" #List of city council meetings, agenda in each one
url_huntington_beach = "https://huntingtonbeach.legistar.com/Calendar.aspx" #List of all meetings with agenda links

#TODO also find date of most recent meeting
def get_last_agenda_an():
    page_anaheim = requests.get(url_anaheim)
    soup_an = BeautifulSoup(page_anaheim.content, "lxml")
    agenda = soup_an.find('a', class_='Hyperlink', title='Print Current Agenda')

    print(agenda['href'])

#Website has possible locations for most recent agenda: tables "Current and Upcoming meetings" and "archived".
# TODO the table bodies <tbody> are inaccessible with beautifulsoup alone, need selenium
# TODO Locate table cell <td> which contains meeting title "Regular City Council."
# TODO Get date from sibling cell <td> (common parent is row <tr>) 
# TODO Get agenda link <a> from sibling cell <td> (from same parent row <tr>)
def get_last_agenda_sa():
    # header_mask =   {
    #                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0',
    #                 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
    #                 'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    #                 'Accept-Encoding': 'gzip, deflate, br, zstd',
    #                 'Accept-Language': 'en-US,en;q=0.5',
    #                 'Connection': 'keep-alive'
    #                 }
    # page_santa_ana = requests.get(url_santa_ana)
    # soup_sa = BeautifulSoup(page_santa_ana.content, "lxml")

    # #search by title cell <td>, then get parent row <tr>, to get sibling agenda link <a>
    # archived_table = soup_sa.find_all('td', string='Regular City Council and Housing Authority Meeting')
    # print(archived_table)

    #SELENIUM:
    #bs4 thinks archived_table.tbody is childless, even with http header. need selenium to access this <tbody> and its data <td>
    #It is loaded via JS, check network tab of FF devtools
    driver = webdriver.Firefox()
    driver.get(url_santa_ana)

    time.sleep(5) #TODO sleep doesn't work every time, replace with wait for element to load
    #agenda_title_cell = driver.find_element(By.XPATH, '//table[@id="archivedMeetingsTable"]/tbody/tr/td[contains(text(),"Regular City Council")]')
    agenda_title_cell = driver.find_element(By.XPATH, '//tr/td[contains(text(),"Regular City Council")]')
    agenda_date_cell = agenda_title_cell.find_element(By.XPATH, './following-sibling::*[1]')
    agenda_link = agenda_title_cell.find_element(By.XPATH, '..//a[text()="Agenda"]')

    print(agenda_title_cell.text)
    print(agenda_date_cell.text)
    print(agenda_link.get_attribute('href'))
    driver.close()

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

get_last_agenda_sa()

