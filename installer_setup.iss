; Script generated for SKD TOOL Standalone Installer
; Requires Inno Setup 6 (https://jrsoftware.org/isinfo.php)

#define MyAppName "SKD TOOL - Ultimate Media Downloader"
#define MyAppVersion "1.0.9"
#define MyAppPublisher "SKD CyberGuard"
#define MyAppURL "https://github.com/ksuyvisal-a11y/tool-download"
#define MyAppExeName "SKD_TOOL.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{D9A6F4E2-81B3-4B07-9E45-8B2A91D0E471}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; The [Icons] "quicklaunchicon" entry uses {userappdata}, but will be used only on Windows Vista and older, but we want universal.
LicenseFile=
OutputDir=installer_output
OutputBaseFilename=SKD_TOOL_Setup_v1.0.9
SetupIconFile=assets\app_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSmallImageFile=assets\app_icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\SKD_TOOL.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\app_icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\app_icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
