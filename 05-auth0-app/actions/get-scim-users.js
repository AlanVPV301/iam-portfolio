exports.onExecutePostUserRegistration = async (event, api) => {
    const SCIM_URL = "https://extremely-answer-reform-return.trycloudflare.com";
  
  
  fetch(`${SCIM_URL}/scim/v2/Users`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${event.secrets.BEARER}`  
    }
  })
    .then(response => response.json())
    .then(data => console.log('Success:', data))
    .catch(error => console.error('Error:', error));
    
  };