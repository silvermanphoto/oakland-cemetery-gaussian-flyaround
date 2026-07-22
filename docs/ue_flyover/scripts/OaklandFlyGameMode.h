// OaklandFlyGameMode.h — GameMode whose default pawn is the smooth fly camera.
// Set as the map's GameMode Override (World Settings) so Play/PIE spawns the
// AOaklandFlyPawn. Project 26-029, UE 5.8.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "OaklandFlyGameMode.generated.h"

UCLASS()
class OAKLANDFLYAROUND_API AOaklandFlyGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AOaklandFlyGameMode();
};
