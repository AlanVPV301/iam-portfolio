/**
 * Post User Registration Action — copy into Auth0 Dashboard → Actions →
 * Post User Registration flow, then Deploy.
 *
 * Action secrets (required):
 *   SCIM_URL — public SCIM origin, no trailing slash
 *              e.g. https://scim.alanvpv.dev (Render)
 *   BEARER   — same value as SCIM_BEARER_TOKEN in Project 3
 *
 * Auth0 Actions run in Auth0's cloud and cannot reach localhost.
 *
 * On timing: Auth0 terminates any Action that runs longer than 20 seconds, and
 * a sleeping Render free instance takes 50-60 seconds to cold start. No retry
 * or wait can outlast a sleeping SCIM server, so the timeouts below exist to
 * fail fast and say why in the logs — not to survive it. Keep SCIM warm during
 * demo hours instead (see 04-lifecycle-orchestrator/scripts/prime-demo.sh).
 *
 * Also note this trigger is non-blocking: signup succeeds regardless of what
 * happens here, so these console lines are the only evidence you get. They show
 * up in Auth0 Dashboard → Monitoring → Logs.
 */

// Two bounded calls at 5s each leave plenty of room inside the 20s ceiling, and
// guarantee the create is still attempted even when the lookup is slow.
const REQUEST_TIMEOUT_MS = 5000;

async function fetchWithTimeout(url, options) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    // Clear even on success, or a fast response still leaves the timer pending.
    clearTimeout(timer);
  }
}

// Distinguishes "never got a response" from "got a response we did not like".
// An AbortError here almost always means the host is asleep or unreachable.
function describeNetworkError(error) {
  return error.name === "AbortError"
    ? `timed out after ${REQUEST_TIMEOUT_MS}ms — SCIM host asleep or unreachable?`
    : `could not connect — ${error.message}`;
}

exports.onExecutePostUserRegistration = async (event, api) => {
  const SCIM_URL = event.secrets.SCIM_URL;
  const BEARER = event.secrets.BEARER;

  if (!SCIM_URL || !BEARER) {
    console.error(
      "Missing Action secrets: set SCIM_URL and BEARER before deploying."
    );
    return;
  }

  // A trailing slash would build //scim/v2/Users and 404.
  const baseUrl = SCIM_URL.replace(/\/+$/, "");
  const authHeader = { Authorization: `Bearer ${BEARER}` };
  const email = event.user.email;

  // Auth0 user_ids look like "auth0|abc123". The pipe, the quotes and the
  // spaces in the filter all need encoding before they go in a query string.
  const query = new URLSearchParams({
    filter: `externalId eq "${event.user.user_id}"`,
  });

  let lookup;
  try {
    lookup = await fetchWithTimeout(`${baseUrl}/scim/v2/Users?${query}`, {
      method: "GET",
      headers: authHeader,
    });
  } catch (error) {
    console.error(`SCIM lookup ${describeNetworkError(error)}`);
    return;
  }

  // Without this check a 401 body would be parsed as if it were a user list,
  // come back with no Resources, and be misread as "not provisioned yet" — so
  // every signup would follow up with a create that fails the same way.
  if (!lookup.ok) {
    console.error(
      `SCIM lookup rejected: HTTP ${lookup.status} — ${await lookup.text()}`
    );
    return;
  }

  const data = await lookup.json();
  const existing = data.Resources?.[0] ?? null;

  if (existing) {
    console.log(`SCIM user already exists for ${email} (id ${existing.id})`);
    return;
  }

  // Project 3 requires name.givenName and name.familyName, but a database
  // signup usually carries neither — those come from social providers or from
  // extra signup fields. Derive something stable so the create does not 422.
  const emailLocalPart = email.split("@")[0];
  const userData = {
    userName: email,
    externalId: event.user.user_id,
    name: {
      givenName: event.user.given_name || event.user.nickname || emailLocalPart,
      familyName: event.user.family_name || "Unspecified",
    },
    emails: [{ value: email, primary: true }],
    roles: ["Engineering"],
  };

  let created;
  try {
    created = await fetchWithTimeout(`${baseUrl}/scim/v2/Users`, {
      method: "POST",
      headers: { ...authHeader, "Content-Type": "application/json" },
      body: JSON.stringify(userData),
    });
  } catch (error) {
    console.error(`SCIM create ${describeNetworkError(error)}`);
    return;
  }

  if (!created.ok) {
    console.error(
      `SCIM create rejected: HTTP ${created.status} — ${await created.text()}`
    );
    return;
  }

  const body = await created.json();
  console.log(`SCIM user created for ${email} (id ${body.id})`);
};
