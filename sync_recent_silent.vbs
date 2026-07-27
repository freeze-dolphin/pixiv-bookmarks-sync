Dim ws
Set ws = Wscript.CreateObject("Wscript.Shell")
ws.run "sync_recent_nopause.bat",vbhide
Wscript.quit