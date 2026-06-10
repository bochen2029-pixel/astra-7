// ASTRA-7 warp hull synthesis — single custom MetaSound node, all five layers.
//
// Canon sources:
//   docs/synthesis.md "4.x The audio is the field" — five layers + drive params:
//     L1 drone        additive 12-45 Hz, tracks |W|
//     L2 shear        FM, modulation index = |gradW| x 150, modulator ratio = pi
//     L3 turbulence   granular, grain density = vorticity x 800 /sec
//     L4 interference ring modulation (nacelle-pair / multi-field coupling)
//     L5 hull modes   8-voice modal bank; damping inversely proportional to
//                     warp factor — at high warp the hull rings
//   spec v0.128 §8.3 locked DSP:
//     modal IIR    y[n] = 2 cos(w0) r y[n-1] - r^2 y[n-2] + x[n],  r = exp(-pi BW / SR)
//     DC blocker   y[n] = a (y[n-1] + x[n] - x[n-1]),              a = exp(-2 pi fc / SR)
//     grain pool   8-16 voices, round-robin allocation
//
// All inputs are normalized [0,1] drives (the voyage driver owns the mapping
// from physical quantities). Numeric coefficients marked PROVISIONAL are
// tune-by-ear targets; the structural forms above are spec-locked.

#include "Internationalization/Text.h"
#include "MetasoundExecutableOperator.h"
#include "MetasoundNodeRegistrationMacro.h"
#include "MetasoundPrimitives.h"
#include "MetasoundAudioBuffer.h"
#include "MetasoundFacade.h"
#include "MetasoundParamHelper.h"
#include "Math/RandomStream.h"
#include "Math/UnrealMathUtility.h"

#define LOCTEXT_NAMESPACE "AstraAudio_WarpHullSynthNode"

namespace Metasound
{
	namespace WarpHullSynthVertexNames
	{
		METASOUND_PARAM(InputW,            "W",            "Normalized warp field amplitude [0,1].");
		METASOUND_PARAM(InputDWdt,         "dWdt",         "Normalized warp amplitude rate of change [-1,1]. Drives modal strike transients.");
		METASOUND_PARAM(InputGradW,        "GradW",        "Normalized bubble-wall tidal gradient |gradW| [0,1]. Drives FM shear index.");
		METASOUND_PARAM(InputVorticity,    "Vorticity",    "Normalized wake vorticity [0,1]. Drives grain density (x800/sec at 1).");
		METASOUND_PARAM(InputInterference, "Interference", "Normalized field interference coupling [0,1]. Drives ring modulation.");
		METASOUND_PARAM(InputLifeSupport,  "LifeSupport",  "Life-support ambient noise floor enable [0,1].");
		METASOUND_PARAM(InputMasterGain,   "MasterGain",   "Master output gain [0,1].");

		METASOUND_PARAM(OutputAudioLeft,  "Out Left",  "Left channel of the synthesized hull field.");
		METASOUND_PARAM(OutputAudioRight, "Out Right", "Right channel of the synthesized hull field.");
	}

	class FWarpHullSynthOperator : public TExecutableOperator<FWarpHullSynthOperator>
	{
	public:
		// --- Tuning tables (PROVISIONAL coefficients; structures spec-locked) ---

		// L1 additive drone: slightly inharmonic partial stack.
		static constexpr int32 NumDronePartials = 4;
		static constexpr float DroneRatios[NumDronePartials] = { 1.0f, 2.0f, 2.98f, 4.21f };
		static constexpr float DroneGains[NumDronePartials]  = { 1.0f, 0.5f, 0.30f, 0.18f };

		// L3 grain pool — §8.3 locks 8-16 voices, round-robin.
		static constexpr int32 NumGrainVoices = 16;

		// L5 modal bank — 8 modes. Frequencies: stretched inharmonic series
		// (~x1.66 per step with per-mode detune) seeded by the 280 x 78 x 22 m
		// hull; spread 55 Hz - 2.43 kHz. PROVISIONAL, tune by ear.
		static constexpr int32 NumModes = 8;
		static constexpr float ModeFreqs[NumModes] = { 55.0f, 92.4f, 147.6f, 233.1f, 388.8f, 642.0f, 1276.5f, 2431.7f };
		static constexpr float ModeGains[NumModes] = { 1.0f, 0.85f, 0.70f, 0.60f, 0.50f, 0.42f, 0.30f, 0.22f };
		static constexpr float ModeBW0[NumModes]   = { 6.0f, 6.5f, 7.0f, 8.0f, 9.0f, 10.0f, 12.0f, 14.0f };

