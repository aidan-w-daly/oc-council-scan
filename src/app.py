from re import search
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import datetime
from dateutil import parser
from pathlib import Path
from pypdf import PdfReader

import time
import requests
#from re import A
print("Running...")

ROOT_DIR_PATH = Path(__file__).resolve().parent.parent

#Where do new city council agendas get uploaded? + In what format?
URL_ANAHEIM = "https://www.anaheim.net/2527/Agendas" #list of city council agenda links, + viewer
URL_SANTA_ANA = "https://santa-ana.primegov.com/public/portal?" #iframe, taken from https://www.santa-ana.org/agendas-and-minutes/
URL_GARDEN_GROVE = "https://agendasuite.org/iip/gardengrove/search" #Have to search, filter by city council meetings
URL_CITY_OF_ORANGE = "https://cityoforange.legistar.com/Calendar.aspx" #List of city council meetings, agenda in each one
URL_HUNTINGTON_BEACH = "https://huntingtonbeach.legistar.com/Calendar.aspx" #List of all meetings with agenda links

class Meeting:
    def __init__(self, date, body, city, href):
        self.date = format_date(date)
        self.body = body
        self.city = city
        self.href = href

    def __str__(self):
        return f"{self.date} {self.city} {self.body}: {self.href}"
    
    #TODO Can use @property to allow Meeting.pdf instead of Meeting.pdf() ?
    def pdf_path(self) -> Path:
        '''returns Path, location of Meeting's agenda in pdf form. Uses Path instead of str so Path operations can be used'''
        return ROOT_DIR_PATH / 'agendas' / f'{self.date} {self.city} {self.body}.pdf'
        #return f'{str(ROOT_DIR_PATH)}\agendas\{self.date} {self.city} {self.body}.pdf'



def format_date(date):
    '''take a date in various formats (single-digit days, word/abbreviated/number months, /2024 vs /24) 
    and return string with format mm-dd-yyyy
    '''
    d = parser.parse(date)
    return d.strftime('%m-%d-%Y')

#TODO ALL
#   - Handle agenda cancellation (notify user?)
#       - Parity between cities - do I ignore Cancellation Notice or do I treat it as Agenda?
#   - Date Parity between cities (date of council meeting vs date of agenda upload)
#   - Optimize time to run (selenium)
#       - use bs4 when possible
#       - avoid load times
#       - Can html agenda be used instead of pdf agenda?
#   - Exception handling (necessary? easier to bugfix w/o)

def get_last_cc_all() -> tuple[Meeting]:
    return get_last_cc_an(), get_last_cc_sa(), get_last_cc_gg(), get_last_cc_co(), get_last_cc_hb()


def get_last_cc_an() -> Meeting:
    page_anaheim = requests.get(URL_ANAHEIM)
    soup = BeautifulSoup(page_anaheim.content, "lxml")
    print_agenda = soup.find('a', class_='Hyperlink', title='Print Current Agenda')
    
    #switching to frame inside URL_ANAHEIM to get date (mm/dd/yy h:mm xx)
    page_anaheim = requests.get('https://local.anaheim.net/OpenData/xml/XMLrender.aspx?x=CouncilMeetingAgendas')
    soup = BeautifulSoup(page_anaheim.content, 'lxml')
    agenda_date = soup.find('a', target='fraAgenda')

    #print(agenda_date.text)
    #print(print_agenda['href'])
    return Meeting(agenda_date.text, 'CC', 'Anaheim', print_agenda['href'])

#TODO decrease time to run
def get_last_cc_sa() -> Meeting:
    options = FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    driver.get(URL_SANTA_ANA)

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
        return Meeting(agenda_date_cell.text, 'CC', 'Santa Ana', agenda_link.get_attribute('href'))
    # except:
    #     print("An exception occurred in get_last_agenda_sa()")
    finally:
        driver.quit()

