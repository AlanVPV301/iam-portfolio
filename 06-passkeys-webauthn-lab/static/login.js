const outputLogin = document.getElementById("output");

function log(message) {
  outputLogin.textContent =
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
    log("WebAuthn is not available in this browser or context.");
    return;
  }

  const btn = document.getElementById("login-btn");
  btn.disabled = false;



  try {
    const form = document.getElementById("userForm");
    const formData = new FormData(form);
    const usernameValue = formData.get("username");

    const optionsResp = await fetch("/webauthn/login/options", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: usernameValue }),
    });

    //Check for errors in the options call before proceeding, to catch issues such as user not found

    const optionsFromServer = await parseOptionsResponse(optionsResp);

    console.log("options status", optionsResp.status);
    console.log("options raw", optionsFromServer);
    console.log("challenge", optionsFromServer.challenge);
    console.log("allowCredentials", optionsFromServer.allowCredentials);


    // 3. Request assertion (signature) from the user's device authenticator
    const assertion = await navigator.credentials.get({
      publicKey: prepareAuthenticationOptions(optionsFromServer)
    });

    // 5. Submit to server to finalize authentication and issue a session cookie/JWT
    const verifyResponse = await fetch('/webauthn/login/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(authenticationCredentialToJSON(assertion)),
      credentials: "same-origin", 
    });

    const result = await verifyResponse.json();
    if (!verifyResponse.ok) {
      throw new Error(result.detail || result.msg || verifyResponse.statusText);
    }

    await renderSession();
  } catch (err) {
    log({ status: "error", message: err.message || String(err) });
  } finally {
    btn.disabled = false;
  }

});

async function renderSession() {
  try {
    const resp = await fetch("/me", { credentials: "same-origin" });
    const payload = await resp.json();
    log(
      resp.ok
        ? { status: "signed in", user_name: payload.user_name }
        : { status: "signed out" }
    );
  } catch (err) {
    log({ status: "error", message: err.message || String(err) });
  }
}

renderSession();