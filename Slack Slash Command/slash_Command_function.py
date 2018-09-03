import json
import os
import time
from base64 import b64decode
from datetime import datetime
from operator import itemgetter
from urllib.parse import parse_qsl

import boto3
from boto3.dynamodb.conditions import Attr, Key

# Connect to the Dynamo table to read the information from it
dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
table = dynamodb.Table('SupportAgentStatus')


def parse_input(data):
    parsed = parse_qsl(data, keep_blank_values=True)
    result = {}
    for item in parsed:
        result[item[0]] = item[1]
    return result

# Get the agents we want by filtering by routing profile
def getSuppAgents():
    supportReps = []
    tableResponse = table.scan()
    agents = tableResponse['Items']
    for item in agents:
        if (item['Routing Profile'].startswith("Supp-Class") or item['Routing Profile'] == "CAM Support - Volleymetrics"):
            supportReps.append(item)
        else:
            continue
    return supportReps

# Set our status counts to 0 for all possible values
def getStatusCount(list):
    availableCount = 0
    offlineCount = 0
    apprenticeCount = 0
    biweeklyCount = 0
    break_lunchCount = 0
    gbplusCount = 0
    maxprepsCount = 0
    interviewCount = 0
    meetingCount = 0
    orientationCount = 0
    projectsCount = 0
    shadowCount = 0
    tweetersCount = 0
    closersexpertCount = 0
    followUpCount = 0
    connectingCount = 0
    connectedCount = 0
    endedCount = 0
    # Check the table for status counts ( could by done in a more efficient way using an array )
    for item in list:
        if item['Agent Status'] == 'Available':
            availableCount += 1
        elif item['Agent Status'] == 'Offline':
            offlineCount += 1
        elif item['Agent Status'] == 'Apprenticeship':
            apprenticeCount += 1
        elif item['Agent Status'] == 'Bi-weekly':
            biweeklyCount += 1
        elif item['Agent Status'] == 'Break/Lunch':
            break_lunchCount += 1
        elif item['Agent Status'] == 'GB+':
            gbplusCount += 1
        elif item['Agent Status'] == 'MaxPreps':
            maxprepsCount += 1
        elif item['Agent Status'] == 'Interview':
            interviewCount += 1
        elif item['Agent Status'] == 'Meetings':
            meetingCount += 1
        elif item['Agent Status'] == 'Orientation':
            orientationCount += 1
        elif item['Agent Status'] == 'Projects':
            projectsCount += 1
        elif item['Agent Status'] == 'Shadowing':
            shadowCount += 1
        elif item['Agent Status'] == 'Tweeters':
            tweetersCount += 1
        elif item['Agent Status'] == 'Closer/Expert Calls':
            closersexpertCount += 1
        elif item['Agent Status'] == 'Follow-Up Work':
            followUpCount += 1
        elif item['Agent Status'] == 'CONNECTING':
            connectingCount += 1
        elif item['Agent Status'] == 'CONNECTED' or item['Agent Status'] == 'CONNECTED_ONHOLD':
            connectedCount += 1
        elif item['Agent Status'] == 'ENDED':
            endedCount += 1
    # Group counts
    totals = {'Projects': projectsCount, 'Tweeters': tweetersCount, 'Closer/Expert Calls': closersexpertCount, 'Follow-Up Work': endedCount+followUpCount,  'On a Call': connectingCount +
              connectedCount, 'Available':  availableCount, 'Offline': offlineCount, 'Shadowing':  shadowCount, 'Break/Lunch':  break_lunchCount, 'Apprenticeship': apprenticeCount, 'Meetings': meetingCount}
    return totals

# Itterate through list to find the longest available time, save that user
def upNext(list):
    upNext = {'Name': '', 'Duration': 1700000000}
    for item in list:
        if item['Agent Status'] == 'Available':
            newName = item['Agent Name']
            statusStart = item['Duration']
            if statusStart < upNext['Duration']:
                upNext = {'Name': newName, 'Duration': statusStart}
    return upNext

# This is where we do the math to find time available. Taking the invocation time and comparing to the status start time, converting from epoch to date time format
def timeAvailable(list):
    avaList = []
    text = ""
    for item in list:
        if item["Agent Status"] == "Available":
            statusStart = str(item["Duration"])
            realStatusStart = datetime.strptime(time.strftime(
                '%m-%d %H:%M:%S', time.localtime(int(statusStart))), '%m-%d %H:%M:%S')
            nowTime = datetime.strptime(time.strftime(
                '%m-%d %H:%M:%S', time.localtime(time.time())), '%m-%d %H:%M:%S')
            timeInState = nowTime - realStatusStart
            avaList.append(
                {'agentName': item['Agent Name'], 'routingProfile': item['Routing Profile'], 'timeAvailable': timeInState})
    avaListSorted = sorted(avaList, key=itemgetter(
        'timeAvailable'), reverse=True)
    for item in avaListSorted:
        if item['routingProfile'] == 'Supp-Class 2':
            line = item['agentName'] + " has been available for " + \
                str(item['timeAvailable'])+" (Sideline)\n"
        else:
            line = item['agentName'] + " has been available for " + \
                str(item['timeAvailable'])+"\n"
        text = text + line
    return text

