// ASTRA-7 warp hull audio PoC — game target.

using UnrealBuildTool;
using System.Collections.Generic;

public class AstraAudioTarget : TargetRules
{
	public AstraAudioTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("AstraAudio");
	}
}
