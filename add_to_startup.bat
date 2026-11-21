@echo off
title Windows Baslangicina Ekle
echo WiFi Speed Tray Windows Baslangicina Ekleniyor...

powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut(\"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\WifiSpeedTray.lnk\"); $Shortcut.TargetPath = 'pythonw.exe'; $Shortcut.Arguments = '\"%~dp0wifi_speed_tray.py\"'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Description = 'WiFi Speed Tray Monitor'; $Shortcut.WindowStyle = 7; $Shortcut.Save()"

echo.
echo [OK] Basariyla eklendi! Bilgisayar her acildiginda otomatik baslayacak.
pause
