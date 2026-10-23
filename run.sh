#!/usr/bin/env bash
set -euo pipefail

uv sync
uv run pytest
uv run scaled-engine
