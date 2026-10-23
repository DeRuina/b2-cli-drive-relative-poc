# B2 CLI (Windows): a drive-relative object name (`C:../x`) escapes the download directory

**What this proves (one sentence):** `b2 file download <uri> <directory>` names the local file after
the (attacker-chosen) remote object name, and on Windows a drive-relative name such as `C:../escape.txt`
passes the CLI's safety validator and is written **one level above** the directory the user chose.

**Why it matters:** the object name comes from the bucket (`x-bz-file-name`) — chosen by whoever can
write to a shared/public bucket, or by whoever hands the user a `b2id://` URI (the exact case the
directory mode exists for, "he might not know the name of the file"). From the usual
`%USERPROFILE%\Downloads` this reaches the per-user **Startup** folder, i.e. code execution at the next
logon. Since 4.7.0 the download command validates the name, but on Windows the validator only rejects a
drive letter **followed by a separator** (`C:\`, `C:/`); a drive-relative `C:..` with no separator slips
through, and there is no containment check after the `pathlib` join.

**What you need:** nothing for the root cause (runs on Linux in seconds). For the end-to-end Windows
write, a GitHub account — the proof runs on GitHub Actions `windows-latest`, no local Windows box.

## Two ways to see it

### 1. Root cause, locally, in seconds (any OS)
```
./run-local.sh
```
Installs `b2sdk` and runs the validator test. **3 cases FAIL** (`DID NOT RAISE ValueError` for
`C:file.txt`, `C:../file.txt`, and the Startup-folder name) while the `C:/` and `C:\` controls are
rejected — that gap is the bug.

### 2. End-to-end on real Windows (GitHub Actions)
Push this folder to a GitHub repo (or use **Run workflow**). `.github/workflows/poc.yml` checks out the
B2 CLI at the pinned commit `04697197` on `windows-latest` (Windows Server 2025), then:
- **STEP 1** runs the validator test → 3 FAIL (root cause);
- **STEP 2** uploads an object named `C:../escape.txt` to the in-process simulator and runs
  `b2 file download b2id://<id> <tmp>\downloads`, asserting nothing was written outside `downloads\`.
  The assertion **FAILS**: the file lands at `<tmp>\escape.txt`, one level above the chosen directory.

`windows-ci-proof-2026-10-17.txt` is the log from our own run of exactly this (b2 5.0.1.dev39+g04697197e,
Python 3.12.10, no account, in-process `raw_simulator`).

## Stages
| Stage | Expected |
|---|---|
| `run-local.sh` (Linux) | validator accepts `C:`, `C:..` → 3 FAIL, 3 control PASS |
| GH Actions STEP 1 (Windows) | same 3 FAIL |
| GH Actions STEP 2 (Windows) | `b2 file download` writes `escape.txt` **outside** the destination → assertion FAILS (the decisive line: `object written outside the destination: …\escape.txt`) |

## Cause and fix
- `b2sdk/_internal/utils/filesystem.py` `DRIVE_MATCHER` requires `[/\\]` after the colon, so `C:` /
  `C:..` are not caught; `console_tool.py` then does `output_directory / file_name` with no post-join
  containment check (the `sync` path has one via `os.path.commonpath`; the download command does not).
- Fix: reject any drive prefix (`^[A-Za-z]:`), or reject `:` on Windows entirely; AND after the join
  require `output_filepath.resolve().is_relative_to(output_directory.resolve())`, independent of the regex.

## Files
- `run-local.sh` — Linux root-cause check
- `.github/workflows/poc.yml` — end-to-end Windows proof on GitHub Actions
- `tests/` — the two test files the workflow runs
- `windows-ci-proof-2026-10-17.txt` — our own Windows Actions run log
