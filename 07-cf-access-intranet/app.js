const emailEl = document.getElementById("identity-email");
const nameEl = document.getElementById("identity-name");
const groupsEl = document.getElementById("identity-groups");
const idpEl = document.getElementById("identity-idp");

function setIdentityError(message) {
  const text = message || "Could not load identity (open via Access)";
  emailEl.textContent = text;
  nameEl.textContent = "—";
  groupsEl.textContent = "—";
  idpEl.textContent = "—";
  emailEl.classList.add("identity-error");
}

const GROUPS_CLAIM =
  "http://schemas.microsoft.com/ws/2008/06/identity/claims/groups";

function formatGroups(identity) {
  // Access "groups" array (OIDC / SCIM-normalized) or SAML claim under custom
  if (Array.isArray(identity.groups) && identity.groups.length > 0) {
    return identity.groups.join(", ");
  }
  const fromCustom = identity.custom?.[GROUPS_CLAIM];
  if (Array.isArray(fromCustom) && fromCustom.length > 0) {
    return fromCustom.join(", ");
  }
  if (typeof fromCustom === "string" && fromCustom.trim()) {
    return fromCustom;
  }
  return "none";
}

function formatDisplayName(identity) {
  const parts = [identity.givenName, identity.surName].filter(Boolean);
  if (parts.length) return parts.join(" ");
  return identity.name || "—";
}

async function loadIdentity() {
  try {
    const resp = await fetch("/cdn-cgi/access/get-identity", {
      credentials: "same-origin",
    });
    if (!resp.ok) {
      setIdentityError("Could not load identity (open via Access)");
      return;
    }
    const identity = await resp.json();
    emailEl.textContent = identity.email || "—";
    nameEl.textContent = formatDisplayName(identity);
    groupsEl.textContent = formatGroups(identity);
    idpEl.textContent = identity.idp?.type || identity.idp?.id || "—";
    emailEl.classList.remove("identity-muted", "identity-error");
    nameEl.classList.remove("identity-muted");
    groupsEl.classList.remove("identity-muted");
    idpEl.classList.remove("identity-muted");
  } catch {
    setIdentityError("Could not load identity (open via Access)");
  }
}

loadIdentity();
