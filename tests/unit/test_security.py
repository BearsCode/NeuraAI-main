from backend.app.core.security import verify_password


def test_verify_password_returns_false_for_unknown_legacy_hash() -> None:
    legacy_hash = "39180ed21d4e9c8ba0fed7af28fbfb1a:260d129b7244e1d811d97e670e4b4402e0452396de715972510a981ed96774cb"

    assert verify_password("LocalAdmin12345", legacy_hash) is False
