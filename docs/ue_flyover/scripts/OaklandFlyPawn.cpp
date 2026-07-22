// OaklandFlyPawn.cpp  (project 26-029, UE 5.8) — see OaklandFlyPawn.h for the
// tunables table. Movement + look + speed ramp + soft bounds are polled from the
// PlayerController each tick, so no Enhanced-Input / project input assets needed.
#include "OaklandFlyPawn.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/FloatingPawnMovement.h"
#include "GameFramework/PlayerController.h"
#include "Components/SceneComponent.h"
#include "Components/PrimitiveComponent.h"
#include "EngineUtils.h"
#include "Engine/World.h"

AOaklandFlyPawn::AOaklandFlyPawn()
{
	PrimaryActorTick.bCanEverTick = true;

	RootScene = CreateDefaultSubobject<USceneComponent>(TEXT("RootScene"));
	SetRootComponent(RootScene);

	Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
	Camera->SetupAttachment(RootScene);

	Movement = CreateDefaultSubobject<UFloatingPawnMovement>(TEXT("Movement"));
	Movement->UpdatedComponent = RootScene;   // pure flight, no collision component

	// The controller drives the pawn's view; movement flies where you look.
	bUseControllerRotationYaw = true;
	bUseControllerRotationPitch = true;
	bUseControllerRotationRoll = false;

	AutoPossessPlayer = EAutoReceiveInput::Player0; // works in PIE even without GameMode wiring
}

void AOaklandFlyPawn::BeginPlay()
{
	Super::BeginPlay();

	// Seed the movement component from the tunables.
	if (Movement)
	{
		Movement->MaxSpeed = CruiseSpeed;
		Movement->Acceleration = Acceleration;
		Movement->Deceleration = Deceleration;
	}

	if (bUseManualBounds)
	{
		WorldBounds = FBox(ManualBoundsMin, ManualBoundsMax);
		bBoundsValid = WorldBounds.IsValid != 0;
	}
	else if (bAutoComputeBounds)
	{
		ComputeWorldBounds();
	}

	if (APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		if (bRequireRMBToLook)
		{
			PC->bShowMouseCursor = true;
			PC->SetInputMode(FInputModeGameAndUI());
		}
		else
		{
			PC->bShowMouseCursor = false;
			PC->SetInputMode(FInputModeGameOnly());
		}
	}
}

// Union the bounds of every rendered splat/mesh in the level (skips the huge
// sky/atmosphere and this pawn), so a v2 tile swap needs no change here.
void AOaklandFlyPawn::ComputeWorldBounds()
{
	const double SanityCapCm = 2000000.0; // 20 km — excludes SkyAtmosphere-scale bounds
	FBox Acc(ForceInit);
	int32 Counted = 0;

	if (UWorld* World = GetWorld())
	{
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			AActor* A = *It;
			if (!A || A == this)
			{
				continue;
			}
			TInlineComponentArray<UPrimitiveComponent*> Prims(A);
			for (UPrimitiveComponent* Prim : Prims)
			{
				if (!Prim || !Prim->IsRegistered())
				{
					continue;
				}
				const float R = Prim->Bounds.SphereRadius;
				if (R < 1.f || R > SanityCapCm)
				{
					continue;
				}
				Acc += Prim->Bounds.GetBox();
				++Counted;
			}
		}
	}

	WorldBounds = Acc;
	bBoundsValid = (Counted > 0 && WorldBounds.IsValid != 0);
	UE_LOG(LogTemp, Log, TEXT("[OaklandFlyPawn] auto world bounds: valid=%d comps=%d min=%s max=%s"),
		bBoundsValid ? 1 : 0, Counted,
		*WorldBounds.Min.ToString(), *WorldBounds.Max.ToString());
}

void AOaklandFlyPawn::ApplySpeedRamp(APlayerController* PC)
{
	if (PC->WasInputKeyJustPressed(EKeys::MouseScrollUp))
	{
		CruiseSpeed = FMath::Clamp(CruiseSpeed * ScrollSpeedStep, SpeedMin, SpeedMax);
	}
	if (PC->WasInputKeyJustPressed(EKeys::MouseScrollDown))
	{
		CruiseSpeed = FMath::Clamp(CruiseSpeed / ScrollSpeedStep, SpeedMin, SpeedMax);
	}

	const bool bBoost = PC->IsInputKeyDown(EKeys::LeftShift) || PC->IsInputKeyDown(EKeys::RightShift);
	if (Movement)
	{
		Movement->MaxSpeed = bBoost ? CruiseSpeed * BoostMultiplier : CruiseSpeed;
		Movement->Acceleration = Acceleration;
		Movement->Deceleration = Deceleration;
	}
}

