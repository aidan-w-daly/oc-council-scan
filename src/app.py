from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

import time
import requests
#from re import A

print("Running...")

#Where do new city council agendas get uploaded? + In what format?
url_anaheim = "https://www.anaheim.net/2527/Agendas" #list of city council agenda links, + viewer
url_santa_ana = "https://santa-ana.primegov.com/public/portal?" #iframe, taken from https://www.santa-ana.org/agendas-and-minutes/
url_garden_grove = "https://agendasuite.org/iip/gardengrove/search" #Have to search, filter by city council meetings
url_city_of_orange = "https://cityoforange.legistar.com/Calendar.aspx" #List of city council meetings, agenda in each one
url_huntington_beach = "https://huntingtonbeach.legistar.com/Calendar.aspx" #List of all meetings with agenda links


#TODO ALL
#   - Handle agenda cancellation (notify user?)
#   - Optimize time to run (selenium)
#   - Exception handling (necessary? easier to bugfix w/o)

def get_last_agenda_an():
    page_anaheim = requests.get(url_anaheim)
    soup = BeautifulSoup(page_anaheim.content, "lxml")
    print_agenda = soup.find('a', class_='Hyperlink', title='Print Current Agenda')
    
    #switching to frame
    page_anaheim = requests.get('https://local.anaheim.net/OpenData/xml/XMLrender.aspx?x=CouncilMeetingAgendas')
    soup = BeautifulSoup(page_anaheim.content, 'lxml')
    agenda_date = soup.find('a', target='fraAgenda')

    print(agenda_date.text)
    print(print_agenda['href'])

#TODO decrease time to run
def get_last_agenda_sa():
    options = FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    driver.get(url_santa_ana)

    try:
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//select[@name="archivedMeetingsTable_length"]'))
        )
        selection = Select(driver.find_element(By.XPATH, '//select[@name="archivedMeetingsTable_length"]'))
        selection.select_by_value("15")

        #Find table row with data cell with text "Regular City Council" but not "CANCEL" (to filter out notice of cancelled meeting)
        agenda_title_cell = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//tr/td[contains(text(),"Regular City Council")and not(contains(text(), "CANCEL"))]'))
        )
        agenda_date_cell = agenda_title_cell.find_element(By.XPATH, './following-sibling::*[1]')
        agenda_link = agenda_title_cell.find_element(By.XPATH, '..//a[text()="Agenda"]')

        print(agenda_title_cell.text) #Meeting name
        print(agenda_date_cell.text) #Date/Time
        print(agenda_link.get_attribute('href')) #link
    # except:
    #     print("An exception occurred in get_last_agenda_sa()")
    finally:
        driver.quit()

#TODO decrease time to run
#TODO handle cancelled meetings
#   - No way to detect? In URL only place where meeting shows "CANCELLED" is INSIDE pdf
def get_last_agenda_gg():
    options = FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    driver.get(url_garden_grove)

    try:
        WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.ID, 'searchbutton'))
        )
        search_field = driver.find_element(By.ID, 'SearchFilters_SearchString')
        search_field.send_keys('.')

        organization_dropdown = driver.find_element(By.ID, 'SearchFilters_SelectedOrganizationFilterId')
        Select(organization_dropdown).select_by_visible_text('City Council')

        agenda_checkbox = driver.find_element(By.ID, 'SearchFilters_InNotification')
        agenda_checkbox.click()

        search_button = driver.find_element(By.ID, 'searchbutton')
        search_button.click()
        #By default, searches only within last year

        agenda_link = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, ', City Council'))
        )

        print(agenda_link.find_element(By.XPATH, '../preceding-sibling::*[1]').text) #date
        print(agenda_link.get_attribute('href')) #agenda pdf link
    # except:
    #     print("An exception occurred in get_last_agenda_gg()")
    finally:
        driver.quit()

#TODO Selenium:
#TODO   - replace time.sleep with appropriate WebDriverWait (already tried element_to_be_clickable, try staleness_of?)
def get_last_agenda_co():
    options = FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    driver.get(url_city_of_orange)

    try:
        #Selecting 'all years' as "dropdown"(<input>) "option" (<li>)
        WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.ID, 'ctl00_ContentPlaceHolder1_lstYears_Input'))
        )

        date_dropdown = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_lstYears_Input')
        driver.execute_script("arguments[0].click();", date_dropdown) #instead of .click() to bypass html layer

        for x in range(11):
            date_dropdown.send_keys(Keys.ARROW_UP)
        date_dropdown.send_keys(Keys.ENTER)


        time.sleep(5)
        #selecting city council in department "dropdown" 
        WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.ID, 'ctl00_ContentPlaceHolder1_lstBodies_Input'))
        )

        departments_dropdown = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_lstBodies_Input')
        driver.execute_script("arguments[0].click();", departments_dropdown) #instead of .click() to bypass html layer
        departments_dropdown.send_keys(Keys.ARROW_DOWN)
        departments_dropdown.send_keys(Keys.ENTER)


        time.sleep(5)
        #searching table for agenda
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_gridCalendar_ctl00"]'))
        )
        all_meetings_table = driver.find_element(By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_gridCalendar_ctl00"]')
        agenda_link = all_meetings_table.find_element(By.XPATH, './/a[text()="Agenda" or contains(text(), "Cancel")]')

        print(agenda_link.find_element(By.XPATH, '../../preceding-sibling::*[5]').text) #date
        print(agenda_link.get_attribute('href')) #agenda pdf link
    # except:
    #     print("An exception occurred in get_last_agenda_co()")
    finally:
        driver.quit()


# #TODO
def get_last_agenda_hb():
    options = FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    driver.get(url_huntington_beach)

    try:
        #Selecting 'all years' as "dropdown"(<input>) "option" (<li>)
        WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.ID, 'ctl00_ContentPlaceHolder1_lstYears_Input'))
        )

        date_dropdown = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_lstYears_Input')
        driver.execute_script("arguments[0].click();", date_dropdown) #instead of .click() to bypass html layer

        #navigating to 'all years'
        for x in range(13):
            date_dropdown.send_keys(Keys.ARROW_UP)
        date_dropdown.send_keys(Keys.ENTER)


        time.sleep(3)
        #selecting city council in department "dropdown" 
        WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.ID, 'ctl00_ContentPlaceHolder1_lstBodies_Input'))
        )

        departments_dropdown = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_lstBodies_Input')
        driver.execute_script("arguments[0].click();", departments_dropdown) #instead of .click() to bypass html layer
        for x in range(5):
            departments_dropdown.send_keys(Keys.ARROW_DOWN)
        departments_dropdown.send_keys(Keys.ENTER)


        time.sleep(3)
        #searching table for agenda
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_gridCalendar_ctl00"]'))
        )
        all_meetings_table = driver.find_element(By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_gridCalendar_ctl00"]')
        agenda_link = all_meetings_table.find_element(By.XPATH, './/a[contains(text(), "Agenda") or contains(text(), "CANCEL")]')

        print(agenda_link.find_element(By.XPATH, '../../preceding-sibling::*[5]').text) #date
        print(agenda_link.get_attribute('href')) #agenda pdf link
    # except:
    #     print("An exception occurred in get_last_agenda_hb()")
    finally:
        driver.quit()

get_last_agenda_hb()

