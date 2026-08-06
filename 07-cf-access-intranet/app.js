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

function formatGroups(groups) {
  if (!Array.isArray(groups) || groups.length === 0) return "none";
  return groups.join(", ");
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
    nameEl.textContent = identity.name || "—";
    groupsEl.textContent = formatGroups(identity.groups);
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