# Buckets 1,2,3 are different support tiers that we group together and use this to find info about those groups
def bucketOne(list):
    buckOneList = []
    text = ""
    for item in list:
        if item["Agent Status"] in ("Follow-Up Work", "GB+", "Tweeters", "Projects", "Closer/Expert Calls", "MaxPreps", "ENDED"):
            statusStart = str(item["Duration"])
            realStatusStart = datetime.strptime(time.strftime(
                '%m-%d %H:%M:%S', time.localtime(int(statusStart))), '%m-%d %H:%M:%S')
            nowTime = datetime.strptime(time.strftime(
                '%m-%d %H:%M:%S', time.localtime(time.time())), '%m-%d %H:%M:%S')
            timeInState = nowTime - realStatusStart
            buckOneList.append({'agentName': item['Agent Name'], 'routingProfile': item['Routing Profile'],
                                'status': item["Agent Status"], 'timeAvailable': timeInState})
    buckOneListSorted = sorted(
        buckOneList, key=itemgetter('timeAvailable'), reverse=True)
    for item in buckOneListSorted:
        line = item['agentName'] + " has been on " + \
            item['status'] + " for " + str(item['timeAvailable'])+"\n"
        text = text + line
    return text


def bucketTwo(list):
    buckTwoList = []
    text = ""
    for item in list:
        if item["Agent Status"] in ("Apprenticeship", "Meetings"):
            statusStart = str(item["Duration"])
            realStatusStart = datetime.strptime(time.strftime(
                '%m-%d %H:%M:%S', time.localtime(int(statusStart))), '%m-%d %H:%M:%S')
            nowTime = datetime.strptime(time.strftime(
                '%m-%d %H:%M:%S', time.localtime(time.time())), '%m-%d %H:%M:%S')
            timeInState = nowTime - realStatusStart
            buckTwoList.append({'agentName': item['Agent Name'], 'routingProfile': item['Routing Profile'],
                                'status': item["Agent Status"], 'timeAvailable': timeInState})
    buckTwoListSorted = sorted(
        buckTwoList, key=itemgetter('timeAvailable'), reverse=True)
    for item in buckTwoListSorted:
        line = item['agentName'] + " has been on " + \
            item['status'] + " for " + str(item['timeAvailable'])+"\n"
        text = text + line
    return text


def bucketThree(list):
    buckThreeList = []
    text = ""
    for item in list:
        if item["Agent Status"] in ("Break/Lunch", "Orientation", "Interview", "Shadowing", "Bi-weekly"):
            statusStart = str(item["Duration"])
            realStatusStart = datetime.strptime(time.strftime(
                '%m-%d %H:%M:%S', time.localtime(int(statusStart))), '%m-%d %H:%M:%S')
            nowTime = datetime.strptime(time.strftime(
                '%m-%d %H:%M:%S', time.localtime(time.time())), '%m-%d %H:%M:%S')
            timeInState = nowTime - realStatusStart
            buckThreeList.append({'agentName': item['Agent Name'], 'routingProfile': item['Routing Profile'],
                                  'status': item["Agent Status"], 'timeAvailable': timeInState})
    buckThreeListSorted = sorted(
        buckThreeList, key=itemgetter('timeAvailable'), reverse=True)
    for item in buckThreeListSorted:
        line = item['agentName'] + " has been on " + \
            item['status'] + " for " + str(item['timeAvailable'])+"\n"
        text = text + line
    return text

# Handle the request and take the paramater (statusReq) then run the funciton that parameter refers to
def lambda_handler(event, context):
    request_data = parse_input(event["body"])
    statusReq = request_data["text"]
    list = getSuppAgents()
    totals = getStatusCount(list)
    next = upNext(list)
    if statusReq == 'All':
        text = "There are:\n " + str(totals.get('On a Call')) + " rep(s) on a call\n" + str(totals.get(
            'Available')) + " agents available \n" + str(totals.get('Follow-Up Work')) + " agents in follow up "
    elif statusReq == 'Next':
        text = next['Name']+' is next up for a call'
    elif statusReq in totals:
        text = "There are " + str(totals.get(statusReq)) + \
            " support reps currently in " + statusReq + " status."
    elif statusReq == 'Order':
        text = timeAvailable(list)
    elif statusReq == 'Bucket One':
        text = bucketOne(list)
    elif statusReq == 'Bucket Two':
        text = bucketTwo(list)
    elif statusReq == 'Bucket Three':
        text = bucketThree(list)
    # Easter Egg gif response
    elif statusReq == 'hotline':
        text = "https://giphy.com/gifs/Tiffany-drake-elaine-benes-slideshow-NXjbbmqehJHkk"
    elif statusReq == 'info':
        text = "All-- Will show counts for agents on calls, Available, and in Follow up work\nNext-- Show who is next up for a call\nOrder-- Show all agents available in the order calls will be received on the main support line. If noted as Sideline then those are Class 2 reps on the sideline line as well.\n Any individual status will display the number of reps in that status ('Follow-Up Work', 'On a Call', 'Available', 'Offline', 'Shadowing', 'Break/Lunch', 'Apprenticeship', 'Meetings')\n"
    elif statusReq == 'squadlead':
        text = "Bucket One-- People we can ask to get back on calls, status in Follow-Up Work, GB+, Tweeters, Projects, Closer/Expert Calls, MaxPreps, ENDED\nBucket Two-- Second level to get back on phones, status is Apprenticeship or Meetings\nBucket Three-- Last group to get back on phones, status in Break/Lunch, Orientation, Interview, Shadowing, Bi-weekly"
    else:
        text = "Invaild argument: Please use '/agent-status info' to see available options"

    # Return data to the API, Slack takes the message and displays the response which is our text we return from which ever function ran
    slackMes = {
        "response_type": "in_channel",
        "text": text
    }
    return {
        "body": json.dumps(slackMes),
        "headers": {"Content-Type": "application/json"},
        "statusCode": 200
    }
