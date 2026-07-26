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


def begin_registration(user_name: str, user_id: bytes, display_name:str) -> tuple[dict, bytes]:
    options = generate_registration_options(
    rp_id=RP_ID,
    rp_name=RP_NAME,
    user_id=user_id,
    user_name=user_name,
    user_display_name=display_name,

)
    challenge = options.challenge
    return options_to_json(options), challenge

def finish_registration(credential: dict, expected_challenge: bytes):
    try:
        return verify_registration_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
        )
    except Exception as err:
        return {"verified": False, "msg": str(err), "status": 400}

    return {"verified": True}

def begin_authentication(user_id: str, allow_credentials: list[PublicKeyCredentialDescriptor]) -> tuple[str|dict, bytes]:

    options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.PREFERRED,
    )   
    challenge = options.challenge
    return options_to_json(options), challenge

def finish_authentication(
    credential: dict,
    expected_challenge: bytes,
    *,
    public_key: bytes,
    sign_count: int,
) -> VerifiedAuthentication:
    try:
        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
            credential_public_key=public_key,
            credential_current_sign_count=sign_count,
            require_user_verification=True,
        )
    except Exception as err:
        return {"verified": False, "msg": str(err), "status": 400}

    return verification
