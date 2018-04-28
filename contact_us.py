from selenium import webdriver
from bs4 import BeautifulSoup
from urlparse import urljoin
from urlparse import urlparse
import requests
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
import sys
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
import test
import traceback

CACHE_CONSTANT = 20
CLEAR_CACHE_TIMEOUT = 20 #seconds
LOAD_TIME = 20 #seconds
MAX_TAB = 10
PAGE_LOAD_TIMEOUT = 25 #seconds

   
#To run browser in background
options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1200x600')

browser = webdriver.Chrome("chromedriver", options = options)
browser.set_page_load_timeout(PAGE_LOAD_TIMEOUT)

#in has list of websites with each link in a new line
with open("in.txt") as urlList:
    websites = []
    for line in urlList:
        websites.append(line.strip())

contactNotFound = []
timeOut = []
contactPage = open("contactPages", "w+")

count = 0
i = 0

#add www. at the starting of url
def addWWW(link):
    link=link.replace("http://www.","http://")
    link=link.replace("https://www.","https://")
    link=link.replace("https://","https://www.")
    link=link.replace("http://","http://www.")
    return link

def close_browser():
    try:
        while len(browser.window_handles) > 0:
            browser.switch_to_window(browser.window_handles[0])
            browser.close()
    
    except Exception as ex:
        browser = webdriver.Chrome("chromedriver", options = options)
        browser.set_page_load_timeout(PAGE_LOAD_TIMEOUT)


while i < len(websites):
    try:
        #clear cache after every CACHE_CONSTANT websites
        if i%CACHE_CONSTANT is 0:
            close_browser()
            sys.stderr.write("cache cleared\n")
            
        sys.stdout.flush()
        sys.stderr.write(str(len(contactNotFound))+" "+str(len(timeOut))+"\n")
        browser.switch_to_window(browser.window_handles[0])
        
        #open MAX_TAB at once
        for j in range(i,min(MAX_TAB+i,len(websites))):
            website = websites[j]
            stri = "window.open('" + website + "');"
            browser.execute_script(stri)
            sys.stderr.write(website + " " + str(j) + "\n")
        
        #wait for all the tabs to load
        sleep(LOAD_TIME)
        for j in range(i,min(MAX_TAB+i,len(websites))):
            website = websites[j]
            
            foundContact = []
            browser.switch_to_window(browser.window_handles[-1])
            
            
            try:
                soup = BeautifulSoup(browser.page_source, "html.parser")
            except Exception as ex:
                timeOut.append(website)
                browser.close()
                continue
            
            #finding all links which has contact in it
            for link in soup.find_all('a'):
                if(len(foundContact)>5):
                    break
                if((link.string != None and link.string.lower().find("contact")!=-1) or (link.get('href')!=None and link.get('href').find('contact')!=-1)):
                    foundContact.append(urljoin(website, link.get('href')).strip())
            
            if len(foundContact) is 0:
                contactNotFound.append(website)
            
            foundContact.append(website)
            for link in foundContact:
                contactPage.write((addWWW(link).strip()) + "\n")
            contactPage.write("$$$$$$\n")
            browser.close()
            del foundContact[:]
    
    #if exception occurs close browser and start again
    except Exception, err:
        traceback.print_exc()
        sys.stderr.write("Exception occured")
        close_browser()
        
    i+=MAX_TAB