#!/usr/bin/env bash
# Linux quick-check of the ROOT CAUSE (seconds, no Windows needed): the shared
# b2sdk validator accepts drive-relative Windows names that have no separator
# after the drive letter. The end-to-end write is Windows-only — run the
# GitHub Actions workflow (.github/workflows/poc.yml) for that.
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
./.venv/bin/pip install -q "b2sdk==2.13.1" pytest
echo "== validator test (3 cases must FAIL = the bug: C:, C:.. accepted) =="
./.venv/bin/python -m pytest tests/test_filesystem_drive_relative.py -v || true
echo
echo "The 3 'DID NOT RAISE ValueError' failures above ARE the finding:"
echo "  validate_b2_file_name_as_path accepts C:file.txt / C:../file.txt while rejecting C:/ and C:\\."
echo "On Windows, 'output_dir / \"C:../escape.txt\"' then resolves above output_dir — see the GH Actions run."
