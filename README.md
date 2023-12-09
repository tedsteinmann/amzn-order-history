# amzn-order-history
Download all of your Amazon order history to CSV files

## Requirements:
- Mac (tested on Monterey 12.6.3)
- Chrome

## Outputs:
- orders.csv - Order history
- items.csv  - Items ordered

## Getting started

Create a venv
`python3 -m venv venv`

Activate
`source vevn/bin/activate`

Install Requirements
`pip install -r requirements.txt`

Update primary variables
```
browserProfile='Default2'
accountName='personal'          # name of folder for storing downloaded content
latestYear = 2023               # start year
oldestYear = 2022               # end year
crawlOrderHistory = True        # get's order history for period, downloads it to .json file
downloadInvoicePages = False    # necessary for local processing from scrapwhether you should navigate to each individual invoiceprimary functionalitye
scrapeInvoicePages = False
verbose = False
```
Note that downloadInvoicePages is necessary for writing orders to csv in "scrapeInvoicePages" which takes place locally