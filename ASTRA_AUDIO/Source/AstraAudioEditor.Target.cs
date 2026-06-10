// ASTRA-7 warp hull audio PoC — editor target (PIE).

using UnrealBuildTool;
using System.Collections.Generic;

public class AstraAudioEditorTarget : TargetRules
{
	public AstraAudioEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("AstraAudio");
	}
}
