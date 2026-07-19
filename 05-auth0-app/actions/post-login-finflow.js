/**
 * Post-login Action — copy into Auth0 Dashboard → Actions → Login flow
 * Requires: Adaptive MFA + Risk Assessment enabled; user enrolled in MFA
 */
exports.onExecutePostLogin = async (event, api) => {
  const enrolled = (event.user.enrolledFactors ?? []).map((f) => ({ type: f.type }));
  const canMfa = enrolled.length > 0;

  // Step-up when Flask sends /login?step_up=payroll
  if (event.request?.query?.step_up && canMfa) {
    api.multifactor.enable("any", { allowRememberBrowser: false });
    return;
  }

  // Adaptive MFA — new / unrecognized device
  const newDevice = event.authentication?.riskAssessment?.assessments?.NewDevice;
  const risky =
    newDevice &&
    (newDevice.confidence === "low" || newDevice.confidence === "medium");

  if (risky && canMfa) {
    api.authentication.challengeWithAny(enrolled);
  }
};
