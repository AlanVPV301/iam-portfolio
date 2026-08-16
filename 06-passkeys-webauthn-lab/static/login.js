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

//Prepare base64url string for the buffer function
function prepareAuthenticationOptions(options) {
  const publicKey = structuredClone(options);
  publicKey.challenge = bufferFromBase64url(publicKey.challenge);
  if (publicKey.allowCredentials) {
    publicKey.allowCredentials = publicKey.allowCredentials.map((cred) => ({
      ...cred,
      id: bufferFromBase64url(cred.id),
    }));
  }
  return publicKey;
}

//Parse the PublicKeyCredential object for assertion
function authenticationCredentialToJSON(credential) {
  const response = credential.response;
  return {
    id: credential.id,
    rawId: bufferToBase64url(credential.rawId),
    type: credential.type,
    response: {
      clientDataJSON: bufferToBase64url(response.clientDataJSON),
      authenticatorData: bufferToBase64url(response.authenticatorData),
      signature: bufferToBase64url(response.signature),
      userHandle: response.userHandle
        ? bufferToBase64url(response.userHandle)
        : null,
    },
    clientExtensionResults: credential.getClientExtensionResults(),
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

document.getElementById("login-btn").addEventListener("click", async () => {
  if (!window.PublicKeyCredential) {
    logLine("WebAuthn is not available in this browser or context.");
    return;
  }

  const btn = document.getElementById("login-btn");
  btn.disabled = true;

  try {
    const form = document.getElementById("loginForm");
    if (!form.reportValidity()) {
      btn.disabled = false;
      return;
    }

    const formData = new FormData(form);
    const usernameValue = formData.get("username");

    clearLog();
    logScenarioHeader();

    const optionsResp = await fetch("/webauthn/login/options", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: usernameValue,
        scenario: window.selectedScenario ? window.selectedScenario() : "happy",
      }),
    });
    logLine("POST /webauthn/login/options " + optionsResp.status);

    const optionsFromServer = await parseOptionsResponse(optionsResp);
    logLine("RP ID from server: " + (optionsFromServer.rpId || optionsFromServer.rp?.id || "(missing)"));

    let assertion;
    try {
      assertion = await navigator.credentials.get({
        publicKey: prepareAuthenticationOptions(optionsFromServer)
      });
    } catch (err) {
      logCeremonyError("credentials.get", err);
      return;
    }

    const verifyResponse = await fetch('/webauthn/login/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(authenticationCredentialToJSON(assertion)),
      credentials: "same-origin",
    });

    const result = await verifyResponse.json();
    logLine("POST /webauthn/login/verify " + verifyResponse.status);
    if (!verifyResponse.ok) {
      logLine(result.detail || result.msg || verifyResponse.statusText);
      return;
    }

    await renderSession();
  } catch (err) {
    logLine("error: " + (err.message || String(err)));
  } finally {
    btn.disabled = false;
  }

});

async function renderSession() {
  try {
    const resp = await fetch("/me", { credentials: "same-origin" });
    const payload = await resp.json();
    const logout_btn = document.getElementById("logout-btn");
    if (resp.ok){
      logout_btn.disabled = false;
    }
    logLine(
      resp.ok
        ? "signed in as " + payload.user_name
        : "signed out"
    );
  } catch (err) {
    logLine("error: " + (err.message || String(err)));
  }
}

renderSession();
