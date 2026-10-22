' ==============================================================================
' run_silent.vbs - Silent Launcher for ZYRO Voice Agent
' Prevents any black console window from blinking on startup.
' ==============================================================================
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strDir = fso.GetParentFolderName(WScript.ScriptFullName)

If fso.FileExists(strDir & "\.venv\Scripts\pythonw.exe") Then
    strCmd = """" & strDir & "\.venv\Scripts\pythonw.exe"" """ & strDir & "\zyro_app.pyw"""
Else
    strCmd = "pythonw """ & strDir & "\zyro_app.pyw"""
End If

WshShell.Run strCmd, 0, False
