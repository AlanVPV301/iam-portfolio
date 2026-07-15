exports.onExecutePostLogin = async (event, api) => {
    const newDevice = event.authentication?.riskAssessment?.assessments?.NewDevice;
    if (!newDevice) return;
  
    const risky = newDevice.confidence === 'low' || newDevice.confidence === 'medium';
    const enrolled = event.user.enrolledFactors ?? [];
  
    if (risky && enrolled.length > 0) {
      api.authentication.challengeWithAny(
        enrolled.map((f) => ({ type: f.type }))
      );
    }
  
    // Step-up (only when Flask asked for it)
    const stepUp = event.request?.query?.step_up;
    if (stepUp) {
      api.authentication.challengeWithAny(
        enrolled.map((f) => ({ type: f.type }))
      );  
    }
  };