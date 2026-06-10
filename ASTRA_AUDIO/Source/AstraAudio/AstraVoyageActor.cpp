#include "AstraVoyageActor.h"

#include "AudioMixerBlueprintLibrary.h"
#include "Components/AudioComponent.h"
#include "Components/InputComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "MetasoundBuilderSubsystem.h"

DEFINE_LOG_CATEGORY_STATIC(LogAstraAudio, Log, All);

namespace
{
	// Synth parameter names — must match WarpHullSynthNode vertex names exactly.
	const FName ParamW(TEXT("W"));
	const FName ParamDWdt(TEXT("dWdt"));
	const FName ParamGradW(TEXT("GradW"));
	const FName ParamVorticity(TEXT("Vorticity"));
	const FName ParamInterference(TEXT("Interference"));
	const FName ParamLifeSupport(TEXT("LifeSupport"));
	const FName ParamMasterGain(TEXT("MasterGain"));

	constexpr float VoyageEndTime = 90.0f;
	constexpr float RecordExpectedDuration = 95.0f;

	float SmoothRamp(float T, float Start, float Duration)
	{
		return FMath::SmoothStep(0.0f, 1.0f, FMath::Clamp((T - Start) / Duration, 0.0f, 1.0f));
	}
}

AAstraVoyageActor::AAstraVoyageActor()
{
	PrimaryActorTick.bCanEverTick = true;

	AudioComp = CreateDefaultSubobject<UAudioComponent>(TEXT("AstraAudioComp"));
	AudioComp->SetAutoActivate(false);
	RootComponent = AudioComp;
}

void AAstraVoyageActor::BeginPlay()
{
	Super::BeginPlay();

	bGraphLive = BuildAndAuditionGraph();
	if (!bGraphLive)
	{
		UE_LOG(LogAstraAudio, Error, TEXT("WarpHullSynth graph build FAILED — see log above."));
		return;
	}

	// Keyboard control.
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
	{
		EnableInput(PC);
		if (InputComponent)
		{
			InputComponent->BindKey(EKeys::One,   IE_Pressed, this, &AAstraVoyageActor::OnKeyRest);
			InputComponent->BindKey(EKeys::Two,   IE_Pressed, this, &AAstraVoyageActor::OnKeyCharge);
			InputComponent->BindKey(EKeys::Three, IE_Pressed, this, &AAstraVoyageActor::OnKeyCruise);
			InputComponent->BindKey(EKeys::Four,  IE_Pressed, this, &AAstraVoyageActor::OnKeyHighWarp);
			InputComponent->BindKey(EKeys::Five,  IE_Pressed, this, &AAstraVoyageActor::OnKeyBlackHole);
			InputComponent->BindKey(EKeys::Six,   IE_Pressed, this, &AAstraVoyageActor::OnKeyDrop);
			InputComponent->BindKey(EKeys::Seven, IE_Pressed, this, &AAstraVoyageActor::OnKeyCryo);
			InputComponent->BindKey(EKeys::SpaceBar, IE_Pressed, this, &AAstraVoyageActor::OnKeyToggleAuto);
			InputComponent->BindKey(EKeys::R, IE_Pressed, this, &AAstraVoyageActor::OnKeyRestartVoyage);
			InputComponent->BindKey(EKeys::Up,   IE_Pressed, this, &AAstraVoyageActor::OnKeyWUp);
			InputComponent->BindKey(EKeys::Down, IE_Pressed, this, &AAstraVoyageActor::OnKeyWDown);
		}
	}

	StartVoyage();
}

void AAstraVoyageActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	StopRecordingIfActive();
	Super::EndPlay(EndPlayReason);
}