		FWarpHullSynthOperator(const FBuildOperatorParams& InParams,
			const FFloatReadRef& InW,
			const FFloatReadRef& InDWdt,
			const FFloatReadRef& InGradW,
			const FFloatReadRef& InVorticity,
			const FFloatReadRef& InInterference,
			const FFloatReadRef& InLifeSupport,
			const FFloatReadRef& InMasterGain)
			: WIn(InW)
			, DWdtIn(InDWdt)
			, GradWIn(InGradW)
			, VorticityIn(InVorticity)
			, InterferenceIn(InInterference)
			, LifeSupportIn(InLifeSupport)
			, MasterGainIn(InMasterGain)
			, OutLeft(FAudioBufferWriteRef::CreateNew(InParams.OperatorSettings))
			, OutRight(FAudioBufferWriteRef::CreateNew(InParams.OperatorSettings))
			, SampleRate(InParams.OperatorSettings.GetSampleRate())
			, Rng(1337)
		{
			ResetState();
		}

		static const FNodeClassMetadata& GetNodeInfo()
		{
			auto CreateNodeClassMetadata = []() -> FNodeClassMetadata
			{
				FVertexInterface NodeInterface = DeclareVertexInterface();

				FNodeClassMetadata Metadata
				{
					FNodeClassName { "AstraAudio", "WarpHullSynth", "" },
					1, // Major version
					0, // Minor version
					METASOUND_LOCTEXT("WarpHullSynthDisplayName", "Warp Hull Synth"),
					METASOUND_LOCTEXT("WarpHullSynthDesc", "ASTRA-7 five-layer warp field hull synthesis. The audio is the field."),
					FString(TEXT("ASTRA-7")),
					METASOUND_LOCTEXT("AstraAudioMissingPrompt", "Enable the AstraAudio module."),
					NodeInterface,
					{ METASOUND_LOCTEXT("AstraCategory", "ASTRA-7") },
					{ },
					FNodeDisplayStyle()
				};

				return Metadata;
			};

			static const FNodeClassMetadata Metadata = CreateNodeClassMetadata();
			return Metadata;
		}

