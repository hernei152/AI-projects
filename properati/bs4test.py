from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import requests
import time
import csv

chrome_driver_path = "/Users/bautista/Desktop/chromedriver"
options = webdriver.ChromeOptions()
options.add_experimental_option("detach", True)
options.add_argument("--start-maximized")
options.add_experimental_option("detach", True)  
service = Service(executable_path=chrome_driver_path, log_path="NUL")
driver = webdriver.Chrome(options=options, service=service)

#driver.get("https://www.properati.com.ar/s/venta")

def switch_to_new_window(main_window):
    for window_handle in driver.window_handles:
        if window_handle != main_window:
            driver.switch_to.window(window_handle)
            break

def save_data(data):
    fieldnames = ["Bedrooms","Bathrooms","m²","Location","Property type","Floor","Covered m²","Price"]
    file_name = "properati/realstate.csv"
    if data:  
        with open(file_name, "w", newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()  
            for row in data:
                try:
                    writer.writerow(row)
                except ValueError as e:
                    print(f"Skipping row due to error: {e}")

def get_property_type(soup: BeautifulSoup):
    property_type_div = soup.find(name="div", class_="property-type")
    property_type = property_type_div.find_all(name="span")[1].text
    if property_type == None:
        return "Nan"
    else:
        return property_type

def get_floor(soup: BeautifulSoup):
    floor_div = soup.find(name="div", class_="floor")
    if floor_div == None:
        return "0"
    else:
        floor = floor_div.find(name="span", class_="place-features__values").text
        return floor

def get_covered_m2(soup: BeautifulSoup):
    floor_area_div = soup.find(name="div", class_="floor-area")
    if floor_area_div == None:
        return "Nan"
    else:
        floor_area = floor_area_div.find_all(name="span")[1].text
        return floor_area

def get_location(soup: BeautifulSoup):
    location = soup.find(name="div", class_="location").text
    if location == None:
        return "Nan"
    else:
        return location.strip()

def get_bathrooms_bedrooms_total_m2_info(soup: BeautifulSoup):
    properties = soup.find_all(name="div",class_="details-item-value")
    prop_info = {
        "Bedrooms":"Nan",
        "Bathrooms":"Nan",
        "m²":"Nan"
    }
    if properties != None:
        for property in properties:
            info = property.text
            kv = info.split(" ")
            if kv[1] == "baño" or kv[1] == "baños":
                prop_info["Bathrooms"] = kv[0]
            if kv[1] == "dormitorio" or kv[1] == "dormitorios":
                prop_info["Bedrooms"] = kv[0]
            if kv[1] == "m²":
                prop_info["m²"] = kv[0]

    return prop_info

def get_price(soup: BeautifulSoup):

    price = soup.find(name="div", class_="prices-and-fees__price").text
    if price == None:
        return "Nan"
    else:
        return price.strip()

def get_estate_info(soup: BeautifulSoup):
    prop_info = get_bathrooms_bedrooms_total_m2_info(soup)
    location = get_location(soup)
    property_type = get_property_type(soup)
    floor = get_floor(soup)
    covered_m2 = get_covered_m2(soup)
    price = get_price(soup)
    estate = {}
    estate.update(prop_info)
    estate.update({
        "Location":location,
        "Property type":property_type,
        "Floor":floor,
        "Covered m²":covered_m2,
        "Price":price
    })
    return estate

def get_soup(link: str):
    response = requests.get(f"https://www.properati.com.ar/{link}")
    yc_webpage = response.text
    soup = BeautifulSoup(yc_webpage, "html.parser")
    return soup

def get_links():
    response = requests.get("https://www.properati.com.ar/s/venta")
    yc_webpage = response.text
    main_soup = BeautifulSoup(yc_webpage, "html.parser")
    links_div = main_soup.find(name="div", id="listings-content")
    anchors = links_div.find_all(name="a")
    links = [a.get('href') for a in anchors]
    return links

def function_timer(func):
    def wrapper():
        start = time.time()
        func()
        finish = time.time()
        print(f"Executed in {finish - start}")
    return wrapper

@function_timer
def get_properties():
    estates = []
    links = get_links()

    for link in links:
        soup = get_soup(link)
        estate = get_estate_info(soup)
        estates.append(estate)

    save_data(estates)

def main():
    pages_remaining = True
    original_window = driver.current_window_handle

    while pages_remaining:
        get_properties(original_window)
        try:
            wait = WebDriverWait(driver, 30)
            next_page_button = wait.until(EC.presence_of_element_located((By.XPATH, "//span[text()='Siguiente']")))
            driver.execute_script("arguments[0].scrollIntoView(true);", next_page_button)
            time.sleep(5)
            next_page_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Siguiente']")))
            next_page_button.click()
            original_window = driver.current_window_handle
        except Exception as e:
            print(e)
            pages_remaining = False
        else:
            time.sleep(5)

main()
