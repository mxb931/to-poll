# to-poll

Bash utility for creating and submitting polling requests through the Polling API.

## What this script does

The script performs these steps:
1. Creates a request for an application.
2. Optionally applies request header parameters.
3. Uploads one or more operation files.
4. Sets target stores (or all stores).
5. Submits the request.

It prints step-by-step status with `[OK]`, `[WARN]`, and `[FAIL]` output to simplify troubleshooting.

## Requirements

- Bash shell
- curl
- shasum
- python3 (used only for pretty-printing JSON error responses)
- Network access to the Polling API endpoints

## Usage

```bash
./to-poll.sh [environment] -a <app> -f <file> [-f <file> ...] -s <store_list_or_file> -U <username> -P <password> [options]
```

## Environment switches

- `-d` Development (default)
- `-q` QA
- `-p` Production

## Required arguments

- `-a <app>` Application name
- `-f <file>` Operation file (repeatable)
- `-s <stores>` Comma-delimited stores (example: `9959,9953`) or a file containing comma-delimited stores
- `-U <username>` API username
- `-P <password>` API password

## Optional arguments

- `-x <days>` Expiration in days from today
- `-t <YYYY-MM-DD>` Run-after date
- `-r <request_id>` Prerequisite request/sequence
- `-e <request_id>` Request to fix
- `-o <option>` Fix option (`rescind`, `replace`, `prereq`, `equivalent_to`)
- `-h` Help

## Examples

Single file:

```bash
./to-poll.sh -q -a SYSCTL -f updt-sysctl.xml -s 9959,9953 -U myuser -P mypass
```

Multiple files:

```bash
./to-poll.sh -d -a IDN -f op1.xml -f op2.xml -s stores.txt -U myuser -P mypass
```

All stores:

```bash
./to-poll.sh -p -a PRICE-1.0 -f price-update.xml -s all -U myuser -P mypass
```

## Troubleshooting

If the script fails, look at:

- The **step number** in output (where it failed)
- The **HTTP status code**
- The extracted **Message** field (when present)
- The formatted response body block shown under failures

Common issues:

- `HTTP 401/403`: credentials or permissions issue
- `HTTP 404`: wrong endpoint/environment or missing resource
- `Could not extract requestId`: server returned unexpected payload; inspect the printed raw/formatted response
- Upload failure in Step 3: verify file exists, checksum is valid, and content format is acceptable

## Security note

Credentials are provided via command line flags (`-U` and `-P`). Avoid sharing terminal history/screenshots with secrets visible.
