from webauthn import (
    generate_registration_options,
    verify_registration_response,
    options_to_json,
    base64url_to_bytes,
    verify_authentication_response,
    generate_authentication_options
    
)
import os
from webauthn.helpers.structs import (
    UserVerificationRequirement,
    PublicKeyCredentialDescriptor,
)
from webauthn.authentication.verify_authentication_response import VerifiedAuthentication

RP_NAME = os.getenv("RP_NAME")
RP_ID = os.getenv("RP_ID")
ORIGIN = os.getenv("ORIGIN")

SCENARIO_NAMES = ("happy", "wrong_rp_id", "wrong_origin","expired_challenge")
WRONG_RP_ID = "evil.example"
WRONG_ORIGIN = "https://other.origin"


def resolve_scenario(name: str | None) -> dict:
    scenario = name if name in SCENARIO_NAMES else "happy"
    if scenario == "wrong_rp_id":
        return {
            "name": scenario,
            "options_rp_id": WRONG_RP_ID,
            "verify_rp_id": WRONG_RP_ID,
            "verify_origin": ORIGIN,
            "expected_failure": "Browser rejects rpId that is not this page's host.",
        }
    if scenario == "wrong_origin":
        return {
            "name": scenario,
            "options_rp_id": RP_ID,
            "verify_rp_id": RP_ID,
            "verify_origin": WRONG_ORIGIN,
            "expected_failure": "Ceremony succeeds; server verify fails on origin mismatch.",
        }
    if scenario == "expired_challenge":
        return {
            "name": scenario,
            "options_rp_id": RP_ID,
            "verify_rp_id": RP_ID,
            "verify_origin": ORIGIN,
            "expected_failure": "Ceremony succeeds; server verify fails on with 400 expired cookie.",
        }
    return {
        "name": "happy",
        "options_rp_id": RP_ID,
        "verify_rp_id": RP_ID,
        "verify_origin": ORIGIN,
        "expected_failure": "",
    }


def lab_config() -> dict:
    return {
        "rp_id": RP_ID,
        "origin": ORIGIN,
        "scenarios": {name: resolve_scenario(name) for name in SCENARIO_NAMES},
    }


def begin_registration(
    user_name: str,
    user_id: bytes,
    display_name: str,
    *,
    rp_id: str,
) -> tuple[dict, bytes]:
    options = generate_registration_options(
        rp_id=rp_id,
        rp_name=RP_NAME,
        user_id=user_id,
        user_name=user_name,
        user_display_name=display_name,
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    challenge = options.challenge
    return options_to_json(options), challenge

def finish_registration(
    credential: dict,
    expected_challenge: bytes,
    *,
    expected_rp_id: str,
    expected_origin: str,
):
    try:
        return verify_registration_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_origin=expected_origin,
            expected_rp_id=expected_rp_id,
        )
    except Exception as err:
        return {"verified": False, "msg": str(err), "status": 400}


def begin_authentication(
    user_id: str,
    allow_credentials: list[PublicKeyCredentialDescriptor],
    *,
    rp_id: str,
) -> tuple[str | dict, bytes]:
    options = generate_authentication_options(
        rp_id=rp_id,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    challenge = options.challenge
    return options_to_json(options), challenge

def finish_authentication(
    credential: dict,
    expected_challenge: bytes,
    *,
    public_key: bytes,
    sign_count: int,
    expected_rp_id: str,
    expected_origin: str,
) -> VerifiedAuthentication:
    try:
        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_rp_id=expected_rp_id,
            expected_origin=expected_origin,
            credential_public_key=public_key,
            credential_current_sign_count=sign_count,
            require_user_verification=True,
        )
    except Exception as err:
        return {"verified": False, "msg": str(err), "status": 400}

    return verification
