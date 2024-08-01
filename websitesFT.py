import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup, SoupStrainer
import requests
import tldextract
import re
import numpy as np
import pandas as pd
import adblockparser
from urllib.parse import urlparse
import argparse
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
import random
import pyautogui
from webdriver_manager.chrome import ChromeDriverManager
import traceback
import os
import psutil
from browsermobproxy import Server
import json
import validators
from operator import attrgetter
from BidCollector import BidCollector
from FullPageScreenshotCollector import FullPageScreenshotCollector
from AdCollector import AdCollector


# WHEN VISITING WEBSITES ADD A SCROLL LIMIT [DONE!!]
# PRODUCT VISITING ADD IN FIRST STEP AN AFFIRMATION!! (SEE NOTES) [RONIT!!]
# CLICK ON 'ADD TO BAD' THING! [RONIT!!]
# WHY SSL ERROR???? [RONIT!!]
# REMOVE ERROR (MITM) [RONIT!!]
# Intgrate JS execute to get 'MoatSuperV26' object!!
# REAFFIRMATION!!!!! [RONIT!!]
# SCREENSHOT ISSUE?? FIX LENGTH FOR VERRRYYY LONG PAGES? [RONIT!!]


# Your connection is not private! (asks to click on Advanced)
# Google Ad blocks the entire page!
# Study the kind of ads that appear when opening a website! 
# Show notifications!
# Sign up for news letter!
# Customised accept cookies (blocks the page)!
# Customised sign up for newletter (blocks the page)!
# Defo scroll till bottom and go back up and add a waiting time so that ads can load!
# Cloudfare verify you are a human on entry to a website??!


# MAKE CHANGES IN THE CODE FOR CONTROLLED AND TREATMENT PHASE!!!!! (2 CHROMEDRIVERS)


# TIGERVNC FOR HEADLESS! [GO HEADLESS]
# LOGGING ERRORS AND EVENTS



NUMBER_OF_PAUSES = 6
RANDOM_SLEEP_MIN = 1
RANDOM_SLEEP_MAX = 5
NUM_MOUSE_MOVES = 3

NUMBER_OF_WEBSITES = 108
WEBSITES_PER_PERSONA = 3
PERSONAS = (int) (NUMBER_OF_WEBSITES / WEBSITES_PER_PERSONA)

PORT_TREATMENT = 8024
PORT_CONTROLLED = 8034
PORT = 8081




def getChromeOptionsObject():
    chrome_options = webdriver.ChromeOptions()

    # chrome_options.add_argument('--headless')
    
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    # chrome_options.add_argument("--disable-gpu")
    
    ROOT_DIRECTORY = os.getcwd()
    extension_dir = os.path.join(ROOT_DIRECTORY, "consent-extension", "Consent-O-Matic", "Extension")
    chrome_options.add_argument('--load-extension={}'.format(extension_dir))
    
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--window-size=1536,864")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    # chrome_options.add_argument(directory)
    # chrome_options.add_argument(profileDirectory)
    # chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"

    return chrome_options



def configureProxy(port):
    '''
    Instantiate and start browsermobproxy to collect HAR files and accordingly configure chrome options
    Killing open ports:
        - lsof -i:<port>
        - kill -9 <PID>
    '''
    ROOT_DIRECTORY = os.getcwd()


    try:
        server = Server(os.path.join(ROOT_DIRECTORY, "browsermob-proxy-2.1.4", "bin", "browsermob-proxy"), options={'port': port})
        server.start()
        # print("THE SERVER IS THIS ELEMENT", server)
        time.sleep(2)
        proxy = server.create_proxy(params=dict(trustAllServers=True))
    except BaseException as error:
        print("\nAn exception occurred:", traceback.format_exc(), "in configureProxy()")
        return None, None, None

    # Instantiate chromedriver options
    chrome_options = getChromeOptionsObject()

    # Associate proxy-related settings to the chromedriver
    chrome_options.add_argument("--proxy-server={}".format(proxy.proxy))
    # chrome_options.add_argument("--ignore-ssl-errors=yes")
    # chrome_options.add_argument("--use-littleproxy false")
    # chrome_options.add_argument("--proxy=127.0.0.1:%s" % port)

    return server, proxy, chrome_options

    

def closeProxyServer(proxy, server):
    try:
        proxy.close()
    except:
        pass
    
    try:
        server.close()
    except:
        pass



