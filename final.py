#!/usr/bin/python
# -*- coding: utf-8 -*-

import spacy
import re
import os, sys

#Some initialization
cityThreshold = 30
keyWordThreshold = 100
nlp = spacy.load('en')              #Used to differentiate words
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

textFile = re.compile(r"(.txt$)")
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
def findAddr(pageContent):
    #starting kew words to check validity of address
    kew_word = ['institute', 'address', 'university', 'campus', 'college', 'reach', 'post', 'contact']
    
    
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
                            doc = nlp(pageContent[index:token.idx + start + len(word) + 1].decode('utf-8'))
                            print "Address: "
                            for tok in doc:
                                print tok,
                            print "\n"
                        addressFound = True
                        print "state: ", word
                if not cityFound and word.lower() in cities:
                    cityFound, index = checkValidity(pageContent, kew_word, token.idx - keyWordThreshold + start, token.idx + start)
                    if cityFound:
                        if not addressFound:
                            doc = nlp(pageContent[index:token.idx + start + len(word) + 1].decode('utf-8'))
                            print "Address: "
                            for tok in doc:
                                print tok,
                            print "\n"
                        addressFound = True
                        if word.strip().lower() == "india":
                            cityFound = False
                        else:
                            print "city: ", word
        
    return addressFound





#find contactno from content, if found differentiate it else return False
def findPhoneNo(pageContent):
    kew_word = ['contact', 'ph', 'phone', 'no', 'number', 'enquiry', 'inquiry', 'cell', 'reach']
    
    phnoFound = False
    
    for match in phno.finditer(pageContent):
        possiblePhno = match.group()
        
        phnoFound, index = checkValidity(pageContent, kew_word, match.start() - keyWordThreshold, match.start())
        
        if phnoFound:
            print "phone: ", possiblePhno
            return phnoFound;
        
        
    return phnoFound




c=0

#for each contact page
for fname in os.listdir('./parsed'):
    isTextFile = textFile.search(fname)
    if isTextFile:
        print fname
        
        #getting page content from file
        pageContent = ""
        with open('./parsed/'+fname) as content:
            for line in content:
                pageContent = pageContent + line
        
        #find & differentiate address, pincode, state, city
        if not findAddr(pageContent):
            c+=1
            print "cannot find address"
        #find & differentiate contactno
        if not findPhoneNo(pageContent):
            print "cannot find contact no"
        
        
        print "\n\n\n"

print c
