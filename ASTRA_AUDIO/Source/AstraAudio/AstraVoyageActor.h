// ASTRA-7 warp hull audio PoC — voyage driver.
//
// Builds the MetaSound source graph procedurally at BeginPlay (no .uasset
// anywhere in this project), auditions it on an AudioComponent, then drives
// the synth's normalized field parameters through a scripted ~90 s voyage
// arc: REST -> CHARGE -> JUMP -> CRUISE -> 8000c PUSH -> BH PROXIMITY ->
// EMERGENCY DROP -> ring-down. Records the master output to a WAV under
// Saved/BouncedWavFiles for the showcase artifact.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AstraVoyageActor.generated.h"

class UAudioComponent;
class UMetaSoundSourceBuilder;

USTRUCT()
struct FVoyageParams
{
	GENERATED_BODY()

	float W = 0.0f;
	float GradW = 0.0f;
	float Vorticity = 0.0f;
	float Interference = 0.0f;
	float LifeSupport = 1.0f;
};

UCLASS()
class AAstraVoyageActor : public AActor
{
	GENERATED_BODY()

public:
	AAstraVoyageActor();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void Tick(float DeltaSeconds) override;

private:
	bool BuildAndAuditionGraph();
	void PushParams(const FVoyageParams& P, float DWdt);
	FVoyageParams EvalVoyage(float T, const TCHAR*& OutPhaseName) const;
	void StartVoyage();
	void StopRecordingIfActive();
	void SetPreset(const FVoyageParams& P, const TCHAR* Name);

	// Key handlers
	void OnKeyRest();
	void OnKeyCharge();
	void OnKeyCruise();
	void OnKeyHighWarp();
	void OnKeyBlackHole();
	void OnKeyDrop();
	void OnKeyCryo();
	void OnKeyToggleAuto();
	void OnKeyRestartVoyage();
	void OnKeyWUp();
	void OnKeyWDown();

	UPROPERTY()
	TObjectPtr<UAudioComponent> AudioComp;

	UPROPERTY()
	TObjectPtr<UMetaSoundSourceBuilder> Builder;

	bool bGraphLive = false;
	bool bAutoVoyage = true;
	bool bRecording = false;
	float VoyageTime = 0.0f;
	float PrevW = 0.0f;
	float SmoothedDWdt = 0.0f;
	FVoyageParams ManualParams;
	FString ManualPhaseName = TEXT("MANUAL");
};
