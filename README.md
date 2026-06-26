# to-poll

Utility for creating and submitting polling requests through the Polling API.

Available in two implementations:
- **Bash** (`to-poll.sh`) - Pure bash with curl
- **Python3** (`to-poll.py`) - Python3 with requests library

## What this script does

The script performs these steps:
1. Creates a request for an application.
2. Optionally applies request header parameters.
3. Uploads one or more operation files.
4. Sets target stores (or all stores).
5. Submits the request.

It prints step-by-step status with `[OK]`, `[WARN]`, and `[FAIL]` output to simplify troubleshooting.

## Requirements

### Bash version (`to-poll.sh`)
- Bash shell
- curl
- shasum
- python3 (used only for pretty-printing JSON error responses)
- Network access to the Polling API endpoints

### Python version (`to-poll.py`)
- Python 3.6+
- `requests` library
- Network access to the Polling API endpoints

Install the Python dependencies:
```bash
pip install requests
```

## Usage

### Bash version
```bash
./to-poll.sh [environment] -a <app> -f <file> [-f <file> ...] -s <store_list_or_file> -U <username> -P <password> [options]
```

### Python version
```bash
python3 to-poll.py [environment] -a <app> -f <file> [-f <file> ...] -s <store_list_or_file> -U <username> -P <password> [options]
```
Or with direct execution (if executable):
```bash
./to-poll.py [environment] -a <app> -f <file> [-f <file> ...] -s <store_list_or_file> -U <username> -P <password> [options]
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

### Bash version

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

### Python version

Single file:

```bash
python3 to-poll.py -q -a SYSCTL -f updt-sysctl.xml -s 9959,9953 -U myuser -P mypass
```

Multiple files:

```bash
python3 to-poll.py -d -a IDN -f op1.xml -f op2.xml -s stores.txt -U myuser -P mypass
```

All stores:

```bash
python3 to-poll.py -p -a PRICE-1.0 -f price-update.xml -s all -U myuser -P mypass
```

### Python GUI Mode

Launch the GUI application:

```bash
python3 to-poll.py -g
```

The GUI provides a user-friendly form with all available parameters:

**Required fields** (marked with `*`):
- **Application**: Dropdown menu of all supported applications
- **File(s)**: Browse button to select one or more operation files
- **Store List**: Text entry or import button to load stores from CSV
- **Username**: API authentication username
- **Password**: API authentication password (masked)

**Optional fields**:
- **Environment**: Dropdown (Development, QA, Production) - default is Development
- **Expires**: Number of days from today
- **Run After Date**: Date in YYYY-MM-DD format
- **Prerequisite**: Request ID for sequencing
- **Request to Fix**: Request ID to fix (enables Fix Option dropdown when filled)
- **Fix Option**: Dropdown (rescind, replace, prereq, equivalent_to) - only enabled when Request to Fix is filled

**Features**:
- **Submit button**: Validates form and submits the request. Values persist for reuse.
- **Clear button**: Resets all fields to defaults
- **Import CSV button**: Load store list from a CSV file (comma-delimited)
- **Production confirmation**: When submitting to Production, confirms with user before proceeding
- **Output display**: Scrolling text box shows all step-by-step output ([OK]/[WARN]/[FAIL] messages)
- **Reusable form**: After submit, form values remain so you can resubmit without re-entering data

## Setup for GUI Mode

The GUI mode requires Python 3.12+ with tkinter support. If you don't have the required environment:

### macOS (using Homebrew)

```bash
# Install Python with tkinter support
brew install python-tk@3.12

# Create a virtual environment
/usr/local/bin/python3.12 -m venv venv

# Activate the environment
source venv/bin/activate

# Install dependencies
pip install requests

# Run GUI mode
python to-poll.py -g
```

### Linux

```bash
# Install Python with tkinter
sudo apt-get install python3 python3-tk

# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install requests

# Run
python to-poll.py -g
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
