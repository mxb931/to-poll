#!/usr/bin/env python3

import argparse
import sys
import json
import os
import hashlib
import re
import requests
from pathlib import Path
from typing import List, Dict, Optional

# ── Terminal formatting ────────────────────────────────────────────────────
class Colors:
    NORMAL = '\033[0m'
    BOLD = '\033[1m'
    HIGHLIGHT = '\033[7m'

N = Colors.NORMAL
B = Colors.BOLD
BG = Colors.HIGHLIGHT

# Valid applications
APPS = [
    "IDN", "UPD", "PhoenixC", "CUPN", "STORE", "PARAM", "Volume", "XCDS", 
    "APPS", "QCDS", "DXGROUP", "EDIACCT", "Cust", "MSAVEND", 
    "SizeCodeMaintenance", "MfgMaintenance", "PRICE-1.0", "PRICE-2.0", 
    "ProductMaintenance", "storeStaffing", "SYSCTL", "TinterVersion", "DNRETURN"
]

# ── Output helpers ────────────────────────────────────────────────────────
CURL_STATUS = ""
CURL_BODY = ""

def ok(msg: str):
    print(f"  {B}[OK]{N}   {msg}")

def fail(msg: str):
    print(f"  {B}[FAIL]{N} {msg}", file=sys.stderr)

def warn(msg: str):
    print(f"  {B}[WARN]{N} {msg}")

def step(num: int, msg: str):
    print(f"\n{BG} Step {num}: {msg} {N}")

def print_response(body: str):
    if not body:
        print("  (empty response)", file=sys.stderr)
        return
    
    # Try to extract message field first if JSON
    try:
        data = json.loads(body)
        if isinstance(data, dict) and "message" in data:
            print(f"  {B}Message:{N} {data['message']}", file=sys.stderr)
    except:
        pass
    
    # Try to pretty-print JSON
    print("  " + "-" * 28, file=sys.stderr)
    try:
        data = json.loads(body)
        pretty = json.dumps(data, indent=2)
        for line in pretty.split('\n'):
            print(f"  {line}", file=sys.stderr)
    except:
        # Fall back to stripping HTML tags
        cleaned = re.sub(r'<[^>]*>', '', body)
        for line in cleaned.split('\n'):
            if line.strip():
                print(f"  {line}", file=sys.stderr)
    
    print("  " + "-" * 28, file=sys.stderr)

def do_curl(method: str, url: str, headers: Dict = None, data: str = None, 
            files: Dict = None, auth: tuple = None, verify_ssl: bool = False) -> tuple:
    """Make HTTP request and return (status_code, response_body)"""
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, auth=auth, verify=verify_ssl)
        elif method == "POST":
            resp = requests.post(url, headers=headers, data=data, files=files, 
                               auth=auth, verify=verify_ssl)
        elif method == "PUT":
            resp = requests.put(url, headers=headers, data=data, auth=auth, 
                              verify=verify_ssl)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return resp.status_code, resp.text
    except Exception as e:
        fail(f"Request failed: {e}")
        return 0, str(e)

