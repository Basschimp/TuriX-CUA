; Inno Setup Script for TuriX-CUA Windows Installer
; Save this as installer.iss and run with Inno Setup Compiler

[Setup]
AppId={{A1B2C3D4-E5F6-7890-GHIJ-KLMNOPQRSTUV}
AppName=TuriX-CUA
AppVersion=1.0.0
AppPublisher=TuriX-CUA
DefaultDirName={autopf}\TuriX-CUA
DefaultGroupName=TuriX-CUA
OutputDir=installer_output
OutputBaseFilename=TuriX-CUA-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Copy the entire dist/TuriX-CUA folder contents
Source: "dist\TuriX-CUA\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TuriX-CUA"; Filename: "{app}\TuriX-CUA.exe"
Name: "{autodesktop}\TuriX-CUA"; Filename: "{app}\TuriX-CUA.exe"
Name: "{userprograms}\TuriX-CUA"; Filename: "{app}\TuriX-CUA.exe"

[Run]
Filename: "{app}\TuriX-CUA.exe"; Description: "{cm:LaunchProgram,TuriX-CUA}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  // Check if Python is required (it's not, since we bundle everything)
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Optional: Create config directory in user's app data
    CreateDir(ExpandConstant('{userappdata}\TuriX-CUA'));
  end;
end;
