######################################################################
#
# File: test/unit/utils/test_filesystem_drive_relative.py
#
# Candidate-finding test (bounty review 2026-10-15): drive-relative Windows
# names such as ``C:../x`` pass ``validate_b2_file_name_as_path`` although
# ``C:\x`` and ``C:/x`` are rejected, and pathlib joins them outside the
# chosen directory.
#
######################################################################
import pathlib

import pytest

from b2sdk._internal.utils import filesystem


@pytest.fixture
def windows(monkeypatch):
    monkeypatch.setattr(filesystem, '_IS_WINDOWS', True)


@pytest.mark.parametrize('file_name', ['C:/file.txt', 'C:\\file.txt'])
def test_drive_with_separator_is_rejected(windows, file_name):
    with pytest.raises(ValueError, match=r'drive letters'):
        filesystem.validate_b2_file_name_as_path(file_name)


@pytest.mark.parametrize(
    'file_name',
    [
        'C:file.txt',  # drive-relative: current directory of drive C
        'C:../file.txt',  # drive-relative + parent: one level above the directory
        'C:../AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/evil.bat',
    ],
)
def test_drive_relative_name_passes_validator(windows, file_name):
    # EXPECTED (secure): ValueError.  ACTUAL: returns None -> the name is accepted.
    with pytest.raises(ValueError):
        filesystem.validate_b2_file_name_as_path(file_name)


def test_drive_relative_name_escapes_output_directory():
    # What console_tool.get_local_output_filepath does: output_directory / file_name
    same_drive = pathlib.PureWindowsPath('C:/Users/victim/Downloads') / 'C:../AppData/evil.bat'
    other_drive = pathlib.PureWindowsPath('D:/downloads') / 'C:../evil.bat'
    assert str(same_drive) == 'C:\\Users\\victim\\Downloads\\..\\AppData\\evil.bat'
    assert str(other_drive) == 'C:..\\evil.bat'
    # neither path stays under the directory the user chose
    assert not str(same_drive).startswith('C:\\Users\\victim\\Downloads\\AppData')
    assert not str(other_drive).startswith('D:\\downloads')
