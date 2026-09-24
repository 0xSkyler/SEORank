[Setup]
AppId={{0A8E3E54-9B31-4D09-B8CA-4C5C5C070101}
AppName=Serp Sentinel
AppVersion=0.1.0
AppPublisher=SEORank
DefaultDirName={autopf}\Serp Sentinel
DefaultGroupName=Serp Sentinel
OutputDir=..\release
OutputBaseFilename=SerpSentinel-v0.1.0-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern

[Files]
Source: "..\dist\SerpSentinel\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\Serp Sentinel"; Filename: "{app}\SerpSentinel.exe"
Name: "{autodesktop}\Serp Sentinel"; Filename: "{app}\SerpSentinel.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"
