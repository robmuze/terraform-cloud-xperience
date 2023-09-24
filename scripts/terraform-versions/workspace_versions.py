#!/usr/bin/env python3


import requests
import json
import sys
import getpass
import pandas as pd

print(
    """
Terraform Cloud workspace versions script.
 
Fetch All Terraform Cloud workspaces, and their versions using the Terraform Cloud API, create a CSV file

TFC_ORG: Name of your Terraform Cloud organization
TFC_TOKEN: Terraform Cloud Team token, for a team with permission to read workspace details

"""
)


# Org name & Token/Password input in a terminal
try:
    TFC_TOKEN = getpass.getpass(prompt="Enter Terraform Cloud API Token: ", stream=None)
    if TFC_TOKEN == "":
        print("Missing Terraform Cloud API token")
        sys.exit()

    TFC_ORG = input("Enter Terraform Cloud Organization Name: ")
    if TFC_ORG == "":
        print("Missing Terraform Cloud Organization name")
        sys.exit()
except Exception as e:
    print(e)

# HTTP Request Headers
requestHeaders = {
    "Authorization": "Bearer %s" % TFC_TOKEN,
    "Content-Type": "application/json",
}

# TFC EndPoint
URL = f"https://app.terraform.io/api/v2/organizations/{TFC_ORG}/workspaces?page=100"

# Init Mushed JSON List
merged_set = []


# Merge JSON objects
def merge_main_request():
    getRequest = requests.get(URL, headers=requestHeaders)
    rawJsonData = getRequest.json()
    for workspaces in rawJsonData["data"]:
        merged_set.append(workspaces)
    while rawJsonData["links"]["first"] != rawJsonData["links"]["last"]:
        if (rawJsonData["links"]["next"]) == None:
            break
        else:
            nextPage = requests.get(
                rawJsonData["links"]["next"], headers=requestHeaders
            )
            rawJsonData = nextPage.json()
            for workspaces in rawJsonData["data"]:
                merged_set.append(workspaces)
    return merged_set


# Get WorkSpaces with saved state
def saved_states():
    states_list = []
    # Inspect data from request and response
    for pg in merge_main_request():
        if (pg["relationships"]["current-state-version"]["data"]) is None:
            # Ignore workspaces currently with no states saved
            continue
        else:
            # Sends a GET Request
            SGR = requests.get(
                "https://app.terraform.io"
                + pg["relationships"]["current-state-version"]["links"]["related"],
                headers=requestHeaders,
            ).json()
            char = {
                "NameSpace": pg["attributes"]["name"],
                "StateVersion": SGR["data"]["attributes"]["terraform-version"],
                "TerraformVersion": pg["attributes"]["terraform-version"],
            }
            states_list.append(char)
    return states_list


# Load saved_states into a Pandas DataFrame
workspacesData = pd.DataFrame(saved_states())

# Load Pandas DataFrame into a CSV file
workspacesData.to_csv("%s_workspaces_versions.csv" % TFC_ORG, index=False)
