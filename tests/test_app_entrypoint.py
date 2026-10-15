import pytest
from app import build_parser


def test_app_argument_parser():
    parser = build_parser()
    args = parser.parse_args(["--port", "9000", "--host", "0.0.0.0", "--no-browser"])
    assert args.port == 9000
    assert args.host == "0.0.0.0"
    assert args.no_browser is True


def test_app_argument_defaults():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.port == 8000
    assert args.host == "127.0.0.1"
    assert args.no_browser is False
