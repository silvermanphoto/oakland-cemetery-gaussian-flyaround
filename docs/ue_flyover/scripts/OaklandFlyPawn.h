// =============================================================================
//  OaklandFlyPawn.h  —  smooth spectator-style fly camera for the Oakland
//  Cemetery gaussian-splat world (project 26-029, UE 5.8).
//
//  A collision-free flying pawn with real inertia (ease-in / ease-out via a
//  FloatingPawnMovement component), a scroll-wheel speed ramp, subtle banked
//  turns, and SOFT world bounds that keep the camera inside the site volume.
//  The bounds are computed AT PLAY from the union of the splat tiles' own
//  bounds, so a later v2 tile swap needs no change here.
//
//  ---------------------------------------------------------------------------
//  TUNABLES  (Joel's one-file taste pass — every "feel" number lives here as a
//  UPROPERTY default; edit a value + recompile, OR override per-instance in the
//  Blueprint child BP_OaklandFlyPawn, OR re-stamp headless with pawn_tunables.py)
//  ---------------------------------------------------------------------------
//   Speed          CruiseSpeed 1200 cm/s · SpeedMin 150 · SpeedMax 12000
//                  ScrollSpeedStep 1.15 (x/tick of the wheel) · BoostMultiplier 3.0 (Shift)
//   Inertia        Acceleration 2400 cm/s^2 · Deceleration 2400  (higher = snappier / lower = floatier)
//   Look           LookSensitivity 1.0 deg/count · LookSmoothing 12.0 (higher = crisper, lower = silkier)
//                  InvertPitch false · bRequireRMBToLook true (UE-editor grammar: hold RMB to look+fly)
//   Banking        bEnableBanking true · MaxBankAngle 8 deg · BankInterpSpeed 3.0  (subtle by design)
//   Soft bounds    bAutoComputeBounds true · BoundsMarginCm 6000 (60 m past the splats)
//                  BoundsPushStrength 3.0 · BoundsVerticalMarginCm 12000 (120 m head/floor room)
//                  bUseManualBounds false + ManualBoundsMin/Max (only if auto is turned off)
//   Movement keys  W/S fwd-back · A/D strafe · E or Space up · Q or Ctrl down (world up/down)
//
//  Nothing about the tiles, environment, or lighting is set here — this is the
//  pawn only. Keys are polled directly from the PlayerController each tick, so
//  the pawn needs no Enhanced-Input or project input assets to function.
// =============================================================================
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "OaklandFlyPawn.generated.h"

class UCameraComponent;
class UFloatingPawnMovement;

UCLASS()
class OAKLANDFLYAROUND_API AOaklandFlyPawn : public APawn
{
	GENERATED_BODY()

public:
	AOaklandFlyPawn();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	// ---- Components -------------------------------------------------------
	UPROPERTY(VisibleAnywhere, Category = "Flight")
	USceneComponent* RootScene;

	UPROPERTY(VisibleAnywhere, Category = "Flight")
	UCameraComponent* Camera;

	UPROPERTY(VisibleAnywhere, Category = "Flight")
	UFloatingPawnMovement* Movement;

	// ---- TUNABLES: Speed --------------------------------------------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Speed")
	float CruiseSpeed = 1200.f;      // cm/s, the wheel-ramped max ground speed

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Speed")
	float SpeedMin = 150.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Speed")
	float SpeedMax = 12000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Speed")
	float ScrollSpeedStep = 1.15f;   // multiply/divide CruiseSpeed per wheel notch

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Speed")
	float BoostMultiplier = 3.0f;    // hold Shift

	// ---- TUNABLES: Inertia (ease-in / ease-out) --------------------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Inertia")
	float Acceleration = 2400.f;     // cm/s^2

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Inertia")
	float Deceleration = 2400.f;     // cm/s^2 (glide-out when input released)

	// ---- TUNABLES: Look ---------------------------------------------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Look")
	float LookSensitivity = 1.0f;    // degrees per mouse count

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Look")
	float LookSmoothing = 12.0f;     // higher = crisper, lower = silkier (0 = raw)

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Look")
	bool bInvertPitch = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Look")
	bool bRequireRMBToLook = true;   // true = hold Right Mouse to look+fly (UE-editor grammar)

	// ---- TUNABLES: Banking ------------------------------------------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Banking")
	bool bEnableBanking = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Banking")
	float MaxBankAngle = 8.0f;       // degrees of camera roll into a turn

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Banking")
	float BankInterpSpeed = 3.0f;

	// ---- TUNABLES: Soft world bounds -------------------------------------
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Bounds")
	bool bAutoComputeBounds = true;  // union of splat tile bounds at BeginPlay (v2-proof)

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Bounds")
	float BoundsMarginCm = 6000.f;   // horizontal breathing room past the splats (60 m)

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Bounds")
	float BoundsVerticalMarginCm = 12000.f; // extra head / floor room (120 m)

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Bounds")
	float BoundsPushStrength = 3.0f; // how firmly the camera is eased back inside

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Bounds")
	bool bUseManualBounds = false;   // ignore auto; use the two vectors below

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Bounds")
	FVector ManualBoundsMin = FVector(-40000.f, -45000.f, -3000.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flight|Tunables|Bounds")
	FVector ManualBoundsMax = FVector(40000.f, 50000.f, 12000.f);

protected:
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

private:
	FVector SmoothedLook = FVector::ZeroVector; // (pitch, yaw) smoothed
	float CurrentBank = 0.f;
	FBox WorldBounds = FBox(ForceInit);
	bool bBoundsValid = false;

	void ComputeWorldBounds();
	void ApplyLook(class APlayerController* PC, float Dt);
	void ApplyMovement(class APlayerController* PC, float Dt);
	void ApplySpeedRamp(class APlayerController* PC);
	void ApplySoftBounds(float Dt);
	void ApplyBanking(float YawDelta, float Dt);
};
