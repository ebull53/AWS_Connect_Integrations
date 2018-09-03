def lambda_handler(event, context):
    import boto3
    import os
    import time
    from datetime import datetime, timedelta
    from boto3.dynamodb.conditions import Key, Attr
    from base64 import b64decode
    from operator import itemgetter
    from slacker import Slacker
   
    ENCRYPTED_EXPECTED_TOKEN = os.environ['SlackToken']
    
    kms = boto3.client('kms')
    expected_token = kms.decrypt(CiphertextBlob=b64decode(ENCRYPTED_EXPECTED_TOKEN))['Plaintext']
    dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
    table = dynamodb.Table('SupportAgentStatus')
    
    
    
    time2Check = 10 # minutes you want to check against
    a = timedelta(minutes = time2Check)
    
    def getSuppAgents(): # Read our dynamo table to get agent info
        supportReps = []
        followup = []
        tableResponse = table.scan()
        agents = tableResponse['Items']
        for item in agents:
            if (item['Routing Profile'].startswith("Supp") or item['Routing Profile']=="CAM Support - Volleymetrics") and item['Agent Status'] == "Follow-Up Work": #set routing profile you want to check against
                supportReps.append(item)
            else:
                continue
        for item in supportReps: # find the duration by taking status time minus current time
            statusStart = str(item["Duration"])
            realStatusStart = datetime.strptime(time.strftime('%m-%d %H:%M:%S', time.localtime(int(statusStart))),'%m-%d %H:%M:%S')
            nowTime = datetime.strptime(time.strftime('%m-%d %H:%M:%S', time.localtime(time.time())),'%m-%d %H:%M:%S')
            timeInState = nowTime - realStatusStart
            if timeInState > a: # check to see if the time in this state is greater then the time we want to check against
                followup.append({'agentName':item['Agent Name'],'routingProfile':item['Routing Profile'], 'duration':str(timeInState)})
        return followup # return list of people over follow up time limit

    def postSlackMessage(message): # define the slack details for the message
        slack.chat.post_message('#cr-rsl', message, username='Follow-Up Bot',icon_url='')#####insert image link here#####

    try: 
        slack = Slacker(expected_token)
        followupList = getSuppAgents()
        slackMessage = "These agents have been in Follow-Up Work for over " + str(time2Check) + " min:\n"
        if len(followupList) > 0: # make sure we have people in our list or else dont post to slack
            for item in followupList:
                slackMessage = slackMessage +item["agentName"] + " (" + str(item['duration']) + ")\n"
            postSlackMessage(slackMessage)
        else:
            print ("Empty List")
    except:  # If the script fails, we should post something so we know it died!
        slackMessage = "There people are in follow up but I dont know who or for how long! The notification failed. Contact someone about fixing it."
        postSlackMessage(slackMessage)
   