# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025
import json
import subprocess
import vars
subprocess.run(["pip","install", "-r","requirements.txt"], creationflags=subprocess.CREATE_NO_WINDOW)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from tkinter import messagebox, filedialog
import webbrowser
from pathlib import Path
import create_task
import sys
import target_edit

class DummyStream:
    def write(self, data): pass
    def flush(self): pass

if sys.stdout is None:
    sys.stdout = DummyStream()
if sys.stderr is None:
    sys.stderr = DummyStream()
    
PUBLIC_KEY_HEX = "2aa3b0cd6993482ed51a9b5e10004eb601cda72aaae88fad360efc95aa634ad7"
def verify_license(license_path: str) -> dict | None:
    
    try: 
        if not Path(license_path).is_file():
          
            messagebox.showinfo("License Verification", "Please select your license file.")
            extern_license_path = filedialog.askopenfilename(initialdir=vars.rootdir, title="Select License File", filetypes=[("License Files", "*.lic")])
            with open(extern_license_path, "r") as f:
                license_file = json.load(f)
            with open(license_path, "w") as f:
                json.dump(license_file, f)  # Copy the license file if not found
                
            
        with open(license_path, "r") as f:
            license_file = json.load(f)

        payload = bytes.fromhex(license_file["data"])
        signature = bytes.fromhex(license_file["signature"])

        public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUBLIC_KEY_HEX))
        public_key.verify(signature, payload)  # raises if invalid
        if license_file.get("task_made", False) :
            
            create_task.create_scheduled_task(
                task_name="FocusedUpTask",
                script_path=f"{vars.rootdir}\\main.exe"
            )
            license_file["task_made"] = True
            with open(license_path, "w") as f:
                json.dump(license_file, f) 
        target_edit.main()

    except (InvalidSignature, FileNotFoundError, KeyError, ValueError, json.JSONDecodeError):
        if messagebox.askokcancel("License not found", "Invalid or missing license. Visit the website to obtain a valid license, or check your email if you have already purchased one."):
            webbrowser.open("https://tomican.gumroad.com/l/focusedup")  

# Usage in your app's startup:
if __name__ == "__main__":
    result = verify_license("license.lic")
  