"""
Contains version information about package
"""
import os

__version__ = os.environ.get(
    "PACKAGE_VERSION",
    os.environ.get(
        "CI_COMMIT_TAG",
        os.environ.get("GITHUB_REF_NAME", os.environ.get("VERSION", "0.1-dev")),
    ),
)
