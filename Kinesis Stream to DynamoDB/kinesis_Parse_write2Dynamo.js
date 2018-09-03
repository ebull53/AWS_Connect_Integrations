const AWS = require("aws-sdk");
exports.handler = (event, context, callback) => {
  // Take the event from the Kinesis stream that is set up as the trigger
  // Decode the message and get it in JSON format for easy handling
  const message = event.Records[0].kinesis.data;
  const decoded = new Buffer(message, "base64").toString("ascii");
  console.log(decoded);
  const parsed = JSON.parse(decoded);
  const logType = parsed.EventType;
  console.log(logType);

  // Check the log type becuase the format differs between Heartbeat and State change logs
  if (logType === "HEART_BEAT") {
    const createItem = () => {
      // Grab all the info we need and save as constants
      const currentStatusName = parsed.CurrentAgentSnapshot.AgentStatus.Name;
      const agentName = parsed.CurrentAgentSnapshot.Configuration.Username;
      const currentTimestamp = parsed.CurrentAgentSnapshot.AgentStatus.StartTimestamp;
      const newTime = Date.parse(currentTimestamp);
      const ingestTime = (newTime / 1000).toFixed(0);
      const numberTime = Number(ingestTime);
      const exp = numberTime + 43200; // This is our TTL value, the current epoch time plus 12 hours
      const routingProfile = parsed.CurrentAgentSnapshot.Configuration.RoutingProfile.Name;
      let phoneCall = "null";
      let contactType = "null";

      if (parsed.CurrentAgentSnapshot.Contacts.length > 0) {
        phoneCall = parsed.CurrentAgentSnapshot.Contacts[0].State;
        contactType = parsed.CurrentAgentSnapshot.Contacts[0].Channel;
      }

      let params = "null";

      // Here we check if the agent is in an ended state as the location of the status we are looking for shifts from status name to phone call state
      if (contactType === "VOICE" && phoneCall === "ENDED") {
        params = {
          TableName: "SupportAgentStatus",
          Item: {
            "Agent Name": agentName,
            "Agent Status": currentStatusName,
            Duration: numberTime,
            ttl: exp,
            "Routing Profile": routingProfile
          }
        };
      } else if (contactType === "VOICE") {
        params = {
          TableName: "SupportAgentStatus",
          Item: {
            "Agent Name": agentName,
            "Agent Status": phoneCall,
            Duration: numberTime,
            ttl: exp,
            "Routing Profile": routingProfile
          }
        };
      } else {
        params = {
          TableName: "SupportAgentStatus",
          Item: {
            "Agent Name": agentName,
            "Agent Status": currentStatusName,
            Duration: numberTime,
            ttl: exp,
            "Routing Profile": routingProfile
          }
        };
      }

      // Take our data and send it to Dynamo, giving your function the IAM permissions to access the correct resources
      const request = new AWS.DynamoDB.DocumentClient().put(params);
      const promise = request.promise();

      // We use promise to run our function asynchonously. It's very easy to start dropping data if your functions take awhile to run and are happening synchonously.
      promise.then(
        function(data) {
          console.log("Success! " + agentName + " in " + currentStatusName);
          // process the data 
        },
        function(error) {
          console.log(`Failure ${params}`);
          // handle the error
        }
      );
    };
    createItem();
  }

  // Run through the same process but with the State change log type
  else if (logType === "STATE_CHANGE") {
    const createItem = () => {
      const currentStatusName = parsed.CurrentAgentSnapshot.AgentStatus.Name;
      const agentName = parsed.CurrentAgentSnapshot.Configuration.Username;
      const currentTimestamp = parsed.EventTimestamp;
      const newTime = Date.parse(currentTimestamp);
      const ingestTime = (newTime / 1000).toFixed(0);
      const numberTime = Number(ingestTime);
      const exp = numberTime + 43200;
      const routingProfile =
        parsed.CurrentAgentSnapshot.Configuration.RoutingProfile.Name;
      let phoneCall = "null";
      let contactType = "null";

      if (parsed.CurrentAgentSnapshot.Contacts.length > 0) {
        phoneCall = parsed.CurrentAgentSnapshot.Contacts[0].State;
        contactType = parsed.CurrentAgentSnapshot.Contacts[0].Channel;
      }

      let params = "null";

      if (contactType === "VOICE" && phoneCall === "ENDED") {
        params = {
          TableName: "SupportAgentStatus",
          Item: {
            "Agent Name": agentName,
            "Agent Status": currentStatusName,
            Duration: numberTime,
            ttl: exp,
            "Routing Profile": routingProfile
          }
        };
      } else if (contactType === "VOICE") {
        params = {
          TableName: "SupportAgentStatus",
          Item: {
            "Agent Name": agentName,
            "Agent Status": phoneCall,
            Duration: numberTime,
            ttl: exp,
            "Routing Profile": routingProfile
          }
        };
      } else {
        params = {
          TableName: "SupportAgentStatus",
          Item: {
            "Agent Name": agentName,
            "Agent Status": currentStatusName,
            Duration: numberTime,
            ttl: exp,
            "Routing Profile": routingProfile
          }
        };
      }

      const request = new AWS.DynamoDB.DocumentClient().put(params);
      const promise = request.promise();

      promise.then(
        function(data) {
          console.log("Success! " + agentName + " in " + currentStatusName);
        },
        function(error) {
          console.log(`Failure ${params}`);
        }
      );
    };
    createItem();
  }
};
