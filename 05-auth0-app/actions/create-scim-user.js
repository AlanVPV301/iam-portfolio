exports.onExecutePostUserRegistration = async (event, api) => {
    const SCIM_URL = "https://extremely-answer-reform-return.trycloudflare.com";
  
  
  
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
  
    fetch(`${SCIM_URL}/scim/v2/Users`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${event.secrets.BEARER}`,
        'Content-Type': 'application/json'  
      },
      body: JSON.stringify(userData)
    })
      .then(response => response.json())
      .then(data => console.log('Success:', data))
      .catch(error => console.error('Error:', error));
    
  };
  