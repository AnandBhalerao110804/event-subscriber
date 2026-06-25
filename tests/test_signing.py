import hashlib
import hmac

from app.signing import sign_payload


def test_sign_payload_format():
    body = b'{"id":"evt-1","type":"order.created","payload":{"id":1}}'
    signature = sign_payload("top-secret", body)
    expected = hmac.new(b"top-secret", body, hashlib.sha256).hexdigest()
    assert signature == f"sha256={expected}"
