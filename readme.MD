# Windows Tray controller
I wrote this app mainly as a convenience tool for myself.
Using the win32 API you don't need to right-click -> display settings-> power & sleep ...
Just right-click the Paulo tray icon and change it!
* Kept open a possible extension for sleep-time, you can modify the code by changing command from ac to dc (or adding dc in a new command) to change sleep-time on laptop while on battery. This code is currently defined for desktop use only.
* Might extend it with other time-savers later.
* Changing from PowerShell backend to a direct API call might look nicer but is irrelevant for performance.


# How to
- Install requirements.txt stuff
- run run.bat
