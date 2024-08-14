
import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import Select


print("Running...")

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

#Selenium
def get_last_agenda_sa():
    options = FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    driver.get(url_santa_ana)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//select[@name="archivedMeetingsTable_length"]'))
        )
        selection = Select(driver.find_element(By.XPATH, '//select[@name="archivedMeetingsTable_length"]'))
        selection.select_by_value("15")

        agenda_title_cell = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//tr/td[contains(text(),"Regular City Council")]'))
        )
        agenda_date_cell = agenda_title_cell.find_element(By.XPATH, './following-sibling::*[1]')
        agenda_link = agenda_title_cell.find_element(By.XPATH, '..//a[text()="Agenda"]')

        print(agenda_title_cell.text)
        print(agenda_date_cell.text)
        print(agenda_link.get_attribute('href'))
    except:
        print("An exception occurred.")
    finally:
        driver.quit()

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

