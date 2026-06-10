#include "AstraAudioGameMode.h"
#include "AstraVoyageActor.h"
#include "GameFramework/SpectatorPawn.h"
#include "EngineUtils.h"

AAstraAudioGameMode::AAstraAudioGameMode()
{
	// Spectator pawn: free camera, no gameplay, audio listener follows.
	DefaultPawnClass = ASpectatorPawn::StaticClass();
}

void AAstraAudioGameMode::BeginPlay()
{
	Super::BeginPlay();

	for (TActorIterator<AAstraVoyageActor> It(GetWorld()); It; ++It)
	{
		return; // already placed in the level
	}
	GetWorld()->SpawnActor<AAstraVoyageActor>(FVector::ZeroVector, FRotator::ZeroRotator);
}