def killBrowserMobProxyInstances(port):    
    try:
        # Check for running instances of browsermobproxy
        output = os.popen('tasklist | findstr /C:"browsermob"').read().strip()
        if output:
            count = len(output.splitlines())
            print(f"Total browsermobproxy instances currently running: {count}")
        else:
            print("No browsermobproxy instances currently running.")

        # Kill processes using tasklist and taskkill
        output = os.popen('tasklist /fi "imagename eq browsermob*" /fo csv /nh').read()
        lines = output.strip().split('\n')
        for line in lines:
            if "browsermob" in line:
                # Extract the process ID (PID), which is the second value in the comma-separated line
                pid = line.split(",")[1].strip('"')
                # Terminate the process using taskkill
                result = os.system(f"taskkill /f /pid {pid}")
                print(f"The status for killing process of pid {pid} is: {result}")

        # Check again for any remaining instances
        output = os.popen('tasklist | findstr /C:"browsermob"').read().strip()
        if output:
            count = len(output.splitlines())
            print(f"Total browsermobproxy instances currently running: {count}")
        else:
            print("No browsermobproxy instances currently running.")

    except Exception as e:
        print(f"Exception occurred: {e}")

    # Using psutil to kill remaining instances
    for proc in psutil.process_iter():
        if 'browsermob' in proc.name().lower():
            try:
                proc.kill()
                print(f"Process {proc.name()} with PID {proc.pid} killed successfully.")
            except Exception as e:
                print(f"Could not kill process {proc.name()} with PID {proc.pid}. Error: {e}")

    # Final check for any remaining instances
    output = os.popen('tasklist | findstr /C:"browsermob"').read().strip()
    if output:
        count = len(output.splitlines())
        print(f"Total browsermobproxy instances currently running: {count}")
    else:
        print("No browsermobproxy instances currently running.")

    # Kill processes using the specified port
    try:
        for proc in psutil.process_iter():
            try:
                for conns in proc.connections(kind='inet'):
                    if conns.laddr.port == port:
                        os.system(f"taskkill /f /pid {proc.pid}")
                        print(f"Killed process {proc.name()} with PID {proc.pid} using port {port}.")
            except Exception as e:
                print(f"Error in checking the local address/port of a connection for process {proc.name()}. Error: {e}")
    except Exception as e:
        print(f"Error in using psutil to terminate port connections. Error: {e}")

    print("")



def killChromeInstances():
    try:
        # Check for running instances of Chrome
        output = os.popen('tasklist | findstr /C:"chrome"').read().strip()
        if output:
            count = len(output.splitlines())
            print(f"Total chrome instances currently running: {count}")
        else:
            print("No chrome instances currently running.")

        # Kill processes using tasklist and taskkill
        output = os.popen('tasklist /fi "imagename eq chrome*" /fo csv /nh').read()
        lines = output.strip().split('\n')
        for line in lines:
            if "chrome" in line:
                # Extract the process ID (PID), which is the second value in the comma-separated line
                pid = line.split(",")[1].strip('"')
                # Terminate the process using taskkill
                result = os.system(f"taskkill /f /pid {pid}")
                print(f"The status for killing chrome process of pid {pid} is: {result}")

        # Kill chrome.exe directly
        result = os.system('taskkill /f /im "chrome.exe"')
        print(f"The status for killing chrome.exe line is: {result} (if 128, then ERROR in finding chrome.exe)")

        # Check again for any remaining instances
        output = os.popen('tasklist | findstr /C:"chrome"').read().strip()
        if output:
            count = len(output.splitlines())
            print(f"Total chrome instances currently running: {count}")
        else:
            print("No chrome instances currently running.")

    except Exception as e:
        print(f"Exception occurred: {e}")

    # Using psutil to kill remaining instances
    for proc in psutil.process_iter():
        if 'chrome' in proc.name().lower():
            try:
                proc.kill()
                print(f"Process {proc.name()} with PID {proc.pid} killed successfully.")
            except Exception as e:
                print(f"Could not kill process {proc.name()} with PID {proc.pid}. Error: {e}")

    # Final check for any remaining instances
    output = os.popen('tasklist | findstr /C:"chrome"').read().strip()
    if output:
        count = len(output.splitlines())
        print(f"Total chrome instances currently running: {count}")
    else:
        print("No chrome instances currently running.")

    print("")