void AOaklandFlyPawn::ApplyLook(APlayerController* PC, float Dt)
{
	// RMB-look grammar: manage capture on the RMB edges so mouse delta reads.
	if (bRequireRMBToLook)
	{
		if (PC->WasInputKeyJustPressed(EKeys::RightMouseButton))
		{
			PC->SetInputMode(FInputModeGameOnly());
			PC->bShowMouseCursor = false;
		}
		else if (PC->WasInputKeyJustReleased(EKeys::RightMouseButton))
		{
			PC->SetInputMode(FInputModeGameAndUI());
			PC->bShowMouseCursor = true;
		}
	}

	const bool bLooking = !bRequireRMBToLook || PC->IsInputKeyDown(EKeys::RightMouseButton);
	if (!bLooking)
	{
		SmoothedLook = FVector::ZeroVector;
		return;
	}

	float Mx = 0.f, My = 0.f;
	PC->GetInputMouseDelta(Mx, My);
	const FVector Raw(My, Mx, 0.f); // X = pitch source, Y = yaw source

	if (LookSmoothing > 0.f)
	{
		const float Alpha = FMath::Clamp(LookSmoothing * Dt, 0.f, 1.f);
		SmoothedLook = FMath::Lerp(SmoothedLook, Raw, Alpha);
	}
	else
	{
		SmoothedLook = Raw;
	}

	const float YawDelta = SmoothedLook.Y * LookSensitivity;
	const float PitchDelta = SmoothedLook.X * LookSensitivity * (bInvertPitch ? 1.f : -1.f);

	AddControllerYawInput(YawDelta);
	AddControllerPitchInput(PitchDelta);

	ApplyBanking(YawDelta, Dt);
}

void AOaklandFlyPawn::ApplyBanking(float YawDelta, float Dt)
{
	if (!bEnableBanking || !Camera)
	{
		return;
	}
	// Roll into the turn (opposite the yaw), subtle and eased.
	const float Target = FMath::Clamp(-YawDelta * 2.f, -MaxBankAngle, MaxBankAngle);
	CurrentBank = FMath::FInterpTo(CurrentBank, Target, Dt, BankInterpSpeed);
	Camera->SetRelativeRotation(FRotator(0.f, 0.f, CurrentBank));
}

void AOaklandFlyPawn::ApplyMovement(APlayerController* PC, float Dt)
{
	const FVector Fwd = GetActorForwardVector();
	const FVector Right = GetActorRightVector();
	const FVector WorldUp = FVector::UpVector;

	if (PC->IsInputKeyDown(EKeys::W)) { AddMovementInput(Fwd, 1.f); }
	if (PC->IsInputKeyDown(EKeys::S)) { AddMovementInput(Fwd, -1.f); }
	if (PC->IsInputKeyDown(EKeys::D)) { AddMovementInput(Right, 1.f); }
	if (PC->IsInputKeyDown(EKeys::A)) { AddMovementInput(Right, -1.f); }
	if (PC->IsInputKeyDown(EKeys::E) || PC->IsInputKeyDown(EKeys::SpaceBar)) { AddMovementInput(WorldUp, 1.f); }
	if (PC->IsInputKeyDown(EKeys::Q) || PC->IsInputKeyDown(EKeys::LeftControl)) { AddMovementInput(WorldUp, -1.f); }
}

void AOaklandFlyPawn::ApplySoftBounds(float Dt)
{
	if (!bBoundsValid)
	{
		return;
	}
	FBox Expanded = WorldBounds.ExpandBy(
		FVector(BoundsMarginCm, BoundsMarginCm, BoundsVerticalMarginCm));

	const FVector Loc = GetActorLocation();
	if (Expanded.IsInsideOrOn(Loc))
	{
		return;
	}
	// Soft spring: ease the camera back toward the nearest point inside the box.
	const FVector Closest = Expanded.GetClosestPointTo(Loc);
	const FVector Eased = FMath::VInterpTo(Loc, Closest, Dt, BoundsPushStrength);
	SetActorLocation(Eased, false);
}

void AOaklandFlyPawn::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	APlayerController* PC = Cast<APlayerController>(GetController());
	if (!PC)
	{
		return;
	}
	ApplySpeedRamp(PC);
	ApplyLook(PC, DeltaSeconds);
	ApplyMovement(PC, DeltaSeconds);
	ApplySoftBounds(DeltaSeconds);
}

void AOaklandFlyPawn::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	// Intentionally empty: all input is polled from the PlayerController in Tick,
	// so the pawn needs no Enhanced-Input or project input mappings to function.
}
