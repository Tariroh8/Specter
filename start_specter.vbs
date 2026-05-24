Set WshShell = CreateObject("WScript.Shell")
' Get the directory of this script
strPath = Wscript.ScriptFullName
Set objFSO = CreateObject("Scripting.FileSystemObject")
Set objFile = objFSO.GetFile(strPath)
strFolder = objFSO.GetParentFolderName(objFile)

' Construct the command to run Python silently
' WindowStyle 0 hides the window
strCommand = """" & strFolder & "\venv\Scripts\pythonw.exe"" """ & strFolder & "\launcher.py"""
WshShell.Run strCommand, 0, False