def consents(driver):

    # ########################## PROBLEM???? #########################################
    # pop-up request to access location - HANDLED! (Deny most probably)
    try:
        buttonPreciseLocation = driver.find_element(By.XPATH, r"/html/body/div[5]/div/div[4]/div/div[2]/span/div/div[2]/div[3]/g-raised-button/div/div")
        buttonPreciseLocation.click()
        time.sleep(3)

    except Exception as e:
        pass


    # # ########################## PROBLEM???? #########################################
    # # USE PRECISE LOCATION - HANDLED! (Not now)
    try:
        not_now_button = WebDriverWait(driver, 4).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Not now')]"))
        )

        # Click on the 'Not now' button
        not_now_button.click()

    except Exception as e:
        pass


    # MISSED CONSENTS!
    try:
        missed = driver.find_elements(By.XPATH, './/*[not(self::script) and self::button]')
        button_click = []
        for ele in missed:
            try:
                ele.str_html = ele.get_attribute('innerHTML').replace('\n', '').replace('\t', '')
                if (re.match(r'(?:.*)(?:acept|accept|accet|got|agree|ok|cookie_accept|accept_cookie|SUTINKU|keep|close|cerrar)(?:.*)', ele.str_html, re.IGNORECASE) or 
                    re.match(r'(?:.*)(?:\ acept|\ accept|\ accet|\ got|\ agree|\ ok|\ cookie_accept|\ accept_cookie|\ SUTINKU)(?:.*)', ele.str_html, re.IGNORECASE)) and len(ele.text) < 16:
                    ele.html_len = len(ele.get_attribute("innerHTML"))
                    if ele.is_displayed():
                        button_click.append(ele)
            except:
                continue
        if button_click:
            bc = min(button_click, key=attrgetter('html_len'))
            bc.click()
            pass
    except:
        pass

    consent_accept_options = ["Yes, I am an EU/EEA citizen", "Accept All Cookies", "Accept All", "Allow All", "Fine By Me", "Yes, I’m happy", "YES, I AGREE", "Yes, I agree", "Prosseguir", "I Accept", "Got it", "Agree and proceed", "AGREE", "Agree", "Accept", "ACCEPT", "Continue", "OK"]
    for opt in consent_accept_options:
        try:
            elements = driver.find_elements(By.XPATH, '//button[contains(text(), "{}")]'.format(opt))
            for ele in elements:
                ele.click()
        except:
            continue

    time.sleep(2)
    
    return









# Function to move the mouse randomly within the screen boundaries
def move_mouse_randomly(mouseMoves):
    screen_width, screen_height = pyautogui.size()
    
    while mouseMoves:
        # # Generate random coordinates within the screen boundaries
        # x = random.randint(0, screen_width)
        # y = random.randint(0, screen_height)
        
        # # Move the mouse to the random coordinates
        # pyautogui.moveTo(x, y, duration=random.uniform(0.1, 0.5))
        
        # # Pause for a random duration before the next move
        # time.sleep(random.uniform(0.5, 3.0))

        mouseMoves = mouseMoves - 1




