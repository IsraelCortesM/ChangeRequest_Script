#!/usr/bin/env python
import requests                                 #export necessary libraries for the code
import json, xmljson
import ssl
from time import sleep
import datetime
import time
import calendar
from datetime import date
from requests.exceptions import HTTPError
from requests.exceptions import Timeout
import lxml 
from lxml.etree import fromstring, tostring
from xmljson import parker, Parker
import logging
import os
import sys


class CustomFormatter(logging.Formatter):               #Define colors for outputs in terminal or logs using logging function

    green = "\x1b[32;21m"
    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
  
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)


                                            
def tiemzone_setup():                                       # TimeZone UTC default (Mexico)
    if time.daylight:
        local_timezone_name = time.tzname[0]
        utc_offset = time.timezone
    else:
        local_timezone_name = time.tzname[1]
        utc_offset = time.altzone
    global today
    today = date.today()

def ssl_verify():
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        # Legacy Python that doesn't verify HTTPS certificates by default
        pass
    else:     # Handle target environment that doesn't support HTTPS verification
        ssl._create_default_https_context = _create_unverified_https_context

                                               
                                                
def get_vars(var_file):                                                                                 #Definition of variables as global for using in all functions
    global cr, user, password, gsd_token_url, gsd_url, cis_url, data_token, data_request
    cr = os.environ['CHANGE_REQUEST']
    
    with open(var_file,'r') as json_file:
        data = json.load(json_file)

     
    user = data['gsd_user'] 
    password = data['gsd_password']
    gsd_token_url = data['gsd_token_url']
    gsd_url = data['gsd_url']
    cis_url = data['cis_url']
    

    data_token= {
    "username": user,
    "password": password,
    "grant_type": "password",
    "client_id": "gsd-client",
    "client_secret": "gsd-secret"
    }

    data_request= f"""
                    <ChangeInquiryRequest action="InquiryRequest" function="ChangeInquiry" genDateTZ="0" version="5.0" xmlns="your url">
                        <ApplicationID>{user}</ApplicationID>
                        <ChangeInquiryRequestDetail>
                            <ReferenceNumber>{cr}</ReferenceNumber>
                        </ChangeInquiryRequestDetail>
                    </ChangeInquiryRequest>"""

    