		static const FVertexInterface& DeclareVertexInterface()
		{
			using namespace WarpHullSynthVertexNames;

			static const FVertexInterface Interface(
				FInputVertexInterface(
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InputW), 0.0f),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InputDWdt), 0.0f),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InputGradW), 0.0f),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InputVorticity), 0.0f),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InputInterference), 0.0f),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InputLifeSupport), 1.0f),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InputMasterGain), 0.9f)
				),
				FOutputVertexInterface(
					TOutputDataVertex<FAudioBuffer>(METASOUND_GET_PARAM_NAME_AND_METADATA(OutputAudioLeft)),
					TOutputDataVertex<FAudioBuffer>(METASOUND_GET_PARAM_NAME_AND_METADATA(OutputAudioRight))
				)
			);

			return Interface;
		}

		virtual void BindInputs(FInputVertexInterfaceData& InOutVertexData) override
		{
			using namespace WarpHullSynthVertexNames;
			InOutVertexData.BindReadVertex(METASOUND_GET_PARAM_NAME(InputW), WIn);
			InOutVertexData.BindReadVertex(METASOUND_GET_PARAM_NAME(InputDWdt), DWdtIn);
			InOutVertexData.BindReadVertex(METASOUND_GET_PARAM_NAME(InputGradW), GradWIn);
			InOutVertexData.BindReadVertex(METASOUND_GET_PARAM_NAME(InputVorticity), VorticityIn);
			InOutVertexData.BindReadVertex(METASOUND_GET_PARAM_NAME(InputInterference), InterferenceIn);
			InOutVertexData.BindReadVertex(METASOUND_GET_PARAM_NAME(InputLifeSupport), LifeSupportIn);
			InOutVertexData.BindReadVertex(METASOUND_GET_PARAM_NAME(InputMasterGain), MasterGainIn);
		}

		virtual void BindOutputs(FOutputVertexInterfaceData& InOutVertexData) override
		{
			using namespace WarpHullSynthVertexNames;
			InOutVertexData.BindReadVertex(METASOUND_GET_PARAM_NAME(OutputAudioLeft), OutLeft);
			InOutVertexData.BindReadVertex(METASOUND_GET_PARAM_NAME(OutputAudioRight), OutRight);
		}

		static TUniquePtr<IOperator> CreateOperator(const FBuildOperatorParams& InParams, FBuildResults& OutResults)
		{
			using namespace WarpHullSynthVertexNames;
			const FInputVertexInterfaceData& InputData = InParams.InputData;

			FFloatReadRef W            = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InputW), InParams.OperatorSettings);
			FFloatReadRef DWdt         = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InputDWdt), InParams.OperatorSettings);
			FFloatReadRef GradW        = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InputGradW), InParams.OperatorSettings);
			FFloatReadRef Vorticity    = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InputVorticity), InParams.OperatorSettings);
			FFloatReadRef Interference = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InputInterference), InParams.OperatorSettings);
			FFloatReadRef LifeSupport  = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InputLifeSupport), InParams.OperatorSettings);
			FFloatReadRef MasterGain   = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InputMasterGain), InParams.OperatorSettings);

			return MakeUnique<FWarpHullSynthOperator>(InParams, W, DWdt, GradW, Vorticity, Interference, LifeSupport, MasterGain);
		}

		void Execute()
		{
			const int32 NumFrames = OutLeft->Num();
			float* LeftData = OutLeft->GetData();
			float* RightData = OutRight->GetData();

			// Block-rate parameter targets (clamped); smoothed per sample below.
			const float TgtW     = FMath::Clamp(*WIn, 0.0f, 1.0f);
			const float TgtDWdt  = FMath::Clamp(*DWdtIn, -1.0f, 1.0f);
			const float TgtGrad  = FMath::Clamp(*GradWIn, 0.0f, 1.0f);
			const float TgtVort  = FMath::Clamp(*VorticityIn, 0.0f, 1.0f);
			const float TgtInt   = FMath::Clamp(*InterferenceIn, 0.0f, 1.0f);
			const float TgtLife  = FMath::Clamp(*LifeSupportIn, 0.0f, 1.0f);
			const float TgtGain  = FMath::Clamp(*MasterGainIn, 0.0f, 1.0f);

			// One-pole smoothing coefficients (~20 ms general, ~5 ms for dWdt).
			const float ASlow = 1.0f - FMath::Exp(-1.0f / (0.020f * SampleRate));
			const float AFast = 1.0f - FMath::Exp(-1.0f / (0.005f * SampleRate));

			const float TwoPi = 2.0f * PI;
			const float InvSR = 1.0f / SampleRate;

			// §8.3 DC blocker coefficient, fc = 20 Hz.
			const float DCAlpha = FMath::Exp(-TwoPi * 20.0f * InvSR);

			for (int32 i = 0; i < NumFrames; ++i)
			{
				// --- Parameter smoothing ---
				SmW    += ASlow * (TgtW - SmW);
				SmDWdt += AFast * (TgtDWdt - SmDWdt);
				SmGrad += ASlow * (TgtGrad - SmGrad);
				SmVort += ASlow * (TgtVort - SmVort);
				SmInt  += ASlow * (TgtInt - SmInt);
				SmLife += ASlow * (TgtLife - SmLife);
				SmGain += ASlow * (TgtGain - SmGain);

				// =====================================================
				// L1 — Sub-bass drone. Additive, f0 = 12 + 33 W  (12-45 Hz).
				// =====================================================
				const float F0 = 12.0f + 33.0f * SmW;
				float Drone = 0.0f;
				for (int32 p = 0; p < NumDronePartials; ++p)
				{
					DronePhase[p] += F0 * DroneRatios[p] * InvSR;
					DronePhase[p] -= FMath::FloorToFloat(DronePhase[p]);
					Drone += DroneGains[p] * FMath::Sin(TwoPi * DronePhase[p]);
				}
				Drone *= 0.5f * SmW; // silent at W=0, full bed at high warp

				// =====================================================
				// L2 — FM boundary shear. Ratio pi (never resolves);
				// index = 150 x GradW^1.5 rad (spec: |gradW| x 150).
				// =====================================================
				const float Fc = 240.0f + 80.0f * SmW;
				FMCarrierPhase += Fc * InvSR;
				FMCarrierPhase -= FMath::FloorToFloat(FMCarrierPhase);
				FMModPhase += Fc * PI * InvSR;
				FMModPhase -= FMath::FloorToFloat(FMModPhase);

				const float FMIndex = 150.0f * SmGrad * FMath::Sqrt(SmGrad); // GradW^1.5
				const float Mod = FMath::Sin(TwoPi * FMModPhase);
				const float ShearRawL = FMath::Sin(TwoPi * FMCarrierPhase + FMIndex * Mod);
				const float ShearRawR = FMath::Sin(TwoPi * FMCarrierPhase + FMIndex * FMath::Sin(TwoPi * FMModPhase + 0.07f * PI));

				// §8.3 DC blocker (per channel).
				const float ShearL = DCAlpha * (DCyL + ShearRawL - DCxL);
				DCxL = ShearRawL; DCyL = ShearL;
				const float ShearR = DCAlpha * (DCyR + ShearRawR - DCxR);
				DCxR = ShearRawR; DCyR = ShearR;

				const float ShearLevel = 0.35f * FMath::Clamp(SmGrad * 1.2f + 0.02f, 0.0f, 1.0f) * FMath::Min(SmW * 4.0f, 1.0f);

				// =====================================================
				// L3 — Granular turbulence. Rate = vorticity x 800 /sec;
				// 5 ms Hann grains; 16-voice round-robin pool (§8.3).
				// =====================================================
				GrainSpawnAccum += 800.0f * SmVort * InvSR;
				while (GrainSpawnAccum >= 1.0f)
				{
					GrainSpawnAccum -= 1.0f;
					FGrain& G = Grains[NextGrainVoice];
					NextGrainVoice = (NextGrainVoice + 1) % NumGrainVoices;
					G.bActive = true;
					G.Age = 0;
					G.LenSamples = FMath::Max(8, FMath::RoundToInt32(0.005f * SampleRate));
					G.Freq = 1200.0f * FMath::Pow(2.0f, Rng.GetFraction() * 1.74f); // 1.2-4.0 kHz
					G.Phase = Rng.GetFraction();
					G.Pan = (Rng.GetFraction() * 2.0f - 1.0f) * 0.8f;
					G.Amp = 0.5f + 0.5f * Rng.GetFraction();
				}

				float GrainL = 0.0f, GrainR = 0.0f, GrainMono = 0.0f;
				for (int32 v = 0; v < NumGrainVoices; ++v)
				{
					FGrain& G = Grains[v];
					if (!G.bActive)
					{
						continue;
					}
					const float Env = 0.5f * (1.0f - FMath::Cos(TwoPi * (float)G.Age / (float)G.LenSamples)); // Hann
					G.Phase += G.Freq * InvSR;
					G.Phase -= FMath::FloorToFloat(G.Phase);
					const float Tone = FMath::Sin(TwoPi * G.Phase);
					const float Noise = Rng.GetFraction() * 2.0f - 1.0f;
					const float S = G.Amp * Env * (0.6f * Tone + 0.4f * Noise);
					const float PanR = 0.5f * (G.Pan + 1.0f);
					GrainL += S * FMath::Sqrt(1.0f - PanR);
					GrainR += S * FMath::Sqrt(PanR);
					GrainMono += S;
					if (++G.Age >= G.LenSamples)
					{
						G.bActive = false;
					}
				}
				const float GrainLevel = 0.5f;

				// =====================================================
				// L4 — Ring-modulated interference. Audio-rate carrier
				// 90-400 Hz; modulates the drone+shear bed.
				// =====================================================
				RingPhase += (90.0f + 310.0f * SmInt) * InvSR;
				RingPhase -= FMath::FloorToFloat(RingPhase);
				const float RingCarrier = FMath::Sin(TwoPi * RingPhase);
				const float RingL = (Drone + ShearL * ShearLevel) * RingCarrier;
				const float RingR = (Drone + ShearR * ShearLevel) * RingCarrier;
				const float RingLevel = 0.45f * SmInt;

				// =====================================================
				// L5 — Modal hull resonance. §8.3 locked IIR per mode:
				//   y[n] = 2 cos(w0) r y[n-1] - r^2 y[n-2] + x[n]
				//   r = exp(-pi BW / SR)
				// Damping inversely proportional to warp factor:
				//   BW = BW0 x max(1 - 0.92 W, 0.05)^1.5  -> at high W the hull rings.
				// =====================================================
				const float NoiseExcite = Rng.GetFraction() * 2.0f - 1.0f;
				const float Excite =
					  0.12f * (ShearL + ShearR) * 0.5f * ShearLevel
					+ 0.45f * GrainMono * GrainLevel
					+ 1.5f  * FMath::Abs(SmDWdt) * NoiseExcite;

				const float DampScale = FMath::Pow(FMath::Max(1.0f - 0.92f * SmW, 0.05f), 1.5f);
				float ModalL = 0.0f, ModalR = 0.0f;
				for (int32 m = 0; m < NumModes; ++m)
				{
					const float BW = ModeBW0[m] * DampScale;
					const float r = FMath::Exp(-PI * BW * InvSR);
					const float w0 = TwoPi * ModeFreqs[m] * InvSR;
					const float y = 2.0f * FMath::Cos(w0) * r * ModeY1[m] - r * r * ModeY2[m] + Excite;
					ModeY2[m] = ModeY1[m];
					ModeY1[m] = y;
					// (1 - r) compensates resonator gain growth as r -> 1.
					const float ModeOut = y * (1.0f - r) * ModeGains[m] * 6.0f;
					const float PanR = 0.5f + ((m & 1) ? 0.25f : -0.25f) * 0.5f;
					ModalL += ModeOut * FMath::Sqrt(1.0f - PanR);
					ModalR += ModeOut * FMath::Sqrt(PanR);
				}
				const float ModalLevel = 0.85f;

				// =====================================================
				// Life-support ambient floor (one-pole LP white, fades at warp).
				// =====================================================
				const float LifeRaw = Rng.GetFraction() * 2.0f - 1.0f;
				LifeLP += 0.05f * (LifeRaw - LifeLP);
				const float Life = LifeLP * 0.05f * SmLife * (1.0f - 0.85f * SmW);

				// --- Mix + §soft-clip master ---
				float L = Drone + ShearL * ShearLevel + GrainL * GrainLevel + RingL * RingLevel + ModalL * ModalLevel + Life;
				float R = Drone + ShearR * ShearLevel + GrainR * GrainLevel + RingR * RingLevel + ModalR * ModalLevel + Life;

				L = FMath::Tanh(L * 1.15f) * 0.85f * SmGain;
				R = FMath::Tanh(R * 1.15f) * 0.85f * SmGain;

				LeftData[i] = L;
				RightData[i] = R;
			}
		}

	private:
		void ResetState()
		{
			for (int32 p = 0; p < NumDronePartials; ++p) { DronePhase[p] = 0.0f; }
			FMCarrierPhase = 0.0f;
			FMModPhase = 0.0f;
			DCxL = DCyL = DCxR = DCyR = 0.0f;
			for (int32 v = 0; v < NumGrainVoices; ++v) { Grains[v] = FGrain(); }
			NextGrainVoice = 0;
			GrainSpawnAccum = 0.0f;
			RingPhase = 0.0f;
			for (int32 m = 0; m < NumModes; ++m) { ModeY1[m] = 0.0f; ModeY2[m] = 0.0f; }
			LifeLP = 0.0f;
			SmW = SmDWdt = SmGrad = SmVort = SmInt = 0.0f;
			SmLife = 1.0f;
			SmGain = 0.9f;
			Rng.Initialize(1337);
		}

		struct FGrain
		{
			bool bActive = false;
			int32 Age = 0;
			int32 LenSamples = 0;
			float Freq = 1000.0f;
			float Phase = 0.0f;
			float Pan = 0.0f;
			float Amp = 0.0f;
		};

		// Inputs
		FFloatReadRef WIn;
		FFloatReadRef DWdtIn;
		FFloatReadRef GradWIn;
		FFloatReadRef VorticityIn;
		FFloatReadRef InterferenceIn;
		FFloatReadRef LifeSupportIn;
		FFloatReadRef MasterGainIn;

		// Outputs
		FAudioBufferWriteRef OutLeft;
		FAudioBufferWriteRef OutRight;

		// Substrate
		float SampleRate;
		FRandomStream Rng;

		// L1
		float DronePhase[NumDronePartials] = {};
		// L2
		float FMCarrierPhase = 0.0f;
		float FMModPhase = 0.0f;
		float DCxL = 0.0f, DCyL = 0.0f, DCxR = 0.0f, DCyR = 0.0f;
		// L3
		FGrain Grains[NumGrainVoices];
		int32 NextGrainVoice = 0;
		float GrainSpawnAccum = 0.0f;
		// L4
		float RingPhase = 0.0f;
		// L5
		float ModeY1[NumModes] = {};
		float ModeY2[NumModes] = {};
		// Ambient
		float LifeLP = 0.0f;
		// Smoothed params
		float SmW = 0.0f, SmDWdt = 0.0f, SmGrad = 0.0f, SmVort = 0.0f, SmInt = 0.0f, SmLife = 1.0f, SmGain = 0.9f;
	};

	using FWarpHullSynthNode = TNodeFacade<FWarpHullSynthOperator>;

	METASOUND_REGISTER_NODE(FWarpHullSynthNode)
}

#undef LOCTEXT_NAMESPACE
