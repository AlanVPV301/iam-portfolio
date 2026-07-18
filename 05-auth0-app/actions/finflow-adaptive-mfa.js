exports.onExecutePostLogin = async (event, api) => {
  const newDevice = event.authentication?.riskAssessment?.assessments?.NewDevice;
  if (!newDevice) return;

  //MFA Challenge if device likely to be new/unrecognized 
  const risky = newDevice.confidence === 'low' || newDevice.confidence === 'medium';
  const enrolled = event.user.enrolledFactors ?? [];

  if (risky && enrolled.length > 0) {
    api.authentication.challengeWithAny(
      enrolled.map((f) => ({ type: f.type }))
    );
  }

};