def gsd_request():                          #GSD Validation (Here we get the requests to the API)
    
    try:
        global gsd_access_token
        headers = {                                                # Token Generator for OAuth2
            "Content-Type": "application/x-www-form-urlencoded"
            }
        gsd_access_token = requests.post(gsd_token_url, verify=False, headers=headers, data=data_token, timeout=60
                            ).json()
        print(gsd_access_token)

        headers = {
            "Content-Type": "application/xml",
            "gsd_acces_token": gsd_access_token['acces_token']
        }
        
        response = requests.post(gsd_url, verify=False, headers=headers, data=data_request, timeout=60
                                 ).json()
        
        if response.status_code == 200:
                
            json_cr = json.dumps(parker.data(fromstring(response.content)), indent = 4)                     #Transformation of XML to JSON format useful to easier manipulation in Python
            #print(json_cr)                     #(Optional) Printed response in json format 
            cr_details = json.loads(json_cr)
                                                                    # Keys transformation to python dict
            cr_details = {key.replace('{your url}', 'CR'): cr_details.pop(key) for key in list(cr_details)}
                
            global cr_response, cr_status, cr_id, cr_opendate, cr_group, cr_startdate, cr_enddate, cr_owner, ci_name_1, ci_class_1, ci_name_2, ci_class_2, ci_name_3, ci_class_3
            cr_response = cr_details["CRChangeInquiryResponseDetail"]["Response"] = cr_details["CRChangeInquiryResponseDetail"].pop("{your rest API URL}ReplyText")
            
            if cr_response == "Request processed Successfully.":

                cr_status = cr_details["CRChangeInquiryResponseDetail"]["Status"] = cr_details["CRChangeInquiryResponseDetail"].pop("{your rest API URL}Status") 
                cr_id = cr_details["CRChangeInquiryResponseDetail"]["ReferenceNumber"] = cr_details["CRChangeInquiryResponseDetail"].pop("{your rest API URL}ReferenceNumber")
                cr_opendate = cr_details["CRChangeInquiryResponseDetail"]["OpenDate"] = cr_details["CRChangeInquiryResponseDetail"].pop("{your rest API URL}OpenDate")
                cr_group = cr_details["CRChangeInquiryResponseDetail"]["OwningGroup"] = cr_details["CRChangeInquiryResponseDetail"].pop("{your rest API URL}OwningGroup")
                cr_startdate = cr_details["CRChangeInquiryResponseDetail"]["StartDate"] = cr_details["CRChangeInquiryResponseDetail"].pop("{your rest API URL}ScheduledStartDate")
                cr_enddate = cr_details["CRChangeInquiryResponseDetail"]["EndDate"] = cr_details["CRChangeInquiryResponseDetail"].pop("{your rest API URL}ScheduledEndDate")
                cr_owner = cr_details["CRChangeInquiryResponseDetail"]["Owner"] = cr_details["CRChangeInquiryResponseDetail"].pop("{your rest API URL}ChangeOwner")
                ci_name_1 = cr_details["CRChangeInquiryResponseDetail"]["{your rest API URL}CIs"]["{your rest API URL}CI"][0]["{your rest API URL}CIName"]
                ci_class_1 = cr_details["CRChangeInquiryResponseDetail"]["{your rest API URL}CIs"]["{your rest API URL}CI"][0]["{your rest API URL}CIClass"]
                ci_name_2 = cr_details["CRChangeInquiryResponseDetail"]["{your rest API URL}CIs"]["{your rest API URL}CI"][1]["{your rest API URL}CIName"]
                ci_class_2 = cr_details["CRChangeInquiryResponseDetail"]["{your rest API URL}CIs"]["{your rest API URL}CI"][1]["{your rest API URL}CIClass"]
                
                try:

                    ci_name_3 = True
                    ci_name_3 = cr_details["CRChangeInquiryResponseDetail"]["{your rest API URL}CIs"]["{your rest API URL}CI"][2]["{your rest API URL}CIName"]
                    ci_class_3 = cr_details["CRChangeInquiryResponseDetail"]["{your rest API URL}CIs"]["{your rest API URL}CI"][2]["{your rest API URL}CIClass"]
                except IndexError:
                    logging.debug("This CR only has two Direct CIs")
                    ci_name_3 = False

            else:
                logging.error("Request error, CR has not been found.  " + cr_response)
                raise Exception ("Request error, CR has not been found.", cr_response)
        else:
            logging.error("Request failed, please verify data or try again." + response.status_code)
            raise Exception ("Request failed, please verify data or try again. Status code: ", response.status_code)
            
                
        #with open("cr_details.json", "w") as outfile:                  //If want to download .json file in local
        #   json.dump(json_cr, outfile, indent = 4)
            #f = open('cr_details.json',) 
          
    except Timeout:
        logging.error("Time for request has expired. Please try again.")
        raise Exception("Time for request has expired. Please try again.")
    except HTTPError as http_err:
        logging.error("HTTP Error", http_err)
        raise Exception("HTTP Error", http_err)
#gsd_request()


