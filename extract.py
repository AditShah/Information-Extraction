import sys
import urllib
from bs4 import BeautifulSoup
from selenium import webdriver
from urlparse import urljoin
from urlparse import urlparse
import requests
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from time import sleep
import re
import spacy
import os
import traceback
import en_core_web_sm


#Some initialization
cityThreshold = 30
keyWordThreshold = 100
MAX_TAB = 10
CLEAR_CACHE_TIMEOUT = 20
PAGE_LOAD_TIMEOUT = 25
CACHE_CONSTANT = 10
LOAD_TIME = 20

nlp = en_core_web_sm.load()              #Used to differentiate words
reload(sys)  
sys.setdefaultencoding('utf-8')

#store states & cities of India
states = set()
cities = set()

with open("statesOfIndia") as stateFile:
    for line in stateFile:
        states.add(line.strip().lower())
with open("citiesOfIndia") as cityFile:
    for line in cityFile:
        cities.add(line.strip().lower())

addressFile = open("./info/address","w+")
citiesFile = open("./info/city","w+")
statesFile = open("./info/state","w+")
phoneFile = open("./info/phone","w+")

#pincode regex
pincode = re.compile(r"\D(\d{3}[-\s*]?\d{3})\D")
#contactno regex
phno = re.compile(r"(0?(9\s*[-\s*\(\)+]?\s*)?(1\s*[-\s*\(\)+]?\s*)?\d\s*[-\s*\(\)+]?\s*\d\s*[-\s*\(\)+]?\s*\d\s*[-\s*\(\)+]?\s*\d\s*[-\s*\(\)+]?\s*\d\s*[-\s*\(\)+]?\s*\d\s*[-\s*\(\)+]?\s*\d\s*[-\s*\(\)+]?\s*\d\s*[-\s*\(\)+]?\s*\d\s*[-\s*\(\)+]?\s*\d)")




def checkValidity(pageContent, kew_word, start, end):
    
    #to prevent decoding error because utf-8 character can use upto 6 bytes
    for i in range(0, 7):
        try:
            start = max(0, start - i)
            end = min(len(pageContent), end + i)
            doc = nlp(pageContent[start:end].decode('utf-8'))
            break
        except:
            pass
    
    
    for token in doc:
        for keyWord in kew_word:
            if keyWord in token.text.lower():
                return True, token.idx + start
    
    return False, 0




#find Address from content, if found differentiate address, pincode, state, city else return False
def findAddr(pageContent, website):
    #starting kew words to check validity of address
    kew_word = ['institute', 'address', 'university', 'campus', 'college', 'reach', 'post', 'contact', 'question', 'query', 'recept', 'technology']
    
    
    stateFound = False
    cityFound = False
    addressFound = False
    
    for match in pincode.finditer(pageContent):
        #removing first and last char of matching
        possiblePin = match.group()[1:-1]
        
        #Will search city or state between start and end
        #to prevent decoding error because utf-8 character can use upto 6 bytes
        for i in range(0, 7):
            start = max(0, match.start() - cityThreshold - i)
            end = min(len(pageContent), match.end() + cityThreshold + i)
            try:
                doc = nlp(pageContent[start:end].decode('utf-8'))
                break
            except:
                pass
        
        #extracting tokens
        tokenList = []
        for token in doc:
            tokenList.append(token)
        
        
        #searching city / states from last
        for token in reversed(tokenList):
            #some of the words can be seperated by -
            for word in token.text.split('-'):
                if not stateFound and word.lower() in states:
                    stateFound, index = checkValidity(pageContent, kew_word, token.idx - keyWordThreshold + start, token.idx + start)
                    if stateFound:
                        if not addressFound:
                            addressFile.write(website + "\n")
                            doc = nlp(pageContent[index:token.idx + start + len(word) + 1].decode('utf-8'))
                            address=""
                            for tok in doc:
                                address+=tok.text
                            address=re.sub("\s\s+"," ",address)
                            address=re.sub("\n\n+","\n",address)
                            addressFile.write(address)
                            addressFile.write("\n\n\n")
                        addressFound = True
                        statesFile.write(website + "\n" + word + "\n\n")
                if not cityFound and word.lower() in cities:
                    cityFound, index = checkValidity(pageContent, kew_word, token.idx - keyWordThreshold + start, token.idx + start)
                    if cityFound:
                        if not addressFound:
                            addressFile.write(website + "\n")
                            doc = nlp(pageContent[index:token.idx + start + len(word) + 1].decode('utf-8'))
                            address=""
                            for tok in doc:
                                address+=tok.text
                            address=re.sub("\s\s+"," ",address)
                            address=re.sub("\n\n+","\n",address)
                            addressFile.write(address)
                            addressFile.write("\n\n\n")
                        addressFound = True
                        if word.strip().lower() == "india":
                            cityFound = False
                        else:
                            citiesFile.write(website + "\n" + word + "\n\n")
    citiesFile.flush()
    addressFile.flush()
    statesFile.flush()
    return addressFound