def usage(prog_name: str):
    print(f"\nUsage Documentation for {B}{prog_name}{N}")
    print(f"{B}The following command line switches indicate the environment{N}")
    print(f"{BG}-p{N}  --Sets Production")
    print(f"{BG}-q{N}  --Sets QA")
    print(f"{BG}-d{N}  --Sets Development *Default")
    print(f"{B}Required parameters{N}")
    print(f"{BG}-a{N}  --Sets the application name")
    print(f"{BG}-f{N}  --Sets the file name.  Repeatable for multiple files")
    print(f"{BG}-s{N}  --Sets the store list, comma delimited or filename with comma delimited")
    print(f"{BG}-U{N}  --Username for authentication")
    print(f"{BG}-P{N}  --Password for authentication")
    print(f"{B}Optional parameters{N}")
    print(f"{BG}-x{N}  --Expires, integer, number of days from today")
    print(f"{BG}-t{N}  --Run After Date, date format YYYY-MM-DD.")
    print(f"{BG}-r{N}  --Prerequisite")
    print(f"{BG}-e{N}  --Request to fix works with Fix Option")
    print(f"{BG}-o{N}  --Fix Option: rescind, replace, prereq, equivalent_to")
    print("-" * 66)
    print("-help  --Displays this help")
    print(f"Example : {B}{prog_name} -q -a SYSCTL -f updt-sysctl.xml -s 9959,9953 -U myuser -P mypass{N}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(add_help=False)
    
    # Environment
    parser.add_argument('-d', '--dev', action='store_true', help='Development (default)')
    parser.add_argument('-q', '--qa', action='store_true', help='QA')
    parser.add_argument('-p', '--prod', action='store_true', help='Production')
    
    # Required
    parser.add_argument('-a', '--app', required=False, help='Application name')
    parser.add_argument('-f', '--file', action='append', dest='files', help='File(s) to upload (repeatable)')
    parser.add_argument('-s', '--stores', required=False, help='Store list (comma-delimited or filename)')
    parser.add_argument('-U', '--user', required=False, help='Username')
    parser.add_argument('-P', '--password', required=False, help='Password')
    
    # Optional
    parser.add_argument('-x', '--expires', help='Expires (days from today)')
    parser.add_argument('-t', '--afterdate', help='Run After Date (YYYY-MM-DD)')
    parser.add_argument('-r', '--prereq', help='Prerequisite')
    parser.add_argument('-e', '--reqtofix', help='Request to fix ID')
    parser.add_argument('-o', '--fixoption', help='Fix option: rescind, replace, prereq, equivalent_to')
    parser.add_argument('-h', '--help', action='store_true', help='Show help')
    
    args = parser.parse_args()
    
    # Handle help
    if args.help or len(sys.argv) == 1:
        usage(sys.argv[0])
        sys.exit(0)
    
    # Determine server
    server = "https://pollingdev.sherwin.com/polling"  # Default
    if args.qa:
        server = "https://pollingqa.sherwin.com/polling"
    elif args.prod:
        server = "https://polling.sherwin.com/polling"
    
    # Validate required parameters
    if not args.app:
        print(f"Require parameter {B}-a{N} missing")
        sys.exit(1)
    
    if args.app not in APPS:
        print(f"Invalid App: {B}{args.app}{N}")
        print("Valid Apps are:")
        print(f"{B}{' '.join(APPS)}{N}")
        sys.exit(1)
    
    if not args.files:
        print(f"Required parameter {B}-f{N} missing")
        sys.exit(1)
    
    # Validate files exist
    for file in args.files:
        if not os.path.isfile(file):
            print(f"Invalid file name {B}{file}{N}")
            sys.exit(1)
    
    if not args.stores:
        print(f"Required parameter {B}-s{N} missing")
        sys.exit(1)
    
    if not args.user:
        print(f"Required parameter {B}-U{N} missing")
        sys.exit(1)
    
    if not args.password:
        print(f"Required parameter {B}-P{N} missing")
        sys.exit(1)
    
    # Read stores from file if it's a file path
    stores = args.stores
    if os.path.isfile(stores):
        with open(stores, 'r') as f:
            stores = f.read().strip()
    
    # Format store list with quotes and commas
    stores_list = [f'"{s.strip()}"' for s in stores.split(',')]
    stores_formatted = ','.join(stores_list)
    
    # Show summary
    print("\n" + "=" * 50)
    print("Sending requests for")
    print("_" * 50)
    print(f"{BG}Server:{N} {server}")
    print(f"{BG}App:{N} {args.app}")
    for file in args.files:
        print(f"{BG}File:{N} {file}")
    print(f"{BG}Stores:{N} {stores_formatted}")
    print(f"{BG}Prereq:{N} {args.prereq or ''}")
    print(f"{BG}Expires:{N} {args.expires or ''}")
    print(f"{BG}Run After:{N} {args.afterdate or ''}")
    print(f"{BG}Fix Option:{N} {args.fixoption or ''}")
    print(f"{BG}Req to Fix:{N} {args.reqtofix or ''}")
    print()
    
    # Confirmation
    response = input("Are you sure? ")
    if response.lower() not in ['y', 'yes']:
        print("")
        sys.exit(2)
    print()
    
    # Setup auth
    auth = (args.user, args.password)
    headers = {"Accept": "application/json"}
    
    # Build optional parameters
    parms = {}
    if args.prereq:
        parms["afterSequence"] = args.prereq
    if args.expires:
        parms["expiration"] = args.expires
    if args.afterdate:
        parms["afterDate"] = args.afterdate
    if args.reqtofix:
        parms["fixRequestId"] = args.reqtofix
    if args.fixoption:
        parms["fixOption"] = args.fixoption
    
    # ── Step 1: Create request ─────────────────────────────────────────────
    string = f"{server}/v1/app/{args.app}"
    step(1, "Creating request")
    print(f"  POST {string}")
    
    status, body = do_curl("POST", string, headers=headers, auth=auth, verify_ssl=False)
    
    if status not in [200, 201]:
        fail(f"Failed to create request.  HTTP {status}")
        print_response(body)
        sys.exit(1)
    
    # Extract requestId
    try:
        data = json.loads(body)
        reqid = data.get("requestId")
    except:
        # Try regex fallback
        match = re.search(r'"requestId":"([^"]*)"', body)
        reqid = match.group(1) if match else None
    
    if not reqid:
        fail(f"Could not extract requestId from response.  HTTP {status}")
        print_response(body)
        sys.exit(1)
    
    ok(f"Request created.  ID: {B}{reqid}{N}")
    
    basestring = f"{server}/v1/{reqid}"
    ops = f"{basestring}/operations"
    str_endpoint = f"{basestring}/stores"
    
    # ── Step 2: Apply optional parameters ──────────────────────────────────
    if parms:
        step(2, "Applying request parameters")
        print(f"  PUT {basestring}")
        parms_json = json.dumps(parms)
        print(f"  Params: {parms_json}")
        
        status, body = do_curl("PUT", basestring, headers={**headers, "Content-Type": "application/json"},
                             data=parms_json, auth=auth, verify_ssl=False)
        
        if status != 200:
            fail(f"Failed to apply parameters.  HTTP {status}")
            print_response(body)
            sys.exit(1)
        
        ok("Parameters applied.")
    
    # ── Step 3: Upload file operations ────────────────────────────────────
    step(3, "Uploading file operations")
    for file_path in args.files:
        fn = os.path.basename(file_path)
        
        # Calculate SHA-1 checksum
        with open(file_path, 'rb') as f:
            md5 = hashlib.sha1(f.read()).hexdigest()
        
        print(f"  POST {ops}")
        print(f"  File: {file_path}  Checksum: {md5}")
        
        with open(file_path, 'rb') as f:
            files = {
                'blob': f,
                'filename': (None, fn),
                'checksum': (None, md5),
                'algorithm': (None, 'SHA-1'),
                'transforms': (None, 'null')
            }
            status, body = do_curl("POST", ops, headers=headers, files=files, 
                                 auth=auth, verify_ssl=False)
        
        if status != 201:
            fail(f"Failed to upload {fn}.  HTTP {status}")
            print_response(body)
            sys.exit(1)
        
        ok(f"Uploaded: {fn}")
    
    # ── Step 4: Set target stores ─────────────────────────────────────────
    step(4, "Setting target stores")
    
    if stores_formatted == '"all"':
        store_type = "chain"
    else:
        store_type = "store"
    
    print(f"  PUT {str_endpoint}")
    print(f"  Type: {store_type}  Stores: {stores_formatted}")
    
    store_data = json.dumps({
        "type": store_type,
        "data": json.loads(f"[{stores_formatted}]")
    })
    
    status, body = do_curl("PUT", str_endpoint, 
                         headers={**headers, "Content-Type": "application/json"},
                         data=store_data, auth=auth, verify_ssl=False)
    
    if status != 201:
        fail(f"Failed to set stores.  HTTP {status}")
        print_response(body)
        sys.exit(1)
    
    ok("Stores set.")
    
    # ── Step 5: Submit request ────────────────────────────────────────────
    step(5, "Submitting request")
    print(f"  POST {basestring}")
    
    status, body = do_curl("POST", basestring, headers=headers, auth=auth, verify_ssl=False)
    
    if status == 206:
        warn("Submitted, but not all stores accepted.  HTTP 206")
    elif status != 200:
        fail(f"Failed to submit request.  HTTP {status}")
        print_response(body)
        sys.exit(1)
    else:
        ok("Request submitted successfully.")
    
    print()
    print(f"{BG} Done {N}  Request ID: {B}{reqid}{N} submitted to {server}")
    print()

if __name__ == "__main__":
    main()