def cis_request():
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().setLevel(logging.DEBUG)
    global response_3
    try: 
        
        data_cis_1= f"""
            <CIListRequest xmlns="your rest API URL" version="1.0" genDateTZ="0" function="CIList" action="InquiryRequest" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <ApplicationID>{user}</ApplicationID>
                <CIListRequestDetail>
                    <CIName>{ci_name_1}%</CIName>
                    <CIClass>{ci_class_1}</CIClass>
                </CIListRequestDetail>
            </CIListRequest>"""

        data_cis_2= f"""
            <CIListRequest xmlns="your rest API URL" version="1.0" genDateTZ="0" function="CIList" action="InquiryRequest" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                ApplicationID>{user}</ApplicationID>
                <CIListRequestDetail>
                    <CIName>{ci_name_2}%</CIName>
                    <CIClass>{ci_class_2}</CIClass>
                </CIListRequestDetail>
            </CIListRequest>"""
        
        if ci_name_3 == True:
            data_cis_3= f"""
                <CIListRequest xmlns="your rest API URL" version="1.0" genDateTZ="0" function="CIList" action="InquiryRequest" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <ApplicationID>{user}</ApplicationID>
                    <CIListRequestDetail>
                        <CIName>{ci_name_3}%</CIName>
                        <CIClass>{ci_class_3}</CIClass>
                    </CIListRequestDetail>
                </CIListRequest>"""

        headers = {                                                # Change Request - GSD Validation & Response
            "Content-Type":     "application/xml",
            "gsd_access_token": gsd_access_token['access_token']
        }

        response_1 = requests.post(cis_url, verify=False, headers=headers, data=data_cis_1, timeout=60
                                   )
        response_2 = requests.post(cis_url, verify=False, headers=headers, data=data_cis_2, timeout=60
                                   )
        
        if ci_name_3 == True:
            response_3 = requests.post(ics_url, verify=False, headers=headers, data=data_cis_3, timeout=60
                                   )


        if response_1.status_code == 200:
            try:
            
                json_cis_1 = json.dumps(parker.data(fromstring(response_1.content)), indent = 4)
                #print(json_cis_1)                     #(Optional) Printed response in json format 
                ci_details_1 = json.loads(json_cis_1)
                ci_details_1 = {key.replace('{your CIList API URL}CIListResponseDetail', 'CIListResponseDetail'): ci_details_1.pop(key) for key in list(ci_details_1)}
                
                global ci_purpose

                ci_status = ci_details_1["CIListResponseDetail"]["{your CIList API URL}CIList"]["{your CIList API URL}CIDetail"][1]["{your CIList API URL}Status"]
                ci_purpose = ci_details_1["CIListResponseDetail"]["{your CIList API URL}CIList"]["{your CIList API URL}CIDetail"][1]["{your CIList API URL}Purpose"]
                #print(ci_purpose)
                if ci_status == "Active":
                    logging.info("Status for this Change Order CIs is Active. Status: " + ci_status)
                else:
                    logging.error("This CIs are not active. Status: " + ci_status)
                    raise Exception("This CIs are not active")

                if ci_purpose == "Production" or "Contingency": 
                    logging.debug("CI Name is: " + ci_name_1)
                    logging.info("This CI is for Production purpose. Purpose: " + ci_purpose)
                else:
                    logging.error("This CI is not for Production purpose. Purpose: " + ci_purpose)
                    raise Exception("This CI is not for Production purpose")

            except KeyError:
                try:
                    json_cis_2 = json.dumps(parker.datq(fromstring(response_2.content)), indent=4)
                    #print(json_cis_2)           (OPTIONAL) Printed respon in JSON format
                    ci_details_2 = json.loads(json_cis_2)
                    ci_details_2 - {key.replace('{your CIList API URL}CIListResponse Detail', 'CIListResponseDetail'): ci_details_2.pop(key) for key in list(ci_details_2)}
                    

                    ci_status = ci_details_2["CIListResponseDetail"]["{your CIList API URL}CIList"]["{your CIList API URL}CIDetail"][1]["{your CIList API URL}Status"]
                    ci_purpose = ci_details_2["CIListResponseDetail"]["{your CIList API URL}CIList"]["{your CIList API URL}CIDetail"][1]["{your CIList API URL}Purpose"]
                    #print(ci_purpose)
                    if ci_status == "Active":
                        logging.info("Status for this Change Order CIs is Active. Status: " + ci_status)
                    else:
                        logging.error("This CIs are not active. Status: " + ci_status)
                        raise Exception("This CIs are not active")
                    if ci_purpose == "Production" or "Contingency": 
                        logging.debug("CI Name is: " + ci_name_2)
                        logging.info("This CI is for Production purpose. Purpose:" + ci_purpose)
                    else:
                        logging.error("This CI is not for Production purpose. Purpose:" + ci_purpose)
                        raise Exception("This CI is not for Production Purpose")
                except KeyError:
                    try:
                        if ci_name_3 == True:
                                        
                            json_cis_3 = json.dumps(parker.data(fromstring(response_3.content)), indent = 4)
                            #print(json_cis_3)                     #(Optional) Printed response in json format 
                            ci_details_3 = json.loads(json_cis_3)
                            ci_details_3 = {key.replace('{your CIList API URL}CIListResponseDetail', 'CIListResponseDetail'): ci_details_3.pop(key) for key in list(ci_details_3)}
                            ci_status = ci_details_3["CIListResponseDetail"]["{your CIList API URL}CIList"]["{your CIList API URL}CIDetail"][1]["{your CIList API URL}Status"]
                            ci_purpose = ci_details_3["CIListResponseDetail"]["{your CIList API URL}CIList"]["{your CIList API URL}CIDetail"][1]["{your CIList API URL}Purpose"]
                            #print(ci_purpose)
                            if ci_status == "Active":
                                logging.info("Status for this Change Order CIs is Active. Status: " + ci_status)
                            else:
                                logging.error("This CIs are not active. Status: " + ci_status)
                                raise Exception("This CIs are not active")
                            if ci_purpose == "Production" or "Contingeny": 
                                logging.debug("CI Name is: " + ci_name_3)
                                logging.info("This CI is for Production purpose. Purpose: " + ci_purpose)
                            else:
                                logging.error("This CI is not for Production purpose. Purpose: " + ci_purpose)
                                raise Exception("This CI is not for Production purpose")
                    except KeyError:
                        try:    
                            ci_status = ci_details_3["CIListResponseDetail"]["{your CIList API URL}CIList"]["{your CIList API URL}CIDetail"][1]["{your CIList API URL}Status"]
                            ci_purpose = ci_details_3["CIListResponseDetail"]["{your CIList API URL}CIList"]["{your CIList API URL}CIDetail"][1]["{your CIList API URL}Purpose"]
                            #print(ci_purpose)
                            if ci_status == "Active":
                                logging.info("Status for this Change Order CIs is Active. Status: " + ci_status)
                            else:
                                logging.error("This CIs are not active. Status: " + ci_status)
                                raise Exception("This CIs are not active")
                            if ci_purpose == "Production" or "Contingency": 
                                logging.debug("CI Name is: " + ci_name_3)
                                logging.info("This CI is for Production purpose. Purpose:" + ci_purpose)
                            else:
                                logging.error("This CI is not for Production purpose. Purpose:" + ci_purpose)
                                raise Exception("This CI is not for Production purpose")

                        except KeyError:
                            logging.error("This CR does not have Production CIs or Purpose")
                            raise Exception ("This CR does not have Production CIs or Purpose")


        else:
            logging.error("CIs Request error, please try again." + response_1.status_code)
            raise Exception("CIs Request error, please try again.")

    except Timeout:
        logging.error("Time for request has expired. Please try again.")
        raise Exception("Time for request has expired. Please try again.")
    except HTTPError as http_err:
        logging.error("HTTP Error", http_err)
        raise Exception("HTTP Error", http_err)
