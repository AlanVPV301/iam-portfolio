const output = document.getElementById("output");

function time() {
  return new Date().toLocaleTimeString("en-GB", { hour12: false });
}

function clearLog() {
  output.textContent = "";
}

function logLine(message) {
  const line = typeof message === "string" ? message : JSON.stringify(message);
  output.textContent += (output.textContent ? "\n" : "") + `[${time()}] ${line}`;
  output.scrollTop = output.scrollHeight;
}

function logScenarioHeader() {
  const spec = window.labConfig.scenarios[window.selectedScenario()];
  logLine("Scenario: " + spec.name);
  logLine("This page: " + location.origin);
  logLine("RP ID in options: " + spec.options_rp_id);
  logLine("Origin at verify: " + spec.verify_origin);
  if (spec.expected_failure) logLine("Expected: " + spec.expected_failure);
}

function logCeremonyError(step, err) {
  logLine(
    step + " FAIL " + (err.name || "Error") + ": " + (err.message || String(err))
  );
  if (err.name === "SecurityError" || /insecure/i.test(err.message || "")) {
    const spec = window.labConfig?.scenarios?.[window.selectedScenario?.()];
    if (spec?.expected_failure) logLine("Expected: " + spec.expected_failure);
  }
}

window.clearLog = clearLog;
window.logLine = logLine;
window.log = logLine; // logout /me can keep calling log(...)
window.logScenarioHeader = logScenarioHeader;
window.logCeremonyError = logCeremonyError;