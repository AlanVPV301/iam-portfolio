//string → ArrayBuffer. server sends strings, browser API needs bytes
function bufferFromBase64url(value) {
  const padding = "=".repeat((4 - (value.length % 4)) % 4);
  const base64 = (value + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64);
  const buffer = new ArrayBuffer(raw.length);
  const view = new Uint8Array(buffer);
  for (let i = 0; i < raw.length; i++) view[i] = raw.charCodeAt(i);
  return buffer;
}

//ArrayBuffer → string. browser gives bytes, server expects strings in JSON
function bufferToBase64url(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}


function prepareRegistrationOptions(options) {
  const publicKey = structuredClone(options); //Clone to prevent mutating the original
  publicKey.challenge = bufferFromBase64url(publicKey.challenge);
  publicKey.user.id = bufferFromBase64url(publicKey.user.id);
  if (publicKey.excludeCredentials) {
    publicKey.excludeCredentials = publicKey.excludeCredentials.map((cred) => ({
      ...cred,
      id: bufferFromBase64url(cred.id),
    }));
  }
  return publicKey;
}

//Builds plain JSON dict payload for the FastAPI endpoint
function registrationCredentialToJSON(credential) {
  const response = credential.response;
  return {
    id: credential.id,
    rawId: bufferToBase64url(credential.rawId),
    type: credential.type,
    response: {
      attestationObject: bufferToBase64url(response.attestationObject),
      clientDataJSON: bufferToBase64url(response.clientDataJSON),
      transports: response.getTransports ? response.getTransports() : undefined,
    },
    clientExtensionResults: credential.getClientExtensionResults(),
    authenticatorAttachment: credential.authenticatorAttachment ?? undefined,
  };
}

async function parseOptionsResponse(resp) {
  const payload = await resp.json();
  if (!resp.ok) {
    const detail = payload?.detail;
    if (typeof detail === "string") throw new Error(detail);
    if (Array.isArray(detail)) {
      throw new Error(detail.map((item) => item.msg).join("; "));
    }
    throw new Error(resp.statusText || "Request failed");
  }
  if (typeof payload === "string") return JSON.parse(payload);
  return payload;
}

document.getElementById("register-btn").addEventListener("click", async () => {
  if (!window.PublicKeyCredential) {
    logLine("WebAuthn is not available in this browser or context.");
    return;
  }

  const btn = document.getElementById("register-btn");
  btn.disabled = true;

  try {
    const form = document.getElementById("registerForm");
    if (!form.reportValidity()) {
      btn.disabled = false;
      return;
    }

    const formData = new FormData(form);
    const usernameValue = formData.get("username");
    const displayNameValue = formData.get("displayName");

    clearLog();
    logScenarioHeader();

    const optionsResp = await fetch("/webauthn/register/options", {
      method: "POST",
      credentials: "same-origin", // required so the browser sends and stores the _webauthn_tx cookie from the server
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: usernameValue,
        display_name: displayNameValue,
        scenario: window.selectedScenario ? window.selectedScenario() : "happy",
      }),
    });
    logLine("POST /webauthn/register/options " + optionsResp.status);
    const options = await parseOptionsResponse(optionsResp);
    logLine("RP ID from server: " + (options.rp?.id || options.rpId || "(missing)"));

    let credential;
    try {
      credential = await navigator.credentials.create({
        publicKey: prepareRegistrationOptions(options),
      });
    } catch (err) {
      logCeremonyError("credentials.create", err);
      return;
    }
    if (!credential) throw new Error("No credential returned.");
    logLine("credentials.create OK id=" + String(credential.id).slice(0, 12) + "…");

    const verifyResp = await fetch("/webauthn/register/verify", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(registrationCredentialToJSON(credential)),
    });
    const result = await verifyResp.json();
    logLine("POST /webauthn/register/verify " + verifyResp.status);
    if (!verifyResp.ok) {
      logLine(result.detail || result.msg || verifyResp.statusText);
      return;
    }

    logLine("registered");
  } catch (err) {
    logLine("error: " + (err.message || String(err)));
  } finally {
    btn.disabled = false;
  }
});
