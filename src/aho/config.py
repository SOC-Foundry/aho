"""Configuration and validation for aho."""
import re


IAO_VERSION_REGEX = re.compile(r"^\d+\.\d+\.\d+$")


def validate_iteration_version(version: str) -> None:
    """Raise ValueError if version string is not exactly three octets.

    aho versioning is locked to X.Y.Z. The Z field is the iteration
    run number, not a patch or minor. Four-octet versioning is a
    pattern-match error from kjtcom and must be rejected.
    """
    if not isinstance(version, str):
        raise ValueError(f"Version must be string, got {type(version).__name__}")
    if not IAO_VERSION_REGEX.match(version):
        raise ValueError(
            f"Iteration version '{version}' does not match X.Y.Z three-octet format. "
            f"aho versioning is locked to three octets; see aho-G107 in gotcha registry."
        )