def visitingWebsite(driver, brand, impFlag):

    if impFlag == 1:

        driver.execute_script("window.open('');")   
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(2)

    # google_search_button = r"/html/body/div[1]/div[3]/form/div[1]/div[1]/div[1]/div/div[2]/textarea"
    google_search_button = r"//textarea[@aria-label='Search']"

    # SEARCHING THE BRANDS DOMAIN ON GOOGLE AND CLICKING ON THE FIRST RESULT
    driver.get("https://google.com")
    flag = 0
    while (flag == 0):
        try:
            button = driver.find_element(By.XPATH, google_search_button)
            flag = 1
        except Exception as e:
            pass
    send = brand + ".com"
    button.send_keys(send)
    button.send_keys(Keys.RETURN)
    time.sleep(2)
    consents(driver)

    print("check1")
    # driver.find_element(By.XPATH, '(//h3)[1]').click()
    # driver.find_element(By.CSS_SELECTOR, "div.tF2Cxc a").click()
    driver.find_element(By.XPATH, '//div[@id="rso"]//div[1]//a').click()
    print("check2")
    time.sleep(3)
    consents(driver)

    
    # SCROLLING
    try:
        total_height = int(driver.execute_script("return document.body.scrollHeight"))
        if total_height <= 0:
            raise ValueError("Scroll height is less than zero.")
        if total_height > 20000:
            total_height = 20000
        random_integers = random.sample(range(1, total_height + 1), NUMBER_OF_PAUSES)
        move_mouse_randomly(random.randint(0, NUM_MOUSE_MOVES))
        for i in range(1, total_height, 2):
            driver.execute_script("window.scrollTo(0, {});".format(i))
            if i in random_integers:
                move_mouse_randomly(random.randint(0, NUM_MOUSE_MOVES))
                time.sleep(random.randint(RANDOM_SLEEP_MIN, RANDOM_SLEEP_MAX))
        time.sleep(2)
        try:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
            time.sleep(3)
        except Exception as e:
            print("error areaaaaaa 3 ", e)
    except Exception as e:
        print("Couldn't scroll for website", brand, "and error is", e)


    # Get all anchor tags
    try:
        anchor_tags = driver.find_elements(By.TAG_NAME, 'a')
    except:
        return

    # Extract the URL and text for each anchor tag
    anchor_tag_info = []
    if anchor_tags:
        for anchor_tag in anchor_tags:
            try:
                url = anchor_tag.get_attribute('href')
                text = anchor_tag.text
                title = anchor_tag.get_attribute('title')
                name = anchor_tag.get_attribute('class')
                style = anchor_tag.get_attribute('style')
                if 'product' in url or 'product' in title or 'product' in name or 'product' in style or 'product' in text or 'men' in url or 'women' in url or 'kid' in url:
                    anchor_tag_info.append((url, text, name, title, style))
            except:
                # print("Error getting href for anchor tag")
                pass

    # Select a random url
    if anchor_tag_info:
        random_url = random.sample(anchor_tag_info, 1)
    else:
        return


    # print("The supposed tuple is:", random_url)
    url = random_url[0][0]
    # print("THE FOOKIN URL BEFORE TRY-EXCEPT IS:", url)


    # SCROLLING
    element = driver.find_element(By.PARTIAL_LINK_TEXT, random_url[0][1])
    flagClicked = False
    try:
        total_height = int(driver.execute_script("return document.body.scrollHeight"))
        if total_height <= 0:
            raise ValueError("Scroll height is less than zero.")
        for i in range(1, total_height, 30):
            try:
                element.click()
                flagClicked = True
                print("Clicking:", element.get_attribute('href'))
                break
            except:
                pass
            driver.execute_script("window.scrollTo(0, {});".format(i))
        time.sleep(2)

    except Exception as e:
        print("Couldn't scroll for clicking a subpage for ", brand, "and error is", e)


    if not flagClicked:
        print("Not Click")
        print(url)
        driver.get(url)
    time.sleep(1)
    consents(driver)


    # SCROLLING
    try:
        total_height = int(driver.execute_script("return document.body.scrollHeight"))
        if total_height <= 0:
            raise ValueError("Scroll height is less than zero.")
        if total_height > 20000:
            total_height = 20000
        random_integers = random.sample(range(1, total_height + 1), NUMBER_OF_PAUSES)
        move_mouse_randomly(random.randint(0, NUM_MOUSE_MOVES))
        for i in range(1, total_height, 2):
            driver.execute_script("window.scrollTo(0, {});".format(i))
            if i in random_integers:
                move_mouse_randomly(random.randint(0, NUM_MOUSE_MOVES))
                time.sleep(random.randint(RANDOM_SLEEP_MIN, RANDOM_SLEEP_MAX))
        time.sleep(2)
        try:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
            time.sleep(3)
        except Exception as e:
            print("error areaaaaaa 3 ", e)
    except Exception as e:
        print("Couldn't scroll for website", brand, "and error is", e)

    
    if impFlag == 1:

        driver.execute_script("window.open('');")   
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(2)




