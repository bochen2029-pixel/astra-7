// ASTRA-7 warp hull audio PoC — game mode. Spawns the voyage driver so the
// PoC works in ANY map (including the engine's Entry map) with zero assets.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "AstraAudioGameMode.generated.h"

UCLASS()
class AAstraAudioGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AAstraAudioGameMode();

	virtual void BeginPlay() override;
};