bool AAstraVoyageActor::BuildAndAuditionGraph()
{
	UMetaSoundBuilderSubsystem* Subsystem = GEngine ? GEngine->GetEngineSubsystem<UMetaSoundBuilderSubsystem>() : nullptr;
	if (!Subsystem)
	{
		UE_LOG(LogAstraAudio, Error, TEXT("MetaSoundBuilderSubsystem unavailable."));
		return false;
	}

	EMetaSoundBuilderResult Result = EMetaSoundBuilderResult::Failed;
	FMetaSoundBuilderNodeOutputHandle OnPlayOutput;
	FMetaSoundBuilderNodeInputHandle OnFinishedInput;
	TArray<FMetaSoundBuilderNodeInputHandle> AudioOutInputs;

	Builder = Subsystem->CreateSourceBuilder(
		FName(TEXT("AstraWarpHullBuilder")),
		OnPlayOutput,
		OnFinishedInput,
		AudioOutInputs,
		Result,
		EMetaSoundOutputAudioFormat::Stereo,
		/*bIsOneShot=*/ false);

	if (Result != EMetaSoundBuilderResult::Succeeded || !Builder)
	{
		UE_LOG(LogAstraAudio, Error, TEXT("CreateSourceBuilder failed."));
		return false;
	}

	// The five-layer synth, registered by the AstraAudio module.
	const FMetasoundFrontendClassName SynthClassName(FName(TEXT("AstraAudio")), FName(TEXT("WarpHullSynth")), FName());
	const FMetaSoundNodeHandle SynthNode = Builder->AddNodeByClassName(SynthClassName, Result, 1);
	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		UE_LOG(LogAstraAudio, Error, TEXT("AddNodeByClassName(AstraAudio.WarpHullSynth) failed — node not registered?"));
		return false;
	}

	// Graph inputs — names double as the runtime parameter interface.
	struct FParamSpec { FName Name; float Default; };
	const FParamSpec Params[] =
	{
		{ ParamW, 0.0f },
		{ ParamDWdt, 0.0f },
		{ ParamGradW, 0.0f },
		{ ParamVorticity, 0.0f },
		{ ParamInterference, 0.0f },
		{ ParamLifeSupport, 1.0f },
		{ ParamMasterGain, 0.9f },
	};

	for (const FParamSpec& Spec : Params)
	{
		FName FloatDataType;
		const FMetasoundFrontendLiteral DefaultLiteral = Subsystem->CreateFloatMetaSoundLiteral(Spec.Default, FloatDataType);

		Builder->AddGraphInputNode(Spec.Name, FloatDataType, DefaultLiteral, Result);
		if (Result != EMetaSoundBuilderResult::Succeeded)
		{
			UE_LOG(LogAstraAudio, Error, TEXT("AddGraphInputNode(%s) failed."), *Spec.Name.ToString());
			return false;
		}

		Builder->ConnectGraphInputToNode(Spec.Name, SynthNode, Spec.Name, Result);
		if (Result != EMetaSoundBuilderResult::Succeeded)
		{
			UE_LOG(LogAstraAudio, Error, TEXT("ConnectGraphInputToNode(%s) failed."), *Spec.Name.ToString());
			return false;
		}
	}

	// Stereo out.
	if (AudioOutInputs.Num() < 2)
	{
		UE_LOG(LogAstraAudio, Error, TEXT("Expected stereo graph outputs, got %d."), AudioOutInputs.Num());
		return false;
	}
	Builder->ConnectNamedNodeOutputToGraphOutput(SynthNode, FName(TEXT("Out Left")), AudioOutInputs[0], Result);
	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		UE_LOG(LogAstraAudio, Error, TEXT("Connect Out Left failed."));
		return false;
	}
	Builder->ConnectNamedNodeOutputToGraphOutput(SynthNode, FName(TEXT("Out Right")), AudioOutInputs[1], Result);
	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		UE_LOG(LogAstraAudio, Error, TEXT("Connect Out Right failed."));
		return false;
	}

	// Live audition — builds a transient MetaSound source and plays it.
	Builder->Audition(this, AudioComp, FOnCreateAuditionGeneratorHandleDelegate(), /*bLiveUpdatesEnabled=*/ false);

	UE_LOG(LogAstraAudio, Display, TEXT("WarpHullSynth graph live. The audio is the field."));
	return true;
}

void AAstraVoyageActor::PushParams(const FVoyageParams& P, float DWdt)
{
	AudioComp->SetFloatParameter(ParamW, P.W);
	AudioComp->SetFloatParameter(ParamDWdt, DWdt);
	AudioComp->SetFloatParameter(ParamGradW, P.GradW);
	AudioComp->SetFloatParameter(ParamVorticity, P.Vorticity);
	AudioComp->SetFloatParameter(ParamInterference, P.Interference);
	AudioComp->SetFloatParameter(ParamLifeSupport, P.LifeSupport);
}