def createPersona(brand, driver, brandWebsite):


    # [1] BRAND.COM
    # [2] FACEBOOK
    # [3] FACEBOOK REDIRECTION
    # [4] INSTAGRAM
    # [5] GET BRAND WEBSITE

    ########################################## PICK A BRAND ####################################################
    # We pick a brand from the pre-compiled list of all the brands
    brand = brand.lower()
    print("The brand is :", brand)
    ############################################################################################################




    # directory = "C:\\Users\\sdala\\AppData\\Local\\Google\\Chrome\\User Data\\"
    # directory = "user-data-dir=" + directory + brand + str(numPersonas)
    # profileDirectory = "profile-directory=" + brand + "Persona" + str(numPersonas)

    # chrome_options = getChromeOptionsObject(directory, profileDirectory)


    # 'user-data-dir=C:\\Users\\gupta\\AppData\\Local\\Google\\Chrome\\User Data'
    # 'profile-directory=Profile 1'
    

    print("it worked!")

    ################################################# PROBLEM?? #########################################################
    # The tag of the button changes every once in a while? What to do about it??
    # google_search_button = r"/html/body/div[1]/div[3]/form/div[1]/div[1]/div[1]/div/div[2]/textarea"
    google_search_button = r"//textarea[@aria-label='Search']"

    #################### PRODUCT CLICKING random links?? #########################################
    visitingWebsite(driver, brand, 0)


    # FACEBOOK FACEBOOK FACEBOOK FACEBOOK FACEBOOK
    driver.execute_script("window.open('');")   
    driver.switch_to.window(driver.window_handles[-1])
    driver.get('https://google.com')
    time.sleep(2)
    # 50 - 50 % CHANCE OF LOCATING THIS BUTTON!!!!!!! (let us see how it works now)
    flag = 0
    while (flag == 0):
        try:
            ################################################# PROBLEM?? #########################################################
            # The tag of the button changes every once in a while? What to do about it??
            button = driver.find_element(By.XPATH, google_search_button)
            flag = 1
        except Exception as e:
            pass
    send = brand + " facebook"
    button.send_keys(send)
    button.send_keys(Keys.RETURN)
    time.sleep(2)
    consents(driver)

    # driver.find_element(By.XPATH, '(//h3)[1]').click()
    # driver.find_element(By.CSS_SELECTOR, "div.tF2Cxc a").click()
    driver.find_element(By.XPATH, '//div[@id="rso"]//div[1]//a').click()
    time.sleep(3)
    consents(driver)

    # ERROR PRONE!!! (let us see how it works now)
    # Facebook scrolling and redirection and then scrolling
    try:
        # Finding the 'X' button
        # x_button = driver.find_element(By.XPATH, r"/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[1]/div/div[2]/div/div/div/div[1]/div")
        x_button = driver.find_element(By.XPATH, '//div[@aria-label="Close"]')
        x_button.click()
        time.sleep(2)

        # Scrolling the facebook page
        total_height = int(driver.execute_script("return document.body.scrollHeight"))
        if total_height <= 0:
            raise ValueError("Scroll height is less than zero.")
        total_height = total_height * 2
        random_integers = random.sample(range(1, total_height + 1), NUMBER_OF_PAUSES)
        move_mouse_randomly(random.randint(0, NUM_MOUSE_MOVES))
        for i in range(1, total_height, 2):
            driver.execute_script("window.scrollTo(0, {});".format(i))
            if i in random_integers:
                move_mouse_randomly(random.randint(0, NUM_MOUSE_MOVES))
                time.sleep(random.randint(RANDOM_SLEEP_MIN, RANDOM_SLEEP_MAX))
        time.sleep(2)

        # Redirection using the facebook link
        # The class of the 'span' tag does not dynamically change with each run and is the same for every facebook homepage!!!
        try:
            url = driver.find_element(By.XPATH, r'(//span)[@class="x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xudqn12 x3x7a5m x6prxxf xvq8zen xo1l8bm x1qq9wsj x1yc453h"]')
            url.click()
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(3)
            consents(driver)

            ################################################# ??? #########################################################
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "footer")))
            except Exception as e:
                pass


            total_height = int(driver.execute_script("return document.body.scrollHeight"))
            if total_height <= 0:
                raise ValueError("Scroll height is less than zero.")
            if total_height > 20000:
                total_height = 20000
            random_integers = random.sample(range(1, total_height + 1), NUMBER_OF_PAUSES)
            move_mouse_randomly(random.randint(0, NUM_MOUSE_MOVES))
            for i in range(1, total_height, 2):
                driver.execute_script("window.scrollTo(0, {});".format(i))
                if i in random_integers:
                    move_mouse_randomly(random.randint(0, NUM_MOUSE_MOVES))
                    time.sleep(random.randint(RANDOM_SLEEP_MIN, RANDOM_SLEEP_MAX))
            time.sleep(2)
            try:
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
                time.sleep(3)
            except Exception as e:
                print("error areaaaaaa 3 ", e)



        except Exception as e:
            pass

    except Exception as e:
        pass


    # INSTAGRAM INSTAGRAM INSTAGRAM INSTAGRAM INSTAGRAM
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get("https://google.com")
    flag = 0
    while (flag == 0):
        try:
            button = driver.find_element(By.XPATH, google_search_button)
            flag = 1
        except Exception as e:
            pass
    send = brand + " instagram"
    button.send_keys(send)
    button.send_keys(Keys.RETURN)
    time.sleep(2)
    consents(driver)

    try:
        # driver.find_element(By.XPATH, '(//h3)[1]').click()
        # stored = driver.find_element(By.CSS_SELECTOR, "div.tF2Cxc a")
        stored = driver.find_element(By.XPATH, '//div[@id="rso"]//div[1]//a')
        stored.click()
        time.sleep(7)
        consents(driver)

        total_height = int(driver.execute_script("return document.body.scrollHeight"))
        if total_height <= 0:
            raise ValueError("Scroll height is less than zero.")
        random_integers = random.sample(range(1, total_height + 1), NUMBER_OF_PAUSES)
        move_mouse_randomly(random.randint(0, NUM_MOUSE_MOVES))
        for i in range(1, total_height, 2):
            driver.execute_script("window.scrollTo(0, {});".format(i))
            if i in random_integers:
                move_mouse_randomly(random.randint(0, NUM_MOUSE_MOVES))
                time.sleep(random.randint(RANDOM_SLEEP_MIN, RANDOM_SLEEP_MAX))
        time.sleep(2)
        try:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
            time.sleep(1)
        except Exception as e:
            print("error areaaaaaa 2 ", e)

    except Exception as e:
        pass



    # Opens a new window and directly get the website domain on it
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    try:
        brandWebsite = "http://" + brandWebsite
        
        print("the brand website during person building stage 5 is:", brandWebsite)
        driver.get(brandWebsite)
        time.sleep(4)
        consents(driver)
        
        # Scrolling the brands website when directly websearched the domain
        total_height = int(driver.execute_script("return document.body.scrollHeight"))
        if total_height <= 0:
            raise ValueError("Scroll height is less than zero.")
        random_integers = random.sample(range(1, total_height + 1), NUMBER_OF_PAUSES)
        move_mouse_randomly(random.randint(0, NUM_MOUSE_MOVES))
        for i in range(1, total_height, 2):
            driver.execute_script("window.scrollTo(0, {});".format(i))
            if i in random_integers:
                move_mouse_randomly(random.randint(0, NUM_MOUSE_MOVES))
                time.sleep(random.randint(RANDOM_SLEEP_MIN, RANDOM_SLEEP_MAX))
        time.sleep(2)
        try:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
            time.sleep(1)
        except Exception as e:
            print("error areaaaaaa 3 ", e)
    except Exception as e:
        print("Website not reachable!!")


    print("FIN.")



