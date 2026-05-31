#!/usr/bin/env fish
# bin/aho-machine-bootstrap.fish - wrapper for the root install.fish
# v1.0.0

set -l project_root (dirname (dirname (realpath (status filename))))
exec $project_root/install.fish $argv
