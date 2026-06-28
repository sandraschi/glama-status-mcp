; -- native/windows/hooks.nsh --
; Kill UI + backend before install/uninstall (backend locks resources/*.exe).
!macro KillFleetProcesses
  DetailPrint "Stopping Glama Status MCP processes..."

  ExecWait 'powershell -NoProfile -Command "Stop-Process -Name glama-status-mcp-backend -Force -ErrorAction SilentlyContinue; Stop-Process -Name glama-status-native -Force -ErrorAction SilentlyContinue; taskkill /F /IM glama-status-mcp-backend.exe /T 2>$null; taskkill /F /IM glama-status-native.exe /T 2>$null"' $0

  !if "${INSTALLMODE}" == "currentUser"
    nsis_tauri_utils::KillProcessCurrentUser "glama-status-mcp-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcessCurrentUser "glama-status-native.exe"
    Pop $0
  !else
    nsis_tauri_utils::KillProcess "glama-status-mcp-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcess "glama-status-native.exe"
    Pop $0
  !endif
  Sleep 3000
!macroend

!macro UninstallPrevious
  DetailPrint "Checking for previous installation..."
  !if "${INSTALLMODE}" == "currentUser"
    ReadRegStr $R0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${IDENTIFIER}" "UninstallString"
  !else
    ReadRegStr $R0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${IDENTIFIER}" "UninstallString"
  !endif
  ${If} $R0 != ""
    DetailPrint "Removing previous installation..."
    ExecWait '"$R0" /S' $0
    DetailPrint "Previous uninstall exit code: $0"
    Sleep 1500
  ${EndIf}
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro KillFleetProcesses
  !insertmacro UninstallPrevious
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro KillFleetProcesses
!macroend
