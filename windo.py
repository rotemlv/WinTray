import sys
import os
import subprocess

"""
In order to avoid showing the powershell console for a split-second
I used the only working solution I found which is described here:
https://stackoverflow.com/questions/2396271/how-to-supress-powershell-window-when-using-the-file-option
"""

st_inf = subprocess.STARTUPINFO()
st_inf.dwFlags = st_inf.dwFlags | subprocess.STARTF_USESHOWWINDOW


def call_powershell_cmd(cmd):
    completed = subprocess.run(["powershell", "-Command", cmd], capture_output=True, startupinfo=st_inf)
    return completed


def change_display_off_timer(time_in_minutes):
    return call_powershell_cmd(f"Powercfg /Change monitor-timeout-ac {time_in_minutes}")


def change_pc_sleep_timer(time_in_minutes):
    raise NotImplementedError()


# @might(definitely)-require-admin-priv
def exclude_antivirus_folder(folder):
    raise NotImplementedError()


def main():
    ret = change_display_off_timer(60)
    print(f"{ret=}")


if __name__ == '__main__':
    main()
