#!/usr/bin/env bash

set -x

LC_ALL=C.UTF-8 LANG=C.UTF-8 black --diff --check --exclude=doc .