def dataCollection(domain_dir, profile1, website, websiteDomain, driver, proxy):

    ROOT_DIRECTORY = os.getcwd()
    profile = profile1.lower()

    # STORAGE DIRECTORIES
    # filename = f"part_{part}_bids.json"
    filename = f"{profile}_{websiteDomain}_bids.json"
    bid_filepath = os.path.join(domain_dir, filename)

    filename = f"{profile}_{websiteDomain}_har.json"
    har_filepath = os.path.join(domain_dir, filename)

    filename = f"{profile}_{websiteDomain}_ssbefore.png"
    ssbefore_filepath = os.path.join(domain_dir, filename)

    filename = f"{profile}_{websiteDomain}_ssafter.png"
    ssafter_filepath = os.path.join(domain_dir, filename)

    filename = f"{profile}_{websiteDomain}_moatsuperv26.json"
    moat_filepath = os.path.join(domain_dir, filename)

    screenshotbefore_path = os.path.join(domain_dir, "Screenshots_Before")
    if not(os.path.exists(screenshotbefore_path)):
        os.makedirs(screenshotbefore_path)

    screenshotafter_path = os.path.join(domain_dir, "Screenshots_After")
    if not(os.path.exists(screenshotafter_path)):
        os.makedirs(screenshotafter_path)

    ad_path = os.path.join(domain_dir, "Ads")
    if not(os.path.exists(ad_path)):
        os.makedirs(ad_path)



    # READY THE PROXY FOR COLLECTING HAR
    proxy.new_har(har_filepath, options={'captureHeaders': True,'captureContent':True, 'captureCookies': True, 'captureBinaryContent': True})



    # GET THE FOOKIN WEBSITE!!!!!!!!!!!!!!!!!
    try:
        driver.get(website)
        time.sleep(5)
    except Exception as e:
        print()
        print("THE DATA COLLECTION COULD NOT HAPPEN FOR THIS DOMAIN :", domain_dir)
        print()
        return
    


    # MOATSUPERV26 - ATTEMPT1!
    json_file = ""
    try:
        json_file = driver.execute_script("""
	var JSON_data = MoatSuperV26.jsonp
	JSON_data = JSON.stringify(JSON_data)
	return JSON_data
	""")
        
        if json_file != "":
            
            json_data = json.loads(json_file)

            # Writing JSON data to a file with indentation
            try:
                with open(moat_filepath, 'w') as json_fileobj:
                    json.dump(json_data, json_fileobj, indent=4)

                print("JSON data has been successfully written to 'data.json' file.")
                print()
            except Exception as e:
                print("An error occurred when writing json into the system", e)
                print()

    except Exception as e:
        print("error for website collecting MOATSUPERV26 ", website)
        print()


    # SCREENSHOT - BEFORE!   
    # ss_object = FullPageScreenshotCollector(profile, ssbefore_filepath, screenshotbefore_path)
    # ss_object.captureFullScreenshot(driver)
    # driver.maximize_window()
    # driver.execute_script("window.scrollTo(0, 0);")

    
    # SCROLLING
    try:
        total_height = int(driver.execute_script("return document.body.scrollHeight"))
        print("alright the height is", total_height)
        if total_height <= 0:
            raise ValueError("Scroll height is less than zero.")
        if total_height > 20000:
            print("height needs to be decreased for scrolling:", total_height)
            total_height = 20000
            print("height reduced!", total_height)
        random_integers = random.sample(range(1, total_height + 1), NUMBER_OF_PAUSES)
        move_mouse_randomly(random.randint(0, NUM_MOUSE_MOVES))
        for i in range(1, total_height, 2):
            driver.execute_script("window.scrollTo(0, {});".format(i))
            if i in random_integers:
                move_mouse_randomly(random.randint(0, NUM_MOUSE_MOVES))
                time.sleep(random.randint(RANDOM_SLEEP_MIN, RANDOM_SLEEP_MAX))
        time.sleep(2)
        try:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
            time.sleep(3)
        except Exception as e:
            print("error areaaaaaa 3 ", e)
    except Exception as e:
        print("Couldn't scroll for website", website, "and error is", e)
        # 'Sample larger than population or is negative' means the 'total_height' is negative


    # SCREENSHOT - AFTER!
    # ss_object = FullPageScreenshotCollector(profile, ssafter_filepath, screenshotafter_path)
    # ss_object.captureFullScreenshot(driver)
    # driver.maximize_window()

    # # ALTERNATE CODE FOR SCREENSHOT
    # # Take full-page screenshot of the webpage
    # width = 1920 # HAVE TO SPECIFY WIDTH??
    # try:
    #     height = driver.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight,document.documentElement.clientHeight,document.documentElement.scrollHeight,document.documentElement.offsetHeight);")
    #     driver.set_window_size(width, height)
    #     time.sleep(5)
    #     page_body = driver.find_element(By.TAG_NAME, "body")
    #     # screenshot_output_path = "SS" + str(websiteCounter) + ".png"
    #     page_body.screenshot(ss_filepath)
    # except Exception as e:
    #     print("Screenshot did not take place for website", website, "and error is", e)
    # driver.maximize_window()


    # ADS COLLECTION!
    f = open(os.path.join(ROOT_DIRECTORY, "EasyList", "easylist.txt"), "r", encoding="utf-8")
    rules = f.read().split("\n")
    f.close()
    rules = [rule[2:] for rule in rules[18:] if rule.startswith("##")]
    
    spoofLogger = open(os.path.join(ROOT_DIRECTORY, "spoofLogs.txt"), "w")
    spoofLogger.write("Spoofing Through Life")
    EASYLIST_DIR = os.path.join(ROOT_DIRECTORY, "EasyList")
    try:
        ad_object = AdCollector(profile, 69, websiteDomain, 69, rules, ad_path, EASYLIST_DIR, spoofLogger)
        ad_object.collectAds(driver)
        print("Ad collection complete!")
        print()
    except:
        print("Problem in Ad Collection for Website:", website)
        print()



    # BIDS COLLECTION!
    bid_collector = BidCollector(profile, website, bid_filepath)
    bid_collector.collectBids(driver)


    # HAR COLLECTION!
    try:
        with open(har_filepath, 'w') as fhar:
            json.dump(proxy.har, fhar, indent=4)
            print("HAR file collected and stored!")
            print()
    except Exception as e:
        print("HAR file did not save for website", website, "and error is", e)
        print()
    
    try:
        fhar.close()
    except Exception as e:
        print("fhar did not close for website", website, "and error is", e)



    # MOATSUPERV26 - ATTEMPT2!
    json_file = ""
    try:
        json_file = driver.execute_script("""
	var JSON_data = MoatSuperV26.jsonp
	JSON_data = JSON.stringify(JSON_data)
	return JSON_data
	""")
        
        if json_file != "":
            
            json_data = json.loads(json_file)

            # Writing JSON data to a file with indentation
            try:
                with open(moat_filepath, 'w') as json_fileobj:
                    json.dump(json_data, json_fileobj, indent=4)

                print("JSON data has been successfully written to 'data.json' file.")
                print()
            except Exception as e:
                print("An error occurred when writing json into the system", e)
                print()

    except Exception as e:
        print("error for website collecting MOATSUPERV26 ", website)
        print()



    print()

        

