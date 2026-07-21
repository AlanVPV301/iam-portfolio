from webauthn import (
    generate_registration_options,
    verify_registration_response,
    options_to_json,
    base64url_to_bytes,
)


def begin_registration(user_name: str) -> tuple[dict, bytes]:
    options = generate_registration_options(
    rp_id="localhost",
    rp_name="FinFlow",
    user_name="alan",
)
    challenge = options.challenge
    return options_to_json(options), challenge

def finish_registration(credential: dict, expected_challenge: bytes):
    try:
        return verify_registration_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_origin="http://localhost:8002",
            expected_rp_id="localhost",
        )
    except Exception as err:
        return {"verified": False, "msg": str(err), "status": 400}

    return {"verified": True}