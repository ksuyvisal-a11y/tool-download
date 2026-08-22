; Script generated for SKD TOOL Standalone Installer
; Requires Inno Setup 6 (https://jrsoftware.org/isinfo.php)

#define MyAppName "SKD TOOL - Ultimate Media Downloader"
#define MyAppVersion "6.5"
#define MyAppPublisher "SKD Studio"
#define MyAppURL "https://t.me/SKD_ADMIN"
#define MyAppExeName "SKD_TOOL.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{5E28564F-2940-4A0B-971B-94E5E948DA9E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\SKD Tool
DisableProgramGroupPage=yes
; PrivilegesRequired=lowest
OutputDir=installer_output
OutputBaseFilename=SKD_Tool_Setup_v6.5
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
