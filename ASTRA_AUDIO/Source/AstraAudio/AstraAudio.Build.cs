// ASTRA-7 warp hull audio PoC — runtime module.
// MetaSound deps: custom node (Frontend/GraphCore) + procedural graph builder (Engine).

using UnrealBuildTool;

public class AstraAudio : ModuleRules
{
	public AstraAudio(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		// UE 5.7 per-module MetaSound node registration. Without these, the
		// METASOUND_REGISTER_NODE action falls back to the deprecated global
		// registration list whose default-constructed FModuleInfo holds
		// uninitialized FLazyNames -> checkNoEntry crash at editor startup
		// (UnrealNames.cpp:4528) when the registry resolves them. Engine
		// modules all define these; game modules must too.
		PrivateDefinitions.AddRange(new string[]
		{
			"METASOUND_PLUGIN=AstraAudio",
			"METASOUND_MODULE=AstraAudio"
		});

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"AudioMixer",
			"AudioExtensions",
			"MetasoundEngine",
			"MetasoundFrontend",
			"MetasoundGraphCore"
		});
	}
}
