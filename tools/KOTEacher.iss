; KOTEacher 윈도 설치 프로그램 (Inno Setup 6). tools/build_win.py가 ISCC로 만든다.
; 관리자 권한 없이 내 계정(%LOCALAPPDATA%\Programs)에 설치한다.

[Setup]
AppId={{F80CE688-9C06-5E9E-92E8-F6D785B44BD9}
AppName=KOTEacher
AppVersion={#MyVersion}
AppPublisher=Hong-Iron
AppPublisherURL=https://github.com/Hong-Iron/KOTEacher
DefaultDirName={localappdata}\Programs\KOTEacher
DefaultGroupName=KOTEacher
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#OutDir}
OutputBaseFilename=KOTEacher-{#MyVersion}-Setup
SetupIconFile={#IconFile}
UninstallDisplayIcon={app}\KOTEacher.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "desktopicon"; Description: "바탕 화면에 아이콘 만들기"; GroupDescription: "아이콘:"

[Files]
Source: "{#SrcDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\KOTEacher"; Filename: "{app}\KOTEacher.exe"
Name: "{autodesktop}\KOTEacher"; Filename: "{app}\KOTEacher.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\KOTEacher.exe"; Description: "KOTEacher 실행"; Flags: nowait postinstall skipifsilent
