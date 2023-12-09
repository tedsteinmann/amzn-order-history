#
# dl_orders.py
#
# Download all of your Amazon order history to CSV files.
# 
# Requirements:
# - Mac (tested on Monterey 12.6.3)
# - Chrome
#  
# Outputs:
# - orders.csv - Order history
# - items.csv  - Items ordered
#

browserProfile='Default2'
accountName='personal'
latestYear = 2023
oldestYear = 2022
crawlOrderHistory = False
downloadInvoicePages = False
scrapeInvoicePages = False
verbose = False

import os
import time
import math
import random
import re
import glob
import json
import csv

from contextlib import contextmanager

import urllib
import urllib.request
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

def vprint(*msg):
    if verbose:
        print(*msg)

# wait a bit, to be nice to the site
def waitABit(baseSecs = 0.55):
   waitSecs = baseSecs + random.random() * (0.5 * baseSecs)
   vprint('        waiting ' + str(waitSecs) + ' secs')
   time.sleep(waitSecs)

# go down/up one dir level
def pushDir(dirName):
    if not os.path.exists(dirName):
       os.mkdir(dirName)
    os.chdir(dirName)

def popDir():
   os.chdir('..')

def jsonFileExists(basename):
    return os.path.exists(basename+'.json')

def writeToJsonFile(basename, strList):
    filename = basename+'.json'
    vprint('INFO: writing '+filename+'...\n', strList)
    with open(filename, 'w') as jsonFile:
        json.dump(strList, jsonFile, indent=4)

def readFromJsonFile(basename):
    filename = basename+'.json'
    vprint('INFO: reading '+filename+'...')
    strList = []
    with open(filename, 'r') as jsonFile:
        strList = json.load(jsonFile)
    return strList

def getWebPage(url, scrollToEnd=False):
    vprint('INFO: getting page',url,'...')

    if not getWebPage.browserRunning:
        getWebPage.browserStartup()
    
    success = True
    html = ''
    try:
        getWebPage.browser.get(url)
        if scrollToEnd:
            getWebPage.browser.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            time.sleep(5)
    except error:
        vprint('    ERROR: browser.get("%s,%s")'%url,error)
        success = False
        getWebPage.browserShutdown()

    if success:
        html = getWebPage.browser.page_source

    return BeautifulSoup(html, features="html.parser"), success

def browserStartup():
    options = webdriver.ChromeOptions()
    options.add_argument("--user-data-dir="+os.path.expanduser('~')+"/Library/Application Support/Google/Chrome/")
    options.add_argument('--browserProfile-directory='+'"'+browserProfile+'"')
    options.add_experimental_option("excludeSwitches", ["test-type","enable-automation","enable-blink-features"])

    getWebPage.browser = webdriver.Chrome(options=options, service=ChromeService(ChromeDriverManager().install()))
    vprint(getWebPage.browser.capabilities)
    getWebPage.browserRunning = True    

def browserShutdown():
    if getWebPage.browser != None:
        getWebPage.browser.quit()
        getWebPage.browser = None
        getWebPage.browserRunning = False

def addToURLList(urlList, url):
    if not url in urlList:
        urlList.append(url)
        print('adding',url)
        return True
    else:
        return False

@contextmanager
def ignore(*exceptions):
  try:
    yield
  except exceptions:
    pass 

