/**
 * Post User Registration Action — copy into Auth0 Dashboard → Actions →
 * Post User Registration flow, then Deploy.
 *
 * Action secrets (required):
 *   SCIM_URL — public SCIM origin, no trailing slash
 *              e.g. https://scim.alanvpv.dev (Render) or a local tunnel URL
 *   BEARER   — same value as SCIM_BEARER_TOKEN in Project 3
 *
 * Auth0 Actions run in Auth0's cloud and cannot reach localhost.
 */
exports.onExecutePostUserRegistration = async (event, api) => {
  const SCIM_URL = event.secrets.SCIM_URL;
  const BEARER = event.secrets.BEARER;

  if (!SCIM_URL || !BEARER) {
    console.error(
      "Missing Action secrets: set SCIM_URL and BEARER before deploying."
    );
    return;
  }

  const userData = {
    userName: event.user.email,
    externalId: event.user.user_id,
    name: {
      givenName: event.user.given_name,
      familyName: event.user.family_name,
    },
    emails: [{ value: event.user.email, primary: true }],
    roles: ["Engineering"],
  };

  let response = null;

  try {
    response = await fetch(
      `${SCIM_URL}/scim/v2/Users?filter=externalId eq "${event.user.user_id}"`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${BEARER}`,
        },
      }
    );
  } catch (error) {
    console.error("SCIM lookup error:", error);
    return;
  }

  const data = await response.json();
  const scimUser = data.Resources?.[0] ?? null;
  console.log("Lookup result:", scimUser);

  if (!scimUser) {
    try {
      const create_response = await fetch(`${SCIM_URL}/scim/v2/Users`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${BEARER}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(userData),
      });
      const created = await create_response.json();
      console.log("Created:", created);
    } catch (error) {
      console.error("SCIM POST error:", error);
      return;
    }
  } else {
    console.log("User already exists!");
  }
};
