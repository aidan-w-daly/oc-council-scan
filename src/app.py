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

class Agenda:
    def __init__(self, date, body, city, href):
        self.date = date
        self.body = body
        self.city = city
        self.href = href

    def __str__(self):
        return f"{self.date} {self.city} {self.body}: {self.href}"

#TODO ALL
#   - Handle agenda cancellation (notify user?)
#       - Parity between cities - do I ignore Cancellation Notice or do I treat it as Agenda?
#   - Date Parity between cities (date of council meeting vs date of agenda upload)
#   - Optimize time to run (selenium)
#       - use bs4 when possible
#       - avoid load times
#       - Can html agenda be used instead of pdf agenda?
#   - Exception handling (necessary? easier to bugfix w/o)

def get_last_agenda_an():
    page_anaheim = requests.get(url_anaheim)
    soup = BeautifulSoup(page_anaheim.content, "lxml")
    print_agenda = soup.find('a', class_='Hyperlink', title='Print Current Agenda')
    
    #switching to frame inside url_anaheim to get date
    page_anaheim = requests.get('https://local.anaheim.net/OpenData/xml/XMLrender.aspx?x=CouncilMeetingAgendas')
    soup = BeautifulSoup(page_anaheim.content, 'lxml')
    agenda_date = soup.find('a', target='fraAgenda')

    #print(agenda_date.text)
    #print(print_agenda['href'])
    return Agenda(agenda_date.text, 'CC', 'Anaheim', print_agenda['href'])

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

        #print(agenda_title_cell.text) #Meeting name
        #print(agenda_date_cell.text) #Date/Time
        #print(agenda_link.get_attribute('href')) #link
        return Agenda(agenda_date_cell.text, 'CC', 'Santa Ana', agenda_link.get_attribute('href'))
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

        #Adding 1 year to end of date range so upcoming meetings are also detected (defaults limit is present day)
        todate_input = driver.find_element(By.ID, 'SearchFilters_ToDateStr')
        todate_mdy = todate_input.get_attribute('value').split('/')
        todate_input.clear()
        todate_input.send_keys(f'{todate_mdy[0]}/{todate_mdy[1]}/{int(todate_mdy[2])+1}')

        search_button = driver.find_element(By.ID, 'searchbutton')
        search_button.click()

        agenda_link_elem = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, ', City Council'))
        )

        agenda_date_str = agenda_link_elem.find_element(By.XPATH, '../preceding-sibling::*[1]').text
        agenda_link_str = agenda_link_elem.get_attribute('href') #pdf link
        #print(agenda_date_str) #date
        #print(agenda_link_str) #agenda pdf link
        return Agenda(agenda_date_str, 'CC', 'Garden Grove', agenda_link_str)
    # except:
    #     print("An exception occurred in get_last_agenda_gg()")
    finally:
        driver.quit()

#TODO Selenium:
#TODO Optimize!
#TODO   - Can I bypass dropdown alltogether by searching entire table with .contains? would prevent page refresh/load... if not then:
#TODO       - replace time.sleep with appropriate WebDriverWait (already tried element_to_be_clickable, try staleness_of?)
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
        agenda_link_elem = all_meetings_table.find_element(By.XPATH, './/a[text()="Agenda" or contains(text(), "Cancel")]')

        agenda_date_str = agenda_link_elem.find_element(By.XPATH, '../../preceding-sibling::*[5]').text
        agenda_link_str = agenda_link_elem.get_attribute('href') #pdf link

        #print(agenda_date_str) #date
        #print(agenda_link_str) #agenda pdf link
        return Agenda(agenda_date_str, 'CC', 'Orange', agenda_link_str)
    # except:
    #     print("An exception occurred in get_last_agenda_co()")
    finally:
        driver.quit()


#TODO Selenium:
#TODO Optimize!
#TODO   - Can I bypass dropdown alltogether by searching entire page? would prevent page refresh/load... if not then:
#TODO       - replace time.sleep with appropriate WebDriverWait (already tried element_to_be_clickable, try staleness_of?)
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
        agenda_link_elem = all_meetings_table.find_element(By.XPATH, './/a[contains(text(), "Agenda") or contains(text(), "CANCEL")]')

        agenda_date_str = agenda_link_elem.find_element(By.XPATH, '../../preceding-sibling::*[5]').text
        agenda_link_str = agenda_link_elem.get_attribute('href') #pdf link :)

        #print(agenda_date_str) #date
        #print(agenda_link_str) #agenda pdf link
        return Agenda(agenda_date_str, 'CC', 'Huntington Beach', agenda_link_str)
    # except:
    #     print("An exception occurred in get_last_agenda_hb()")
    finally:
        driver.quit()

# print(get_last_agenda_an())
# print(get_last_agenda_sa())
print(get_last_agenda_gg())
# print(get_last_agenda_co()) #returns wrong rn because upcoming most recent != most recent on search function
# print(get_last_agenda_hb())