FVoyageParams AAstraVoyageActor::EvalVoyage(float T, const TCHAR*& OutPhaseName) const
{
	FVoyageParams P;
	P.LifeSupport = 1.0f;

	if (T < 10.0f)
	{
		OutPhaseName = TEXT("REST — coasting, life support only");
	}
	else if (T < 25.0f)
	{
		OutPhaseName = TEXT("WARP CHARGE — field building");
		const float S = SmoothRamp(T, 10.0f, 15.0f);
		P.W = 0.35f * S;
		P.GradW = 0.18f * S;
		P.Vorticity = 0.06f * S;
		P.Interference = 0.02f * S;
	}
	else if (T < 25.5f)
	{
		OutPhaseName = TEXT("JUMP — bubble forms");
		const float S = SmoothRamp(T, 25.0f, 0.5f);
		P.W = FMath::Lerp(0.35f, 0.55f, S);
		P.GradW = FMath::Lerp(0.18f, 0.45f, S);
		P.Vorticity = FMath::Lerp(0.06f, 0.12f, S);
		P.Interference = 0.04f;
	}
	else if (T < 45.0f)
	{
		OutPhaseName = TEXT("WARP CRUISE 2c — steady state");
		const float Settle = SmoothRamp(T, 25.5f, 3.0f);
		P.W = 0.55f + 0.01f * FMath::Sin(0.3f * T);
		P.GradW = FMath::Lerp(0.45f, 0.28f, Settle);
		P.Vorticity = 0.12f;
		P.Interference = 0.06f + 0.04f * FMath::Sin(0.21f * T);
	}
	else if (T < 65.0f)
	{
		OutPhaseName = TEXT("PUSH TO 8000c — the hull rings");
		const float S = SmoothRamp(T, 45.0f, 20.0f);
		P.W = FMath::Lerp(0.55f, 0.95f, S);
		P.GradW = FMath::Lerp(0.28f, 0.85f, S);
		P.Vorticity = FMath::Lerp(0.12f, 0.70f, S);
		P.Interference = FMath::Lerp(0.06f, 0.35f, S);
	}
	else if (T < 72.0f)
	{
		OutPhaseName = TEXT("BH PROXIMITY — chaos coupling, Reflex working");
		const float S = SmoothRamp(T, 65.0f, 2.0f);
		P.W = 0.95f;
		P.GradW = FMath::Lerp(0.85f, 0.90f, S);
		P.Vorticity = FMath::Lerp(0.70f, 0.92f, S);
		P.Interference = FMath::Lerp(0.35f, 0.70f, S);
	}
	else if (T < 72.3f)
	{
		OutPhaseName = TEXT("EMERGENCY DROP — field cut");
		const float S = 1.0f - SmoothRamp(T, 72.0f, 0.3f);
		P.W = 0.95f * S;
		P.GradW = 0.90f * S;
		P.Vorticity = 0.92f * S;
		P.Interference = 0.70f * S;
	}
	else
	{
		OutPhaseName = TEXT("RING-DOWN — the hull remembers");
		// All drives zero; the modal bank decays on its own. Life support remains.
	}

	return P;
}

void AAstraVoyageActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (!bGraphLive)
	{
		return;
	}

	VoyageTime += DeltaSeconds;

	const TCHAR* PhaseName = TEXT("MANUAL");
	FVoyageParams P;
	if (bAutoVoyage)
	{
		P = EvalVoyage(VoyageTime, PhaseName);
	}
	else
	{
		P = ManualParams;
		PhaseName = *ManualPhaseName;
	}

	// Numeric dW/dt, normalized + smoothed — drives modal strike transients.
	const float RawDWdt = (DeltaSeconds > KINDA_SMALL_NUMBER) ? (P.W - PrevW) / DeltaSeconds : 0.0f;
	PrevW = P.W;
	const float TargetDWdt = FMath::Clamp(RawDWdt * 0.5f, -1.0f, 1.0f);
	SmoothedDWdt += 0.2f * (TargetDWdt - SmoothedDWdt);

	PushParams(P, SmoothedDWdt);

	// Voyage end: finalize the WAV.
	if (bAutoVoyage && bRecording && VoyageTime >= VoyageEndTime)
	{
		StopRecordingIfActive();
	}

	// HUD.
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(100, 1.5f, FColor::Cyan,
			FString::Printf(TEXT("[ASTRA-7 WARP AUDIO]  t=%5.1fs  %s"), VoyageTime, PhaseName));
		GEngine->AddOnScreenDebugMessage(101, 1.5f, FColor::Yellow,
			FString::Printf(TEXT("W=%.2f  dWdt=%+.2f  GradW=%.2f  Vort=%.2f  Intf=%.2f"),
				P.W, SmoothedDWdt, P.GradW, P.Vorticity, P.Interference));
		GEngine->AddOnScreenDebugMessage(102, 1.5f, bRecording ? FColor::Red : FColor::Silver,
			bRecording ? TEXT("REC -> Saved/BouncedWavFiles") : TEXT("not recording"));
		GEngine->AddOnScreenDebugMessage(103, 1.5f, FColor::Silver,
			TEXT("[Space] auto/manual  [R] restart+record  [1]rest [2]charge [3]cruise [4]8000c [5]BH [6]drop [7]cryo  [Up/Dn] W"));
	}
}

