exports.onExecutePostUserRegistration = async (event, api) => {
    const SCIM_URL = "<SERVER_URL_HERE>";
  
  
  
    const userData = {
      "userName": event.user.email,
      "externalId": event.user.user_id,
      "name": {
        "givenName": event.user.given_name,
        "familyName": event.user.family_name,
      },
      "emails": [{"value": event.user.email, "primary": true}],
      "roles": ["Engineering"],
    }
  
    let scimUser = null;
    let response = null;
  
    try{
       response = await fetch(`${SCIM_URL}/scim/v2/Users?filter=externalId eq "${event.user.user_id}"`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${event.secrets.BEARER}`  
        }
      })
    }
    catch (error) {
      console.error("SCIM lookup error:", error);
      return;
    }
  
  
    const data = await response.json();          // ← saved to variable
    scimUser = data.Resources?.[0] ?? null;    // ← first match, or null
    console.log("Lookup result:", scimUser);
  
    if (!scimUser){
        try {
          fetch(`${SCIM_URL}/scim/v2/Users`, {
          method: 'POST',
          headers: {
          'Authorization': `Bearer ${event.secrets.BEARER}`,
          'Content-Type': 'application/json'  
          },
        body: JSON.stringify(userData)
        })
        }
        catch (error) {
          console.error("SCIM POST error:", error);
        return;
        }
    }
    
    else {
      console.log("User already exists!")
    }
    
  
    };
  
  
  