exports.onExecutePostLogin = async (event, api) => {
  
    // Step-up (only when Flask asked for it)
    const stepUp = event.request?.query?.step_up;
    if (stepUp) {
      api.authentication.challengeWithAny(
        enrolled.map((f) => ({ type: f.type }))
      );  
    }
  };