from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
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

driver.get("https://www.properati.com.ar/s/venta")

def switch_to_new_window(main_window):
    for window_handle in driver.window_handles:
        if window_handle != main_window:
            driver.switch_to.window(window_handle)
            break

def save_data(data):
    fieldnames = ["Dormitorios","Baños","M²","Ubicacion","Tipo de vivienda","Piso","Superficie Cubierta","Precio"]
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

def get_property_type(estate: dict):
    property_type_div = driver.find_element(By.CLASS_NAME, "property-type")
    property_type = property_type_div.find_elements(By.TAG_NAME, "span")[1].text
    estate["Tipo de vivienda"] = property_type

def get_floor(estate: dict):
    try:
        floor_div = driver.find_element(By.CLASS_NAME, "floor")
    except(NoSuchElementException):
        estate["Piso"] = "0"
    else:
        floor = floor_div.find_element(By.CLASS_NAME, "place-features__values").text
        estate["Piso"] = floor

def get_covered_m2(estate: dict):
    try:
        floor_area_div = driver.find_element(By.CLASS_NAME, "floor-area")
    except(NoSuchElementException):
        estate["Superficie Cubierta"] = "Nan"
    else:
        floor_area = floor_area_div.find_elements(By.TAG_NAME, "span")[1].text
        estate["Superficie Cubierta"] = floor_area

def get_location(estate: dict):
    location = driver.find_element(By.CLASS_NAME, "location").text
    estate["Ubicacion"] = location

def get_bathrooms_bedrooms_total_m2_info(estate: dict):
    div = driver.find_element(By.CSS_SELECTOR, ".place-details")
    properties = div.find_elements(By.CLASS_NAME, "details-item-value")
    for property in properties:
        info = property.text
        kv = info.split(" ")
        if kv[1] == "baño":
            estate["Baños"] = kv[0]
        elif kv[1] == "dormitorio":
            estate["Dormitorios"] = kv[0]
        else:
            try:
                estate[kv[1].title()] = kv[0]
            except(Exception):
                print("Couldnt save dadta in dict")

def get_price(estate: dict):
    price = driver.find_element(By.CLASS_NAME, "prices-and-fees__price").text
    estate["Precio"] = price

def get_estate_info():
    estate = {}
    time.sleep(2)
    get_bathrooms_bedrooms_total_m2_info(estate)
    get_location(estate)
    get_property_type(estate)
    get_floor(estate)
    get_covered_m2(estate)
    get_price(estate)
    return estate

def get_properties(original_window):
    estates = []
    links_div = driver.find_element(By.ID, "listings-content")
    links = links_div.find_elements(By.TAG_NAME, "a")
    for link in links:
        link.send_keys(Keys.COMMAND + Keys.RETURN)
        switch_to_new_window(original_window)
        estate = get_estate_info()
        estates.append(estate)
        driver.close()
        driver.switch_to.window(original_window)
    print(estates)
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
            time.sleep(10)
            next_page_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Siguiente']")))
            next_page_button.click()
            original_window = driver.current_window_handle
        except Exception as e:
            print(e)
            pages_remaining = False
        else:
            time.sleep(5)

main()
driver.quit()
