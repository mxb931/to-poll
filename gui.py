#!/usr/bin/env python

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import json
import hashlib
import re
from datetime import datetime
from typing import List, Dict, Callable, Optional

# Import polling functions
from to_poll_core import (
    APPS, do_curl, build_server_url, FIX_OPTIONS
)

class TextRedirector:
    """Redirect print output to a tkinter Text widget"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
    
    def write(self, message: str):
        if message:
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.insert(tk.END, message)
            self.text_widget.see(tk.END)
            self.text_widget.config(state=tk.DISABLED)
    
    def flush(self):
        pass


class PollingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("To-Poll GUI")
        self.root.geometry("900x650")
        
        # Store for form values
        self.selected_files = []
        
        # Create main frame with paned window for resizing
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ── Form Frame ─────────────────────────────────────────────────────
        form_frame = tk.LabelFrame(main_frame, text="Polling Request Form", font=("Helvetica", 10, "bold"))
        form_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Form fields frame (no scrolling)
        scrollable_frame = tk.Frame(form_frame)
        scrollable_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Row counter for layout
        row = 0
        
        # ── Environment ────────────────────────────────────────────────────
        tk.Label(scrollable_frame, text="Environment:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.env_var = tk.StringVar(value="Development")
        env_combo = tk.OptionMenu(scrollable_frame, self.env_var, "Development", "QA", "Production")
        env_combo.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        # ── Application ────────────────────────────────────────────────────
        tk.Label(scrollable_frame, text="Application *:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.app_var = tk.StringVar()
        app_combo = tk.OptionMenu(scrollable_frame, self.app_var, *APPS)
        app_combo.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        # ── Files ──────────────────────────────────────────────────────────
        tk.Label(scrollable_frame, text="File(s) *:").grid(row=row, column=0, sticky="nw", padx=5, pady=2)
        files_frame = tk.Frame(scrollable_frame)
        files_frame.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        self.files_text = tk.Entry(files_frame, width=40, state="readonly")
        self.files_text.pack(side="left", padx=(0, 5))
        
        tk.Button(files_frame, text="Browse", command=self.browse_files).pack(side="left")
        row += 1
        
        # ── Stores ─────────────────────────────────────────────────────────
        tk.Label(scrollable_frame, text="Store List *:").grid(row=row, column=0, sticky="nw", padx=5, pady=2)
        stores_frame = tk.Frame(scrollable_frame)
        stores_frame.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        self.stores_text = tk.Entry(stores_frame, width=40)
        self.stores_text.pack(side="left", padx=(0, 5))
        
        tk.Button(stores_frame, text="Import CSV", command=self.import_csv).pack(side="left")
        row += 1
        
        # ── Username ───────────────────────────────────────────────────────
        tk.Label(scrollable_frame, text="Username *:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.user_var = tk.StringVar()
        tk.Entry(scrollable_frame, textvariable=self.user_var, width=40).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        # ── Password ───────────────────────────────────────────────────────
        tk.Label(scrollable_frame, text="Password *:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.pass_var = tk.StringVar()
        tk.Entry(scrollable_frame, textvariable=self.pass_var, show="*", width=40).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        # ── Expires ────────────────────────────────────────────────────────
        tk.Label(scrollable_frame, text="Expires (days):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.expires_var = tk.StringVar()
        tk.Entry(scrollable_frame, textvariable=self.expires_var, width=40).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        # ── Run After Date ─────────────────────────────────────────────────
        tk.Label(scrollable_frame, text="Run After Date (YYYY-MM-DD):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.date_var = tk.StringVar()
        tk.Entry(scrollable_frame, textvariable=self.date_var, width=40).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        # ── Prerequisite ───────────────────────────────────────────────────
        tk.Label(scrollable_frame, text="Prerequisite:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.prereq_var = tk.StringVar()
        tk.Entry(scrollable_frame, textvariable=self.prereq_var, width=40).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        # ── Request to Fix ─────────────────────────────────────────────────
        tk.Label(scrollable_frame, text="Request to Fix:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.reqtofix_var = tk.StringVar()
        reqtofix_entry = tk.Entry(scrollable_frame, textvariable=self.reqtofix_var, width=40)
        reqtofix_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        # Bind change event to enable/disable Fix Option
        reqtofix_entry.bind('<KeyRelease>', self.on_reqtofix_change)
        row += 1
        
        # ── Fix Option ─────────────────────────────────────────────────────
        tk.Label(scrollable_frame, text="Fix Option:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.fixopt_var = tk.StringVar()
        self.fixopt_combo = tk.OptionMenu(scrollable_frame, self.fixopt_var, *FIX_OPTIONS)
        self.fixopt_combo.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        self.fixopt_combo.config(state=tk.DISABLED)
        row += 1
        
        # ── Buttons ────────────────────────────────────────────────────────
        button_frame = tk.Frame(scrollable_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10, sticky="ew")
        
        submit_btn = tk.Button(button_frame, text="Submit", command=self.submit_form, 
                               bg="#4CAF50", fg="black", font=("Helvetica", 11, "bold"),
                               activebackground="#45a049", activeforeground="black", 
                               relief=tk.FLAT, bd=0, padx=10, pady=5, highlightthickness=0)
        submit_btn.pack(side="left", padx=5)
        
        clear_btn = tk.Button(button_frame, text="Clear", command=self.clear_form,
                              bg="#2196F3", fg="black", font=("Helvetica", 11, "bold"),
                              activebackground="#0b7dda", activeforeground="black",
                              relief=tk.FLAT, bd=0, padx=10, pady=5, highlightthickness=0)
        clear_btn.pack(side="left", padx=5)
        
        exit_btn = tk.Button(button_frame, text="Exit", command=self.root.quit,
                             bg="#f44336", fg="black", font=("Helvetica", 11, "bold"),
                             activebackground="#da190b", activeforeground="black",
                             relief=tk.FLAT, bd=0, padx=10, pady=5, highlightthickness=0)
        exit_btn.pack(side="left", padx=5)
        
        # ── Output Frame ───────────────────────────────────────────────────
        output_frame = tk.LabelFrame(main_frame, text="Output", font=("Helvetica", 10, "bold"))
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=8, width=80, state=tk.DISABLED)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def browse_files(self):
        """Open file browser to select multiple files"""
        files = filedialog.askopenfilenames(title="Select operation file(s)")
        if files:
            self.selected_files = list(files)
            self.files_text.config(state=tk.NORMAL)
            self.files_text.delete(0, tk.END)
            self.files_text.insert(0, f"{len(files)} file(s) selected")
            self.files_text.config(state="readonly")
    
    def import_csv(self):
        """Import store list from CSV file"""
        file = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if file:
            try:
                with open(file, 'r') as f:
                    content = f.read().strip()
                    self.stores_text.delete(0, tk.END)
                    self.stores_text.insert(0, content)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read CSV: {e}")
    
    def on_reqtofix_change(self, event=None):
        """Enable/disable Fix Option based on Request to Fix value"""
        if self.reqtofix_var.get().strip():
            self.fixopt_combo.config(state=tk.NORMAL)
        else:
            self.fixopt_combo.config(state=tk.DISABLED)
    
    def validate_form(self) -> tuple[bool, str]:
        """Validate form fields. Returns (valid, error_message)"""
        if not self.app_var.get():
            return False, "Application is required"
        
        if not self.selected_files:
            return False, "At least one file is required"
        
        # Validate files exist
        for file in self.selected_files:
            if not os.path.isfile(file):
                return False, f"File not found: {file}"
        
        if not self.stores_text.get():
            return False, "Store list is required"
        
        if not self.user_var.get():
            return False, "Username is required"
        
        if not self.pass_var.get():
            return False, "Password is required"
        
        # Validate expires if provided
        if self.expires_var.get():
            try:
                int(self.expires_var.get())
            except ValueError:
                return False, "Expires must be an integer (days)"
        
        # Validate date if provided (will be validated by DateEntry widget)
        
        return True, ""
    
    def clear_form(self):
        """Reset all form fields to defaults"""
        self.env_var.set("Development")
        self.app_var.set("")
        self.selected_files = []
        self.files_text.config(state=tk.NORMAL)
        self.files_text.delete(0, tk.END)
        self.files_text.config(state="readonly")
        self.stores_text.delete(0, tk.END)
        self.user_var.set("")
        self.pass_var.set("")
        self.expires_var.set("")
        self.date_var.set("")
        self.prereq_var.set("")
        self.reqtofix_var.set("")
        self.fixopt_var.set("")
        self.fixopt_combo.config(state=tk.DISABLED)
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def submit_form(self):
        """Validate and submit the form"""
        # Validate form
        valid, error_msg = self.validate_form()
        if not valid:
            messagebox.showerror("Validation Error", error_msg)
            return
        
        # Production confirmation
        if self.env_var.get() == "Production":
            response = messagebox.askokcancel(
                "Production Confirmation",
                "You are about to submit to PRODUCTION.\n\nAre you sure you want to continue?"
            )
            if not response:
                return
        
        # Clear output
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        # Redirect stdout/stderr to output text
        import sys
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = TextRedirector(self.output_text)
        sys.stderr = TextRedirector(self.output_text)
        
        try:
            # Run the polling submission
            self.run_polling_submission()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    def run_polling_submission(self):
        """Execute the polling submission with form values"""
        # Determine server
        server = build_server_url(self.env_var.get())
        
        app = self.app_var.get()
        files = self.selected_files
        stores = self.stores_text.get()
        user = self.user_var.get()
        password = self.pass_var.get()
        
        # Read stores from file if it's a file path
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
        print(f"Server: {server}")
        print(f"App: {app}")
        for file in files:
            print(f"File: {file}")
        print(f"Stores: {stores_formatted}")
        if self.prereq_var.get():
            print(f"Prereq: {self.prereq_var.get()}")
        if self.expires_var.get():
            print(f"Expires: {self.expires_var.get()}")
        if self.date_var.get():
            print(f"Run After: {self.date_var.get()}")
        if self.fixopt_var.get():
            print(f"Fix Option: {self.fixopt_var.get()}")
        if self.reqtofix_var.get():
            print(f"Req to Fix: {self.reqtofix_var.get()}")
        print()
        
        # Setup auth
        auth = (user, password)
        headers = {"Accept": "application/json"}
        
        # Build optional parameters
        parms = {}
        if self.prereq_var.get():
            parms["afterSequence"] = self.prereq_var.get()
        if self.expires_var.get():
            parms["expiration"] = self.expires_var.get()
        if self.date_var.get():
            parms["afterDate"] = self.date_var.get()
        if self.reqtofix_var.get():
            parms["fixRequestId"] = self.reqtofix_var.get()
        if self.fixopt_var.get():
            parms["fixOption"] = self.fixopt_var.get()
        
        # ── Step 1: Create request ─────────────────────────────────────────
        string = f"{server}/v1/app/{app}"
        self.print_step(1, "Creating request")
        print(f"  POST {string}")
        
        status, body = do_curl("POST", string, headers=headers, auth=auth, verify_ssl=False)
        
        if status not in [200, 201]:
            self.print_fail(f"Failed to create request.  HTTP {status}")
            self.print_response(body)
            return
        
        # Extract requestId
        try:
            data = json.loads(body)
            reqid = data.get("requestId")
        except:
            # Try regex fallback
            match = re.search(r'"requestId":"([^"]*)"', body)
            reqid = match.group(1) if match else None
        
        if not reqid:
            self.print_fail(f"Could not extract requestId from response.  HTTP {status}")
            self.print_response(body)
            return
        
        self.print_ok(f"Request created.  ID: {reqid}")
        
        basestring = f"{server}/v1/{reqid}"
        ops = f"{basestring}/operations"
        str_endpoint = f"{basestring}/stores"
        
        # ── Step 2: Apply optional parameters ──────────────────────────────
        if parms:
            self.print_step(2, "Applying request parameters")
            print(f"  PUT {basestring}")
            parms_json = json.dumps(parms)
            print(f"  Params: {parms_json}")
            
            status, body = do_curl("PUT", basestring, headers={**headers, "Content-Type": "application/json"},
                                 data=parms_json, auth=auth, verify_ssl=False)
            
            if status != 200:
                self.print_fail(f"Failed to apply parameters.  HTTP {status}")
                self.print_response(body)
                return
            
            self.print_ok("Parameters applied.")
        
        # ── Step 3: Upload file operations ────────────────────────────────
        self.print_step(3, "Uploading file operations")
        for file_path in files:
            fn = os.path.basename(file_path)
            
            # Calculate SHA-1 checksum
            with open(file_path, 'rb') as f:
                md5 = hashlib.sha1(f.read()).hexdigest()
            
            print(f"  POST {ops}")
            print(f"  File: {file_path}  Checksum: {md5}")
            
            with open(file_path, 'rb') as f:
                files_dict = {
                    'blob': f,
                    'filename': (None, fn),
                    'checksum': (None, md5),
                    'algorithm': (None, 'SHA-1'),
                    'transforms': (None, 'null')
                }
                status, body = do_curl("POST", ops, headers=headers, files=files_dict, 
                                     auth=auth, verify_ssl=False)
            
            if status != 201:
                self.print_fail(f"Failed to upload {fn}.  HTTP {status}")
                self.print_response(body)
                return
            
            self.print_ok(f"Uploaded: {fn}")
        
        # ── Step 4: Set target stores ─────────────────────────────────────
        self.print_step(4, "Setting target stores")
        
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
            self.print_fail(f"Failed to set stores.  HTTP {status}")
            self.print_response(body)
            return
        
        self.print_ok("Stores set.")
        
        # ── Step 5: Submit request ────────────────────────────────────────
        self.print_step(5, "Submitting request")
        print(f"  POST {basestring}")
        
        status, body = do_curl("POST", basestring, headers=headers, auth=auth, verify_ssl=False)
        
        if status == 206:
            self.print_warn("Submitted, but not all stores accepted.  HTTP 206")
        elif status != 200:
            self.print_fail(f"Failed to submit request.  HTTP {status}")
            self.print_response(body)
            return
        else:
            self.print_ok("Request submitted successfully.")
        
        print()
        print(f"Done - Request ID: {reqid} submitted to {server}")
        print()
    
    def print_ok(self, msg: str):
        """Print [OK] message"""
        print(f"  [OK]   {msg}")
    
    def print_fail(self, msg: str):
        """Print [FAIL] message"""
        print(f"  [FAIL] {msg}")
    
    def print_warn(self, msg: str):
        """Print [WARN] message"""
        print(f"  [WARN] {msg}")
    
    def print_step(self, num: int, msg: str):
        """Print step header"""
        print(f"\n Step {num}: {msg} ")
    
    def print_response(self, body: str):
        """Print API response"""
        if not body:
            print("  (empty response)")
            return
        
        # Try to extract message field first if JSON
        try:
            data = json.loads(body)
            if isinstance(data, dict) and "message" in data:
                print(f"  Message: {data['message']}")
        except:
            pass
        
        # Try to pretty-print JSON
        print("  " + "-" * 28)
        try:
            data = json.loads(body)
            pretty = json.dumps(data, indent=2)
            for line in pretty.split('\n'):
                print(f"  {line}")
        except:
            # Fall back to stripping HTML tags
            cleaned = re.sub(r'<[^>]*>', '', body)
            for line in cleaned.split('\n'):
                if line.strip():
                    print(f"  {line}")
        
        print("  " + "-" * 28)


def run_gui():
    """Launch the GUI application"""
    root = tk.Tk()
    gui = PollingGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    run_gui()
