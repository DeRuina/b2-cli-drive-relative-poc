######################################################################
#
# File: test/unit/console_tool/test_download_drive_relative.py
#
# Candidate-finding test (bounty review 2026-10-15), WINDOWS ONLY.
# `b2 file download b2id://<id> <directory>` with an object named
# ``C:../escape.txt`` writes the file one level ABOVE <directory>.
# Uses the in-process raw_simulator (no network, no B2 account).
#
######################################################################
import platform

import pytest


@pytest.mark.skipif(
    platform.system() != 'Windows',
    reason='drive-relative names only resolve as paths on Windows',
)
@pytest.mark.parametrize('remote_name', ['C:../escape.txt'])
def test_download_file_by_uri__directory_rejects_drive_relative_name(
    b2_cli, api_bucket, tmp_path, remote_name
):
    uploaded_file = api_bucket.upload_bytes(b'hello world', remote_name)
    output_directory = tmp_path / 'downloads'
    output_directory.mkdir()

    # On current code the command SUCCEEDS (status 0); after the fix it must fail with
    # "File names containing ... are not supported" and status 1 like the existing
    # test_download_file_by_uri__directory_rejects_unsupported_server_name.
    b2_cli.run(
        [
            'file',
            'download',
            '--no-progress',
            f'b2id://{uploaded_file.id_}',
            str(output_directory),
        ],
        expected_stderr=None,
    )

    escaped = tmp_path / 'escape.txt'  # one level above the chosen directory
    # EXPECTED (secure): nothing written outside output_directory.
    # ACTUAL on master 04697197 (Python 3.12+): escaped.exists() is True.
    assert not escaped.exists(), f'object written outside the destination: {escaped}'
    assert list(output_directory.iterdir()) == []