if "__main__" == __name__:

    print("IT STARTS!")

    excelWebsites = pd.read_excel("WebsitesDataset.xlsx")
    selected_column = excelWebsites['Websites']
    # selected_column = selected_column.head(30)
    selected_column = selected_column.iloc[87:95]
    websites = pd.DataFrame({'Websites': selected_column})


    # # Reading the Excel file 'Brands' to select the 'Company' and 'Website' columns
    # excelBrands = pd.read_excel("BRANDS.xlsx")
    # selected_companies = excelBrands['Company'].head(NUMBER_OF_WEBSITES)
    # selected_websites = excelBrands['Website'].head(NUMBER_OF_WEBSITES)
    # brands = pd.DataFrame({'Brand': selected_companies, 'Website': selected_websites})
    # print(websites)
    # print(brands)


    # IMP!!
    websiteCounter = 0


    # # Create a directory for the Data Collected!
    # data_collected_dir_treatment = os.path.join(os.getcwd(), 'Treatment Data Collected')
    # os.makedirs(data_collected_dir_treatment, exist_ok=True)

    # data_collected_dir_controlled = os.path.join(os.getcwd(), 'Controlled Data Collected')
    # os.makedirs(data_collected_dir_controlled, exist_ok=True)

    new_data_collected_dir = os.path.join(os.getcwd(), 'Websites Testing - Data Collected')
    os.makedirs(new_data_collected_dir, exist_ok=True)


    while True:

        if websiteCounter >= 54:
            print("WE ARE DONE WITH THE WEBSITES")
            break

        # Setup VPN
        if random.random() < 0.4:

            print("\nWE DOIN IT!!!")

            flagVPN = 0
            try:
                os.system('cd NordVPN && nordvpn --disconnect && cd ..')
                time.sleep(13)
                print("disconnection successful :D")
            except:
                print("VPN could not be disconnected!")

            while flagVPN == 0:
                try:
                    os.system('cd NordVPN && nordvpn -c -g "United States" && cd ..')
                    time.sleep(20)
                    flagVPN = 1
                    print("VPN is connected! baby!!\n")
                except:
                    print("VPN could not be connected!!! Try again connecting")

        # Safety termination!
        killBrowserMobProxyInstances(PORT)
        killChromeInstances()



        # CONTROLLED PHASE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        serverControlled, proxyControlled, chrome_options = configureProxy(PORT)
        driverControlled = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driverControlled.set_page_load_timeout(60)
        # Comment this for headless!!!
        driverControlled.maximize_window()
        print()
        print("CONTROLLED DRIVER INITIALISED!!!!!!!!!!!!!!!!!!")
        print()
        

        for idx1 in range(WEBSITES_PER_PERSONA):

            brand = "something"

            website = websites.iloc[websiteCounter]['Websites']
            websiteDomain = websites.iloc[websiteCounter]['Websites']

            # Create a folder for the website
            website_dir = os.path.join(new_data_collected_dir, website)
            os.makedirs(website_dir, exist_ok=True)

            print(f"Website: {website}")

            
            if not validators.url():
                website = "http://" + website
            websiteCounter = websiteCounter + 1


            # DATA COLLECTION!!
            dataCollection(website_dir, brand, website, websiteDomain, driverControlled, proxyControlled)


        # KILLING DRIVER AND PROXY INSTANCES
        closeProxyServer(proxyControlled, serverControlled)
        driverControlled.quit()
        killBrowserMobProxyInstances(PORT)
        killChromeInstances()

    print("EXITED WHILE LOOP!")
