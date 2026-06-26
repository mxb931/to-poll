#!/usr/bin/env python

import requests
import sys
from typing import Dict, Tuple

# Valid applications
APPS = [
    "IDN", "UPD", "PhoenixC", "CUPN", "STORE", "PARAM", "Volume", "XCDS", 
    "APPS", "QCDS", "DXGROUP", "EDIACCT", "Cust", "MSAVEND", 
    "SizeCodeMaintenance", "MfgMaintenance", "PRICE-1.0", "PRICE-2.0", 
    "ProductMaintenance", "storeStaffing", "SYSCTL", "TinterVersion", "DNRETURN"
]

# Fix options
FIX_OPTIONS = [
    "rescind", "replace", "prereq", "equivalent_to"
]


def build_server_url(environment: str) -> str:
    """Determine server URL based on environment"""
    if environment == "QA":
        return "https://pollingqa.sherwin.com/polling"
    elif environment == "Production":
        return "https://polling.sherwin.com/polling"
    else:  # Development (default)
        return "https://pollingdev.sherwin.com/polling"


def do_curl(method: str, url: str, headers: Dict = None, data: str = None, 
            files: Dict = None, auth: tuple = None, verify_ssl: bool = False) -> Tuple[int, str]:
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
        print(f"  [FAIL] Request failed: {e}", file=sys.stderr)
        return 0, str(e)
