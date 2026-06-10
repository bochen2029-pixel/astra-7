// ASTRA-7 warp hull audio PoC — primary game module.
//
// UE 5.7 per-module MetaSound node registration, mirroring the engine's own
// MetasoundStandardNodesModule.cpp: the METASOUND_PLUGIN / METASOUND_MODULE
// defines (AstraAudio.Build.cs) route METASOUND_REGISTER_NODE actions into
// this module's registration list; the STARTUP/SHUTDOWN macros below register
// and unregister them with a properly populated FModuleInfo. (The pre-5.7
// RegisterPendingNodes() path crashes for game modules: the fallback global
// list carries default-constructed FLazyNames.)

#include "CoreMinimal.h"
#include "MetasoundFrontendModuleRegistrationMacros.h"
#include "Modules/ModuleManager.h"

class FAstraAudioModule : public FDefaultGameModuleImpl
{
public:
	virtual void StartupModule() override
	{
		using namespace Metasound::Frontend;
		METASOUND_REGISTER_ITEMS_IN_MODULE
	}

	virtual void ShutdownModule() override
	{
		using namespace Metasound::Frontend;
		METASOUND_UNREGISTER_ITEMS_IN_MODULE
	}
};

METASOUND_IMPLEMENT_MODULE_REGISTRATION_LIST
IMPLEMENT_PRIMARY_GAME_MODULE(FAstraAudioModule, AstraAudio, "AstraAudio");