#cis_request()

def gsd_validation():
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("URL for OAuth2 authentication is: " + gsd_token_url)
    logging.debug("URL for Change Request validation is: " + gsd_url)
    logging.debug("URL for CIs List request is: " + cis_url)
    #logging.debug("User for this Change Request Validation is: " + user)
    
    logging.info(cr_response)                                                               # Inicio de validaciones del script
    if cr_id == cr:
        logging.debug("Change Request is correct: " + cr_id)
    else:
        logging.error("Change Request is incorrect, please verify it. CR is" + cr_id)
        raise Exception("Change Request is incorrect, please verify it")
    
        
    #logging.info ("The Change Request Owner is user: " + cr_owner)
    #logging.info("The Change Request Group is: " + cr_group)
        
    if cr_status == "Approved":
        logging.info("This Change Request has been approved . Status: " + cr_status)
    elif cr_status == "Closed":
        logging.error("This Change Request is Closed. Status: " + cr_status)
        raise Exception("This CR is Closed.")
    else:
        logging.error("This Change Request has not been approved yet. Status: " + cr_status)
        raise Exception("This Change Request has not been approved yet. Status: ", cr_status)

    


    today = date.today()
    today_epoch =  calendar.timegm(today.timetuple())
    cr_enddate_dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cr_enddate))
    cr_startdate_dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cr_startdate))

    logging.debug("The Start Date for this Change Request is: " + cr_startdate_dt)
    logging.debug("The End Date for this Change Request is: " + cr_enddate_dt)

    if today_epoch < cr_startdate:
        logging.error("This Change Request has not started verification yet.")
        raise Exception("This Change Request has not started verification")
    else:
        if today_epoch < cr_enddate:
            logging.info("This Change Request is on time.")
        else:
            
            logging.error("This Change Request time has expired, limit date was: " + cr_enddate_dt)
            raise Exception ("This Change Request time has expired, limit date was: ", cr_enddate_dt)
#gsd_validation()
    
    
def main(var_file):
    get_vars(var_file)
    gsd_request()
    cis_request()
    gsd_validation()

if __name__ == '__main__':
    var_file=sys.argv[1]
    main (var_file)
