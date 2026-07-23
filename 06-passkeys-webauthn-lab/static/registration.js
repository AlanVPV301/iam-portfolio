const output = document.getElementById("output");

function log(message) {
  output.textContent =
    typeof message === "string" ? message : JSON.stringify(message, null, 2);
}

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
  const publicKey = structuredClone(options);
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
  let options = await resp.json();
  if (typeof options === "string") options = JSON.parse(options);
  return options;
}

document.getElementById("register-btn").addEventListener("click", async () => {
  if (!window.PublicKeyCredential) {
    log("WebAuthn is not available in this browser or context.");
    return;
  }

  const btn = document.getElementById("register-btn");
  btn.disabled = true;

  try {
    log("Requesting registration options…");
    const optionsResp = await fetch("/webauthn/register/options", {
      method: "POST",
      credentials: "same-origin", // required so the browser sends and stores the _webauthn_tx cookie from the server
    });
    if (!optionsResp.ok) {
      throw new Error(`Options failed: ${optionsResp.status} ${optionsResp.statusText}`);
    }

    const options = await parseOptionsResponse(optionsResp);
    log("Creating passkey (browser prompt)…");

    const credential = await navigator.credentials.create({
      publicKey: prepareRegistrationOptions(options),
    });
    if (!credential) throw new Error("No credential returned.");

    log("Verifying registration…");
    const verifyResp = await fetch("/webauthn/register/verify", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(registrationCredentialToJSON(credential)),
    });

    const result = await verifyResp.json();
    if (!verifyResp.ok) {
      throw new Error(result.detail || result.msg || verifyResp.statusText);
    }

    log({ status: "registered", result });
  } catch (err) {
    log({ status: "error", message: err.message || String(err) });
  } finally {
    btn.disabled = false;
  }
});
