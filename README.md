# AWS_Connect_Integrations
Collection of ways to integration Amazon Connect with other systems to get real time data and notifications. Using DynamoDB, Lambda, Kinesis Streams, API Gateways, and Slack.

READ ME

Kinesis Stream to DynamoDB - 

 When setting up the Dynamo table the most important part is to set up the Primary partition key correctly. This is the value you want to be able to check against when looking for existing values in the table. Don't forget to also enable the TTL column from you table settings, this allows you to remove unneeded columns. The Dynamo table we use is set up with read and write capacity of 3 and we basically never even hit 1. Unless dealing with thousands of rows you can also turn auto scaling off, it is very inexpensive to run this table. 

The trigger for the function is the Kinesis Stream with a batch size set up at 50. Giving the allow-read-from-kinesis-STREAM NAME IAM privs to your Lambda function.
Here is an example event from our Kinesis Stream, You can see how and where we are parsing out the values:
        
{
  "AWSAccountId": "**********",
  "AgentARN": "arn:aws:connect:us-east-1:**********:instance/**********/agent/************",
  "CurrentAgentSnapshot": {
    "AgentStatus": {
      "ARN": "arn:aws:connect:us-east-1:**********:instance/**********/agent-state/*******",
      "Name": "Available",
      "StartTimestamp": "2018-07-09T19:11:00.000Z"
    },
    "Configuration": {
      "AgentHierarchyGroups": null,
      "FirstName": "Kevin",
      "LastName": "*****",
      "RoutingProfile": {
        "ARN": "arn:aws:connect:us-east-1:**********:instance/**********/routing-profile/**********",
        "DefaultOutboundQueue": {
          "ARN": "arn:aws:connect:us-east-1:**********:instance/**********/queue/**********",
          "Name": "Support Outbound"
        },
        "InboundQueues": [
          {
            "ARN": "arn:aws:connect:us-east-1:**********:instance/**********/queue/**********",
            "Name": "Billing"
          },
          {
            "ARN": "arn:aws:connect:us-east-1:**********:instance/**********/queue/**********",
            "Name": "Sales"
          },
          {
            "ARN": "arn:aws:connect:us-east-1:**********:instance/**********/queue/**********",
            "Name": "Sideline Support"
          },
          {
            "ARN": "arn:aws:connect:us-east-1:**********:instance/**********/queue/**********",
            "Name": "Support Main"
          },
          {
            "ARN": "arn:aws:connect:us-east-1:**********:instance/**********/queue/**********",
            "Name": "Gamebreaker"
          },
          {
            "ARN": "arn:aws:connect:us-east-1:**********:instance/**********/queue/**********",
            "Name": "Platinum"
          },
          {
            "ARN": "arn:aws:connect:us-east-1::**********::instance/**********/queue/**********",
            "Name": "Other Questions"
          }
        ],
        "Name": "Supp-Class 2"
      },
      "Username": "kevin.*****"
    },
    "Contacts": []
  },
  "EventId": ":**********:-f230-4b1c-ba87-**********",
  "EventTimestamp": "2018-07-09T19:11:00.000Z",
  "EventType": "STATE_CHANGE",
  "InstanceARN": "arn:aws:connect:us-east-1:**********:instance/*****************",
  "PreviousAgentSnapshot": null,
  "Version": "2017-10-01"
}



Slack Slash Command -

Apprenticeship, Bi-weekly, Break/Lunch, GB+, MaxPreps, Interview, Meetings, Orientation, Projects, Shadowing, Tweeters, Closer/Expert Calls, and Follow-Up Work are our different agent states we have set up.  Available, Offline, Connecting, Connected, and Ended are default agent states. Replacing ours with your own agent statuses across this file will allow you to get counts for them, the default agent states will be the same.

To group different statuses together use the 'totals' array to group any states together that you want. Grouping Connected and Connecting will give you a count of all people on a call, also Ended and Follow-Up work combined shows people who just got off a call.

In the lambda handler we use an if statement to take our parameter we pass in from the api and check it again different options. the text can be found in the body of the POST request. This is why we parse out the body of the request to find it.

Your Lambda function needs to have allow-dynamob-fullaccess-TABLENAME IAM privs to read and write to your Dynamo table.


Follow Up Work Notifications - 

The trigger for this script is a fixed rate CloudWatch event of 15 min. This can be configured and set to whatever time span fits your needs. This function needs the same full access IAM privs to your Dynamo table. As well as an environment variable in Lambda for your slack token. The other option you have is to not encrypt this token and put it directly in to your script. This is not advised but it is an option. We have our Routing Profiles in connect for the support team using the same naming conventions: Supp-Class1, Supp-Class2, and Supp-Class3. This allows us to look for profiles starting with "Supp" along with one other profile we use for a special section of support, "CAM Support - Volleymetrics" and check for ones in the Follow-Up Work state.

Using a try/except and inserting variables into the Slack message allows us to customize the message each time as well as still get a Slack message even if it fails.