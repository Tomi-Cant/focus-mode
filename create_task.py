# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025   
import subprocess
import sys
from pathlib import Path
from tkinter import messagebox
import helper_funcs
from target_edit import FocusModeUI

def create_scheduled_task(
    task_name: str,
    script_path: str,
    script_args: str = "",
):
    """
    Creates a Windows scheduled task that:
      - Triggers on logon AND daily at 12:00 AM
      - Runs pythonw/python.exe with the script as the action
      - Starts only on AC power, but does NOT stop if unplugged
      - Allows on-demand run, starts ASAP if a run was missed,
        retries every 1 min up to 20 times on failure
      - Has a 1-day execution time limit and force-kills if still running
      - Won't start a new instance if one is already running
    """
    
    
    xml_content = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Runs {Path(script_path).name} on logon and daily at 12 AM</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
    <CalendarTrigger>
      <StartBoundary>2026-08-25T00:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>true</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>true</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>P1D</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>20</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>"{script_path}" {script_args}</Command>
      <Arguments></Arguments>
    </Exec>
  </Actions>
</Task>'''


    # schtasks requires the XML file to be UTF-16 encoded
    xml_path = Path.cwd() / f"{task_name}.xml"
    xml_path.write_text(xml_content, encoding="utf-16")

    cmd = [
        "schtasks", "/create",
        "/tn", task_name,
        "/xml", str(xml_path),
        "/f",  # overwrite if it already exists
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)

    if result.returncode != 0:
        print(f"Failed to create task '{task_name}'.")
        if messagebox.askokcancel("Fatal Error!", f"Something has gone horribly wrong with setup. Please contact support at 'focusedupofficial@gmail.com' with the following error:\n\n{result.stderr}"):
            helper_funcs.contact_support()
        sys.exit(1)

    xml_path.unlink(missing_ok=True)  # clean up the temp XML
    return result.returncode == 0


if __name__ == "__main__":
    # Example usage
    create_scheduled_task(
        task_name="FocusModeTask1",
        script_path=f"{Path.cwd()}\\main.exe"
    )