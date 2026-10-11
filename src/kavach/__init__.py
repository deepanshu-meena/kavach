"""Kavach - an environmental safety copilot for Delhi's outdoor workers."""

__version__ = "0.1.0"

try:  # load a local .env if python-dotenv is installed (not needed on Lambda)
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass
