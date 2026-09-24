[Setup]
AppName=Serp Sentinel
AppVersion=0.1.0
DefaultDirName={autopf}\Serp Sentinel
OutputBaseFilename=SerpSentinelSetup
[Files]
Source: "..\dist\SerpSentinel\*"; DestDir: "{app}"; Flags: recursesubdirs
[Icons]
Name: "{autoprograms}\Serp Sentinel"; Filename: "{app}\SerpSentinel.exe"
