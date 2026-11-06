; Husham Play Windows x64 installer (NSIS Modern UI)
; Built from the packaged application folder by GitHub Actions.

!include "MUI2.nsh"
!include "x64.nsh"

!ifndef HP_VERSION
  !define HP_VERSION "1.5"
!endif
!ifndef HP_SOURCE
  !define HP_SOURCE "Husham Play"
!endif
!ifndef HP_OUTFILE
  !define HP_OUTFILE "Husham-Play-${HP_VERSION}-windows-x64-setup.exe"
!endif
!ifndef HP_ICON
  !define HP_ICON "icon.ico"
!endif
!ifndef HP_LICENSE
  !define HP_LICENSE "LICENSE.txt"
!endif

Name "Husham Play"
OutFile "${HP_OUTFILE}"
Unicode true
SetCompressor /SOLID lzma
RequestExecutionLevel admin
InstallDir "$PROGRAMFILES64\Husham Play"
InstallDirRegKey HKLM "Software\Husham Play" "InstallPath"
ShowInstDetails show

!define MUI_ABORTWARNING
!define MUI_ICON "${HP_ICON}"
!define MUI_UNICON "${HP_ICON}"
!define MUI_FINISHPAGE_RUN "$INSTDIR\Husham Play.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch Husham Play"
!define MUI_FINISHPAGE_LINK "husham.com"
!define MUI_FINISHPAGE_LINK_LOCATION "https://www.husham.com/"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${HP_LICENSE}"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

VIProductVersion "${HP_VERSION}.0.0"
VIAddVersionKey "ProductName" "Husham Play"
VIAddVersionKey "FileDescription" "Husham Play Setup"
VIAddVersionKey "FileVersion" "${HP_VERSION}"
VIAddVersionKey "ProductVersion" "${HP_VERSION}"
VIAddVersionKey "LegalCopyright" "Dr Husham Memar / GPL-2.0-or-later"
VIAddVersionKey "CompanyName" "Husham"

Section "Husham Play" SecMain
  SectionIn RO
  SetOutPath "$INSTDIR"
  File /r "${HP_SOURCE}\*.*"

  ; Shortcuts
  CreateDirectory "$SMPROGRAMS\Husham Play"
  CreateShortCut "$SMPROGRAMS\Husham Play\Husham Play.lnk" "$INSTDIR\Husham Play.exe"
  CreateShortCut "$SMPROGRAMS\Husham Play\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  CreateShortCut "$DESKTOP\Husham Play.lnk" "$INSTDIR\Husham Play.exe"

  ; Uninstaller + ARP entry
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Husham Play" "InstallPath" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\HushamPlay" "DisplayName" "Husham Play"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\HushamPlay" "DisplayVersion" "${HP_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\HushamPlay" "Publisher" "Dr Husham Memar"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\HushamPlay" "DisplayIcon" "$INSTDIR\Husham Play.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\HushamPlay" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\HushamPlay" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\HushamPlay" "URLInfoAbout" "https://www.husham.com/"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\HushamPlay" "HelpLink" "https://www.husham.com/"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\HushamPlay" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\HushamPlay" "NoRepair" 1
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\Husham Play.lnk"
  RMDir /r "$SMPROGRAMS\Husham Play"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\HushamPlay"
  DeleteRegKey HKLM "Software\Husham Play"
SectionEnd