def getAmazonOrders():
    rootUrl = 'https://www.amazon.com'

    invoiceUrls = []
    detailsUrls = [] 
    digitalInvoiceUrls = []

    # Crawl order history pages for invoice and order detail URLs
    if crawlOrderHistory:
        for year in range(latestYear,oldestYear-1,-1):
            yearStr = str(year)
            pageNum = 1
            morePages = True
            numOrders = -1

            while morePages:
                morePages = False
                paginationStr = str(pageNum-1)+'_'+str(pageNum)
                url = rootUrl + '/gp/your-account/order-history/ref=ppx_yo_dt_b_pagination_'+paginationStr+'?ie=UTF8&orderFilter=year-'+yearStr+'&search=&startIndex='+str((pageNum - 1)*10)
                page, success = getWebPage(url)
                if page != None and success:

                    if pageNum == 1:
                        # <span class="num-orders">93 orders</span> placed in            
                        spans = page.findAll('span', {'class' : 'num-orders'})
                        if len(spans):
                            numOrders = int(spans[0].get_text().split(' ')[0])
                        vprint ("%d numOrders for %d"%(numOrders, year))

                    for tag in page.findAll('a'):
                        url = tag.get('href')
                        if url != None:
                            if '/gp/css/summary/print.html' in url: 
                                morePages = addToURLList(invoiceUrls, url)
                            elif '/gp/your-account/order-details' in url:
                                morePages = addToURLList(detailsUrls, url)
                            elif '/gp/digital/your-account/order-summary' in url:
                                morePages = addToURLList(digitalInvoiceUrls, url)

                if morePages:
                    pageNum += 1
                    waitABit(3)

            print('got %d invoices at year %d'%(len(invoiceUrls),year))
            print('got %d order details at year %d'%(len(detailsUrls),year))
            print('got %d digital invoices at year %d'%(len(digitalInvoiceUrls),year))

            writeToJsonFile('invoices', invoiceUrls)
            writeToJsonFile('order-details', detailsUrls)
            writeToJsonFile('digital-invoices', digitalInvoiceUrls)

    # Download all invoice pages
    if downloadInvoicePages:
        invoiceUrls = readFromJsonFile('invoices')
        # detailsUrls = readFromJsonFile('order-details')
        # digitalInvoiceUrls = readFromJsonFile('digital-invoices')

        # download all the invoices
        pushDir('orders')

        for url in invoiceUrls:
            orderID = url.split('orderID=')[1]
            localUrl = orderID + '.html'
            if not url.startswith(rootUrl):
                url = rootUrl + url
            print('downloading %s to %s'%(url,localUrl))

            page, success = getWebPage(url)
            if page != None and success:
                with open(localUrl, "w", encoding='utf-8') as file:
                    file.write(str(page))
                    vprint('  wrote file',localUrl)
            waitABit(3)
        
        popDir()

    # Scrape local invoice pages into order and item csv files
    if scrapeInvoicePages:

        orderFields = ['orderNumber','orderPlacedDate','orderTotal','orderSubtotal','orderShippingAndHandling','orderTotalPreTax','orderTax','orderGrandTotal','paymentMethod','creditCard']#,'creditCardChargeDate']
        itemFields = ['orderNumber','itemQuantity','itemDescription','itemSeller','itemCondition','itemPrice']

        with open('orders.csv', 'w', newline='', encoding="utf-8") as ordersFile:
            writer = csv.DictWriter(ordersFile, orderFields)
            writer.writeheader()

        with open('items.csv', 'w', newline='', encoding="utf-8") as itemsFile:
            writer = csv.DictWriter(itemsFile, itemFields)
            writer.writeheader()

        invoices = glob.glob("orders/*.html")
        vprint(invoices)
        for invoice in invoices:
            vprint('invoice',invoice)
            with open(invoice) as file:
                html = file.read()
            page = BeautifulSoup(html, "html.parser")

            # 
            # Order Placed: <date>
            # Amazon.com order number: <order>
            # Order Total <price>
            # Shipped on <date>
            # Items Ordered          Price
            # <one or more>
            #   <quantity> of: <description> <price>
            #   Sold by: <seller>
            #   Condition: <condition>
            # Shipping Address: <address>
            # Shipping Speed: <speed>
            # Payment Method: <method>
            # Billing address <address>
            # Item(s) Subtotal: <price>
            # Shipping & Handling: <price>
            # Total before tax: <price>
            # Estimated tax to be collected: <price>
            # Grand Total: <price>
            # Credit Card transactions <cc transaction: cc #: date: price>
            #

            #
            # Order
            #
            orderNumber = orderPlacedDate = orderTotal = orderSubtotal = orderShippingAndHandling = orderTotalPreTax = orderTax = orderGrandTotal = paymentMethod = creditCard = creditCardChargeDate = ''           
            with ignore(AttributeError):
                orderNumber = page.body.find(string=re.compile('Amazon.com order number:')).next_element.strip()
                orderPlacedDate = page.body.find(string=re.compile('Order Placed:')).next_element.strip()
                orderTotal = page.body.find(string=re.compile('Order Total')).parent.contents[0].split('$')[1]
                # TODO - handle billingAddress # vprint(page.body.find(string=re.compile('Billing address')).parent.next_element.next_element.next_element)
                orderSubtotal = page.body.find(string=re.compile('Item\(s\) Subtotal:')).next_element.next_element.contents[0].replace('$','')
                orderShippingAndHandling = page.body.find(string=re.compile('Shipping \& Handling:')).next_element.next_element.contents[0].replace('$','')
                orderTotalPreTax = page.body.find(string=re.compile('Total before tax:')).next_element.next_element.contents[0].replace('$','')
                orderTax = page.body.find(string=re.compile('Estimated tax to be collected:')).next_element.next_element.contents[0].replace('$','')
                orderGrandTotal = page.body.find(string=re.compile('Grand Total:')).next_element.next_element.contents[0].contents[0].replace('$','')
                # TODO - handle paymentMethods
                paymentMethod = page.body.find(string=re.compile('Payment Method:')).next_element.next_element.next_element.strip()
                creditCard = page.body.find(string=re.compile('ending in')).split(':')[0].strip()
                #creditCardChargeDate = page.body.find(string=re.compile('ending in')).split(':')[1].strip()
            orderRow = {'orderNumber':orderNumber, 'orderPlacedDate':orderPlacedDate, 'orderTotal':orderTotal, 'orderSubtotal':orderSubtotal, \
                        'orderShippingAndHandling':orderShippingAndHandling, 'orderTotalPreTax':orderTotalPreTax, 'orderTax':orderTax, 'orderGrandTotal':orderGrandTotal, \
                        'paymentMethod':paymentMethod,'creditCard':creditCard}#, 'creditCardChargeDate':creditCardChargeDate}

            with open('orders.csv', 'a', newline='', encoding="utf-8") as ordersFile:
                writer = csv.DictWriter(ordersFile, orderFields)
                writer.writerow(orderRow)

            print('appended order %s to %s'%(orderNumber, os.getcwd()+'/orders.csv'))
            vprint(orderRow)


            #
            # Items
            #

            # TODO - handle shippingDates
            # shippingDate = page.body.find(string=re.compile('Shipped on')).parent.contents[0].split('Shipped on')[1].strip()
            # vprint('Shipped on:', shippingDate)

            itemRows = []
            itemQuantitiesRaw = page.body.find_all(string=re.compile('of:'))
            itemDescriptionsRaw = page.body.find_all(string=re.compile('of:'))
            itemSellersRaw = page.body.find_all(string=re.compile('Sold by:'))
            itemConditionsRaw = page.body.find_all(string=re.compile('Condition:'))
            itemPricesRaw = page.body.find_all(string=re.compile('Condition:'))
            itemCount = max([len(itemQuantitiesRaw),len(itemDescriptionsRaw),len(itemSellersRaw),len(itemConditionsRaw),len(itemPricesRaw)])

            for i in range(0, itemCount):
                itemRows.append({'orderNumber':orderNumber})           

            for itemNum, itemQuantity in enumerate(itemQuantitiesRaw):
                with ignore(AttributeError):
                    itemQuantity = itemQuantity.split('of:')[0].strip()
                itemRows[itemNum]['itemQuantity'] = itemQuantity

            for itemNum, itemDescription in enumerate(itemDescriptionsRaw):
                with ignore(AttributeError):
                    itemDescription = itemDescription.next_element.contents[0]
                itemRows[itemNum]['itemDescription'] = itemDescription

            for itemNum, itemSeller in enumerate(itemSellersRaw):
                with ignore(AttributeError):
                    itemSeller = itemSeller.split('Sold by:')[1].strip()
                    itemSeller = re.sub(' \($', '', itemSeller)               
                itemRows[itemNum]['itemSeller'] = itemSeller

            for itemNum, itemCondition in enumerate(itemConditionsRaw):
                with ignore(AttributeError):
                    itemCondition = itemCondition.split('Condition:')[1].strip()
                itemRows[itemNum]['itemCondition'] = itemCondition

            for itemNum, itemPrice in enumerate(itemPricesRaw):
                with ignore(AttributeError):
                    itemPrice = itemPrice.find_next(string=re.compile('\$')).strip().replace('$','')
                itemRows[itemNum]['itemPrice'] = itemPrice

            # TODO - handle shippingAddresses
            # for child in page.body.find(string=re.compile('Shipping Address:')).parent.parent.findChildren():
            #     vprint("->",child)
            #vprint(page.body.find(string=re.compile('Shipping Address:')).next_element.next_element.next_element.next_element)

            # TODO - handle shippingSpeeds
            #vprint(page.body.find(string=re.compile('Shipping Speed:')).next_element.next_element.next_element)

            with open('items.csv', 'a', newline='', encoding="utf-8") as itemsFile:
                writer = csv.DictWriter(itemsFile, itemFields)
                writer.writerows(itemRows)

            print('appended %d items from order %s to %s'%(itemCount, orderNumber, os.getcwd()+'/items.csv'))
            vprint(orderRow)


def loginToAmazon():
    page, success = getWebPage('https://www.amazon.com/gp/css/order-history?ref_=nav_orders_first')
    input("Login to Amazon then press Enter here (in the terminal) to continue...")

########################################################################################################################
# main
#
if crawlOrderHistory or downloadInvoicePages:
    browserStartup()
    loginToAmazon()

pushDir(accountName)
getAmazonOrders()
popDir()

if crawlOrderHistory or downloadInvoicePages:
    browserShutdown()

vprint('\ndone!')