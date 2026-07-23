from webauthn import (
    generate_registration_options,
    verify_registration_response,
    options_to_json,
    base64url_to_bytes,
    verify_authentication_response,
    generate_authentication_options
    
)
from webauthn.helpers.structs import (
    UserVerificationRequirement,
    AuthenticationCredential,
    PublicKeyCredentialDescriptor,
    VerifiedAuthentication
)


def begin_registration(user_name: str) -> tuple[dict, bytes]:
    options = generate_registration_options(
    rp_id="localhost",
    rp_name="FinFlow",
    user_name="alan",
)
    challenge = options.challenge
    return options_to_json(opVerifiedAuthenticationtions), challenge

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

def begin_authentication(user_id: str, allow_credentials: list[PublicKeyCredentialDescriptor]) -> tuple[str|dict, bytes]:

    options = generate_authentication_options(
        rp_id="localhost",
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
            expected_challenge=current_challenge,
            expected_rp_id=rp_id,
            expected_origin=origin,
            credential_public_key=user_credential["public_key"],
            credential_current_sign_count=user_credential["sign_count"],
            require_user_verification=True,
        )
    except Exception as err:
        return {"verified": False, "msg": str(err), "status": 400}

    return verification
