; ============================================================================
;  Renegade Platinum QoL : code ajouté au jeu (base : Pokémon Platine US Rev 1)
;  Assemblé avec armips par scripts/build_qol.py (-equ QOL_OVERLAY <numéro>)
;
;  Un nouveau module de code (overlay QOL_OVERLAY) est chargé au démarrage à
;  0x023C8000 : cette zone de RAM, au-dessus des tas mémoire du jeu, n'est
;  jamais utilisée. Le code des fonctionnalités y vit ; le jeu y saute depuis
;  quelques appels modifiés (« hooks »), listés plus bas.
; ============================================================================

.nds
.thumb

; --- Fonctions et données du jeu (adresses vérifiées dans la ROM) -----------
Pokemon_GetValue                equ 0x02074470
Pokemon_SetValue                equ 0x02074B30
Pokemon_GetSpeciesBaseExpAt     equ 0x02075AD0
SaveData_Ptr                    equ 0x020245A4
SaveData_GetTrainerInfo         equ 0x02025E38
SaveData_GetVarsFlags           equ 0x020507E4
SystemFlag_CheckGameCompleted   equ 0x0206A954
SpecialEncounter_GetRepelSteps  equ 0x0202D9CC
LoadOverlayNormal               equ 0x0200671C
PM_GetBackLight                 equ 0x020CB29C   ; code ARM
sSavedBacklightState            equ 0x02101D20
Bag_GetSpecialEncounter         equ 0x0223B9E4   ; overlay 84 (Sac)

; ============================================================================
;  Le module de code
; ============================================================================
.create "build/qol_overlay.bin", 0x023C8000

; Appelée depuis NitroMain à la place de PM_GetBackLight(&sSavedBacklightState, NULL)
; (l'instruction d'origine a été déplacée ici pour faire de la place).
QoL_BootInit:
    push    {r3, lr}
    ldr     r0, =sSavedBacklightState
    mov     r1, #0
    ldr     r3, =PM_GetBackLight
    blx     r3
    pop     {r3, pc}
.pool

.include "levelcap.s"
.include "repel.s"

.align 4
.close

; ============================================================================
;  ARM9
; ============================================================================
.open "build/arm9.bin", 0x02000000

; NitroMain : SetGBACartridgeVersion(0) (redondant, la variable vaut déjà 0)
; + PM_GetBackLight(...) -> chargement du module + QoL_BootInit
.org 0x02000C96
    mov     r0, #0                      ; MI_PROCESSOR_ARM9
    mov     r1, #QOL_OVERLAY
    bl      LoadOverlayNormal
    bl      QoL_BootInit
    nop
.if . != 0x02000CA4
    .error "Le code de démarrage ne fait pas exactement 14 octets"
.endif

; [Level cap] Pokemon_CheckItemEffects : « niveau < 100 » pour le Super Bonbon
.org 0x0209656A
    bl      LevelCap_AdjustedLevel

; [Level cap] Pokemon_ApplyItemEffects : « niveau < 100 » pour le Super Bonbon
.org 0x02096AA6
    bl      LevelCap_AdjustedLevel

.close

; ============================================================================
;  Overlay 6 (terrain : rencontres, pas)
; ============================================================================
.open "build/overlay_0006.bin", 0x0223E140

; [Repousse] Repel_UpdateSteps : « steps-- » remplacé par « steps = steps »
.org 0x02246C06
    add     r1, r1, #0

.close

; ============================================================================
;  Overlay 16 (combat)
; ============================================================================
.open "build/overlay_0016.bin", 0x0223B140

; [Level cap] BattleScript_GetExpTask : « PV > 0 et niveau != 100 »
.org 0x02249004
    bl      LevelCap_AdjustedLevel

; [Level cap] BattleScript_GetExpTask : Pokemon_SetValue(mon, EXPERIENCE, &newExp)
.org 0x022490EA
    bl      LevelCap_SetExp

.close

; ============================================================================
;  Overlay 84 (Sac)
; ============================================================================
.open "build/overlay_0084.bin", 0x0223B5A0

; [Repousse] TryUseRepel, Repousse déjà actif : « selectedItemCount = 0 »
; -> Repel_TurnOff (désactive le Repousse, sans consommer d'objet)
.org 0x0223DCB0
    bl      Repel_TurnOff

; [Repousse] TryUseRepel, activation : « selectedItemCount = 1 » -> 0
; (l'objet n'est pas consommé)
.org 0x0223DCDA
    mov     r1, #0

.close