void AAstraVoyageActor::StartVoyage()
{
	StopRecordingIfActive();
	VoyageTime = 0.0f;
	PrevW = 0.0f;
	SmoothedDWdt = 0.0f;
	bAutoVoyage = true;

	UAudioMixerBlueprintLibrary::StartRecordingOutput(this, RecordExpectedDuration);
	bRecording = true;
	UE_LOG(LogAstraAudio, Display, TEXT("Voyage started; recording master output (~%.0fs)."), VoyageEndTime);
}

void AAstraVoyageActor::StopRecordingIfActive()
{
	if (!bRecording)
	{
		return;
	}
	bRecording = false;

	const FString WavName = FString::Printf(TEXT("astra_warp_voyage_%s"), *FDateTime::Now().ToString(TEXT("%Y%m%d_%H%M%S")));
	UAudioMixerBlueprintLibrary::StopRecordingOutput(this, EAudioRecordingExportType::WavFile, WavName, FString());
	UE_LOG(LogAstraAudio, Display, TEXT("Voyage WAV written: Saved/BouncedWavFiles/%s.wav"), *WavName);
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(110, 8.0f, FColor::Green,
			FString::Printf(TEXT("WAV saved: Saved/BouncedWavFiles/%s.wav"), *WavName));
	}
}

void AAstraVoyageActor::SetPreset(const FVoyageParams& P, const TCHAR* Name)
{
	bAutoVoyage = false;
	ManualParams = P;
	ManualPhaseName = Name;
}

void AAstraVoyageActor::OnKeyRest()      { SetPreset({ 0.00f, 0.00f, 0.00f, 0.00f, 1.0f }, TEXT("PRESET: REST")); }
void AAstraVoyageActor::OnKeyCharge()    { SetPreset({ 0.30f, 0.18f, 0.06f, 0.02f, 1.0f }, TEXT("PRESET: CHARGE")); }
void AAstraVoyageActor::OnKeyCruise()    { SetPreset({ 0.55f, 0.28f, 0.12f, 0.06f, 1.0f }, TEXT("PRESET: CRUISE 2c")); }
void AAstraVoyageActor::OnKeyHighWarp()  { SetPreset({ 0.95f, 0.85f, 0.70f, 0.35f, 1.0f }, TEXT("PRESET: 8000c — hull rings")); }
void AAstraVoyageActor::OnKeyBlackHole() { SetPreset({ 0.95f, 0.90f, 0.92f, 0.70f, 1.0f }, TEXT("PRESET: BH PROXIMITY")); }
void AAstraVoyageActor::OnKeyDrop()      { SetPreset({ 0.00f, 0.00f, 0.00f, 0.00f, 1.0f }, TEXT("PRESET: DROP — ring-down")); }
void AAstraVoyageActor::OnKeyCryo()      { SetPreset({ 0.00f, 0.00f, 0.00f, 0.00f, 0.35f }, TEXT("PRESET: CRYOSLEEP")); }

void AAstraVoyageActor::OnKeyToggleAuto()
{
	bAutoVoyage = !bAutoVoyage;
	if (!bAutoVoyage)
	{
		const TCHAR* PhaseName = TEXT("");
		ManualParams = EvalVoyage(VoyageTime, PhaseName);
		ManualPhaseName = TEXT("MANUAL (frozen from voyage)");
	}
}

void AAstraVoyageActor::OnKeyRestartVoyage()
{
	StartVoyage();
}

void AAstraVoyageActor::OnKeyWUp()
{
	if (!bAutoVoyage)
	{
		ManualParams.W = FMath::Clamp(ManualParams.W + 0.05f, 0.0f, 1.0f);
	}
}

void AAstraVoyageActor::OnKeyWDown()
{
	if (!bAutoVoyage)
	{
		ManualParams.W = FMath::Clamp(ManualParams.W - 0.05f, 0.0f, 1.0f);
	}
}