#TODO decrease time to run
#TODO handle cancelled meetings
#   - No way to detect? In URL only place where meeting shows "CANCELLED" is INSIDE pdf
def get_last_cc_gg() -> Meeting:
    options = FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    driver.get(URL_GARDEN_GROVE)

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
        return Meeting(agenda_date_str, 'CC', 'Garden Grove', agenda_link_str)
    # except:
    #     print("An exception occurred in get_last_agenda_gg()")
    finally:
        driver.quit()

#TODO Selenium:
#TODO Optimize!
#TODO   - Can I bypass dropdown alltogether by searching entire table with .contains? would prevent page refresh/load... if not then:
#TODO       - replace time.sleep with appropriate WebDriverWait (already tried element_to_be_clickable, try staleness_of?)
def get_last_cc_co() -> Meeting:
    options = FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    driver.get(URL_CITY_OF_ORANGE)

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


        time.sleep(3)
        #selecting city council in department "dropdown" 
        WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.ID, 'ctl00_ContentPlaceHolder1_lstBodies_Input'))
        )

        departments_dropdown = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_lstBodies_Input')
        driver.execute_script("arguments[0].click();", departments_dropdown) #instead of .click() to bypass html layer
        departments_dropdown.send_keys(Keys.ARROW_DOWN)
        departments_dropdown.send_keys(Keys.ENTER)


        time.sleep(3)
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
        return Meeting(agenda_date_str, 'CC', 'Orange', agenda_link_str)
    # except:
    #     print("An exception occurred in get_last_agenda_co()")
    finally:
        driver.quit()


#TODO Selenium:
#TODO Optimize!
#TODO   - Can I bypass dropdown alltogether by searching entire page? would prevent page refresh/load... if not then:
#TODO       - replace time.sleep with appropriate WebDriverWait (already tried element_to_be_clickable, try staleness_of?)
def get_last_cc_hb() -> Meeting:
    options = FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    driver.get(URL_HUNTINGTON_BEACH)

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
        return Meeting(agenda_date_str, 'CC', 'Huntington Beach', agenda_link_str)
    # except:
    #     print("An exception occurred in get_last_agenda_hb()")
    finally:
        driver.quit()

def download_agenda_pdf(meeting: Meeting) -> None:
    '''download a Meeting's agenda in pdf form to ./agendas folder'''
    
    (ROOT_DIR_PATH / 'agendas').mkdir(exist_ok = True)

    file_path = meeting.pdf_path()

    print(f'downloading to {str(file_path)}')

    response = requests.get(meeting.href)
    with file_path.open('wb') as f:
        f.write(response.content)
    
    print(f'downloading to {str(file_path)} created.')

def download_agenda_txt(*meetings: Meeting) -> None:
    (ROOT_DIR_PATH / 'agendas').mkdir(exist_ok = True)
    for m in meetings:
        pdf_path = m.pdf_path()

        if(not pdf_path.exists()):
            print('Agenda PDF not found.')
            download_agenda_pdf(m)

        txt_path = pdf_path.with_suffix('.txt')
        with txt_path.open('w', encoding="utf-8") as f:
            f.write(pdf_to_str(pdf_path))


#---
#TODO write functions that:
# 1. Convert pdf to text -> str
# 2. Parse text to agenda items -> tuple of strs
# 3. Search tuple for keywords (therefore, searching each )
#---

#TODO finish me
def parse_agenda_pdf(path: Path) -> tuple:
    '''Converts agenda pdf into tuple of agenda items'''
    agenda = pdf_to_str(path)

#TODO is it faster with StringIO object? concatenating with .write(str) instead of +=str?
#TODO extract_text() args: removing headers/footers, text 
def pdf_to_str(pdf_path: Path) -> str:
    reader = PdfReader(pdf_path)
    text = ''
    for page in reader.pages:
        text += f'{page.extract_text(orientations=0)}\n'
    return text

#TODO make recursive, just in case :^)
def delete_agendas():
    '''Deletes contents of agendas folder AND deletes folder, which is NOT a default capability of pathlib
    NOT RECURSIVE! Only deletes FILES immediately under /agenda
    '''
    pass

download_agenda_txt(*get_last_cc_all())