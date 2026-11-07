# Step 10 sampler process audit

## Existing terminators and exits

- [main.py](/C:/Banjoko/Python/focus_mode/main.py) calls `sys.exit()` when no time groups remain, and for the default finish action.
- [main.py](/C:/Banjoko/Python/focus_mode/main.py) passes functions that call `sys.exit()` to finish actions.
- [proc_funcs.py](/C:/Banjoko/Python/focus_mode/proc_funcs.py) calls `psutil.Process.kill()` for configured programs.
- No `os._exit`, `taskkill`, scheduled-task `/end`, or image-name shell termination was found.
- [StartProcess.bat](/C:/Banjoko/Python/focus_mode/StartProcess.bat) restarts the enforcer executable only; it does not terminate processes by image name.

## Process-name cleanup

- The enforcer kills only names configured in its time-group blacklist through `window_to_process.process_search()`.
- `FocusUpSampler.exe` is now protected in [proc_funcs.py](/C:/Banjoko/Python/focus_mode/proc_funcs.py), including window-close handling, so blacklist cleanup cannot match it.
- No cleanup code names `python.exe` or restarts by `python.exe`.

## Existing responsibilities in running components

- `main.py` exits its loop after its time groups finish, so it cannot own always-running daily work.
- Rollover safety checks are added at startup in both the enforcer and UI.
- Aggregation and suggestion generation belong to the usage scheduler/sampler side.
- `manual_buffer.check_day_rollover()` is not called from the enforcer loop.

## Scheduled-task template reuse

The existing task XML supplies the correct XML framing and highest-privilege principal. It must not be reused unchanged because it has dual logon/daily triggers, battery restrictions, a P1D limit, and `AllowHardTerminate`. The separate sampler task uses a logon-only trigger and the requested sampler settings.