#find contactno from content, if found differentiate it else return False
def findPhoneNo(pageContent, website):
    kew_word = ['contact', 'ph', 'phone', 'no', 'number', 'enquiry', 'inquiry', 'cell', 'reach', 'question', 'query', 'recept', 'technology']
    
    phnoFound = False
    
    for match in phno.finditer(pageContent):
        possiblePhno = match.group()
        
        phnoFound, index = checkValidity(pageContent, kew_word, match.start() - keyWordThreshold, match.start())
        
        if phnoFound:
            phoneFile.write(website + "\n" + possiblePhno + "\n\n")
            phoneFile.flush()
            return phnoFound;
        
        
    return phnoFound


options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1200x600')
browser = webdriver.Chrome("chromedriver", options = options)
browser.set_page_load_timeout(PAGE_LOAD_TIMEOUT)

def close_browser(driver):
    try:
        while len(driver.window_handles) > 0:
            driver.switch_to_window(driver.window_handles[0])
            driver.close()
    
    except Exception as ex:
        browser = webdriver.Chrome("chromedriver", options = options)
        browser.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    
    return browser


websites = []
notFound=[]
with open("contactPages") as urlList:
    cur = []
    for line in urlList:
        if line.strip() == "$$$$$$":
            if(len(cur)>0):
                websites.append(cur)
            cur=[]
        else:
            cur.append(line.strip())
if(len(cur)>0):
    websites.append(cur)


i=0
while i < len(websites):
    print len(notFound)
    try:
        if i%CACHE_CONSTANT is 0:
            browser = close_browser(browser)
            sys.stderr.write("cache cleared\n")
        browser.switch_to_window(browser.window_handles[0])
        for j in range(i,min(MAX_TAB+i,len(websites))):
            website = websites[j][0]
            stri = "window.open('" + website + "');"
            browser.execute_script(stri)
            sys.stderr.write(website + " " + str(j) + "\n")
            
        sleep(LOAD_TIME)
        notFoundAddr = []
        notFoundPhone = []
        
        for j in range(i,min(MAX_TAB+i,len(websites))):
            website = websites[j][0] 
            browser.switch_to_window(browser.window_handles[-1])
            try:
                soup = BeautifulSoup(browser.page_source, "lxml")
            except Exception as ex:
                notFoundAddr.append(j)
                browser.close()
                continue

            # kill all script and style elements
            for script in soup(["script", "style"]):
                script.extract()    # rip it out

            # get text
            pageContent = soup.get_text()
            lines = (line.strip() for line in pageContent.splitlines())
            # break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            
            #find & differentiate address, pincode, state, city
            if not findAddr(pageContent, website):
                notFoundAddr.append(j)

            #find & differentiate contactno
            if not findPhoneNo(pageContent, website):
                notFoundPhone.append(j)
            
            browser.close()
        
        
        for ind in notFoundAddr:
            found=0
            for website in websites[ind]:
                browser.switch_to_window(browser.window_handles[0])
                stri = "window.open('" + website + "');"
                browser.execute_script(stri)
                sys.stderr.write(website + " " + str(j))
                browser.switch_to_window(browser.window_handles[-1])
                try:
                    soup = BeautifulSoup(browser.page_source, "lxml")
                except Exception as ex:
                    browser.close()
                    print "ano"
                    continue

                # kill all script and style elements
                for script in soup(["script", "style"]):
                    script.extract()    # rip it out

                # get text
                pageContent = soup.get_text()
                lines = (line.strip() for line in pageContent.splitlines())
                
                # break multi-headlines into a line each
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                
                #find & differentiate address, pincode, state, city
                if not findAddr(pageContent, website):
                    print "ano"
                    pass
                else:
                    print "ayes"
                    browser.close()
                    found=1
                    break
                browser.close()
            if found is 0:
                notFound.append(website)
                
                
        for ind in notFoundPhone:
            found=0
            for website in websites[ind]:
                browser.switch_to_window(browser.window_handles[0])
                stri = "window.open('" + website + "');"
                browser.execute_script(stri)
                sys.stderr.write(website + " " + str(j) + "\n")
                browser.switch_to_window(browser.window_handles[-1])
                try:
                    soup = BeautifulSoup(browser.page_source, "lxml")
                except Exception as ex:
                    print "pno"
                    browser.close()
                    continue

                # kill all script and style elements
                for script in soup(["script", "style"]):
                    script.extract()    # rip it out

                # get text
                pageContent = soup.get_text()
                lines = (line.strip() for line in pageContent.splitlines())
                
                # break multi-headlines into a line each
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                
                #find & differentiate address, pincode, state, city
                if not findPhoneNo(pageContent, website):
                    pass
                    print "pno"
                else:
                    found=1
                    browser.close()
                    print "pyes"
                    break
                browser.close()
                
    except Exception as ex:
        traceback.print_exc()
        sys.stderr.write("Exception occured\n")
        browser = close_browser(browser)
        
    i+=MAX_TAB

print "not Founded"
for web in notFound:
    print web
    
print len(notFound)