"""aho.host - host-side primitives that the container does NOT carry.

The secrets broker, the run-container wrapper, and any future host-only tooling
live under this package. Container images do not need to import these modules
at runtime; importing them triggers no side-effects, but they reference paths
(${XDG_RUNTIME_DIR}, host secret store) that only resolve correctly on the
host where the broker runs.
"""
