; ============================================================================
;  Trainer Kit (ancien Vs. Recorder) : menu Soigner / PC / Vol, utilisable partout
;  (inclus dans le module de code par main.s)
;
;  - Utiliser l'objet (Sac ou bouton Y) lance le script commun QOL_SCRIPT_ID,
;    ajouté par build_qol.py au fichier des scripts communs.
;  - Trois commandes de script inutilisées du jeu (0x004 à 0x006) sont
;    redirigées vers les fonctions ci-dessous, pour le Vol :
;      0x004 QoL_OpenFlyMap           ouvre la carte en mode Vol
;      0x005 QoL_FlyIfSelected var    vole vers la ville choisie (var = 1) ou var = 0
;      0x006 QoL_CheckCanFly var      var = erreur de Vol du jeu (0 = possible,
;                                     1 = pas ici, 2 = badge manquant, 3 = partenaire)
; ============================================================================

ItemMenu_StartScript            equ 0x02068541   ; sub_02068540 (Sac -> script), Thumb
ItemField_StartScript           equ 0x02068584   ; sub_02068584 (bouton Y -> script)
FieldSystem_GetScriptMemberPtr  equ 0x0203F098
FieldSystem_GetVarPointer       equ 0x0203F118
FieldSystem_IsRunningApplication equ 0x020509B4
FieldSystem_OpenTownMap         equ 0x0203D884
ScriptContext_ReadHalfWord      equ 0x0203E838
ScriptContext_Pause             equ 0x0203E764
TownMapContext_Init             equ 0x0206B70C
FieldTask_StartMapChangeFly     equ 0x02053AB4
FieldMoves_CheckFly             equ 0x02070950
MapHeader_IsFlyAllowed          equ 0x0203A1D4
Heap_Alloc                      equ 0x02018144
Heap_Free                       equ 0x020181C4

SCRIPT_CTX_FIELDSYSTEM          equ 0x80
SCRIPT_MEMBER_PARTY_MGMT_DATA   equ 0x13
HEAP_ID_FIELD2                  equ 0x0B
TOWN_MAP_CONTEXT_SIZE           equ 0x140
TOWN_MAP_MODE_FLY               equ 1
FIELDSYSTEM_LOCATION            equ 0x1C
TOWNMAP_FLY_SELECTED            equ 0x10
TOWNMAP_FLY_X                   equ 0x14
TOWNMAP_FLY_Z                   equ 0x18
TOWNMAP_FLY_MAPHEADER           equ 0x1C

; --- Utilisation de l'objet ---------------------------------------------------

; Depuis le Sac : (ItemMenuUseContext*, ItemUseContext*) -> lance le script
QoLKit_UseFromMenu:
    ldr     r2, =QOL_SCRIPT_ID
    ldr     r3, =ItemMenu_StartScript
    bx      r3

; Depuis le terrain (bouton Y) : (ItemFieldUseContext*) -> lance le script
QoLKit_UseInField:
    push    {r3, lr}
    ldr     r1, =QOL_SCRIPT_ID
    bl      ItemField_StartScript
    mov     r0, #0
    pop     {r3, pc}

; --- Commandes de script pour le Vol ----------------------------------------------

; 0x004 : ouvre la carte de la région en mode Vol (comme ScrCmd_OpenRegionMap)
QoL_ScrCmd_OpenFlyMap:
    push    {r3-r5, lr}
    mov     r5, r0                      ; r5 = contexte du script
    add     r0, #SCRIPT_CTX_FIELDSYSTEM
    ldr     r0, [r0]
    mov     r1, #SCRIPT_MEMBER_PARTY_MGMT_DATA
    bl      FieldSystem_GetScriptMemberPtr
    mov     r4, r0                      ; r4 = emplacement du contexte de carte
    mov     r0, #HEAP_ID_FIELD2
    mov     r1, #(TOWN_MAP_CONTEXT_SIZE >> 6)
    lsl     r1, r1, #6
    bl      Heap_Alloc
    str     r0, [r4]
    mov     r0, r5
    add     r0, #SCRIPT_CTX_FIELDSYSTEM
    ldr     r0, [r0]
    ldr     r1, [r4]
    mov     r2, #TOWN_MAP_MODE_FLY
    bl      TownMapContext_Init
    mov     r0, r5
    add     r0, #SCRIPT_CTX_FIELDSYSTEM
    ldr     r0, [r0]
    ldr     r1, [r4]
    bl      FieldSystem_OpenTownMap
    mov     r0, r5
    ldr     r1, =QoL_WaitFlyMap + 1
    bl      ScriptContext_Pause
    mov     r0, #1
    pop     {r3-r5, pc}

; Attente de la fermeture de la carte : recopie le choix puis libère le contexte
QoL_WaitFlyMap:
    push    {r3-r5, lr}
    add     r0, #SCRIPT_CTX_FIELDSYSTEM
    ldr     r5, [r0]                    ; r5 = système de terrain
    mov     r0, r5
    mov     r1, #SCRIPT_MEMBER_PARTY_MGMT_DATA
    bl      FieldSystem_GetScriptMemberPtr
    mov     r4, r0
    mov     r0, r5
    bl      FieldSystem_IsRunningApplication
    cmp     r0, #0
    beq     @@closed
    mov     r0, #0                      ; carte encore ouverte : on attend
    pop     {r3-r5, pc}
@@closed:
    ldr     r0, [r4]
    ldr     r1, =QoL_FlySelection
    ldr     r2, [r0, #TOWNMAP_FLY_SELECTED]
    str     r2, [r1, #0]
    ldr     r2, [r0, #TOWNMAP_FLY_MAPHEADER]
    str     r2, [r1, #4]
    ldr     r2, [r0, #TOWNMAP_FLY_X]
    str     r2, [r1, #8]
    ldr     r2, [r0, #TOWNMAP_FLY_Z]
    str     r2, [r1, #12]
    bl      Heap_Free
    mov     r0, #0
    str     r0, [r4]
    mov     r0, #1
    pop     {r3-r5, pc}

; 0x005 var : si une ville a été choisie, var = 1 et le Vol démarre ; sinon var = 0
QoL_ScrCmd_FlyIfSelected:
    push    {r4, r5, lr}
    sub     sp, #12
    mov     r5, r0
    bl      ScriptContext_ReadHalfWord
    mov     r1, r0
    mov     r0, r5
    add     r0, #SCRIPT_CTX_FIELDSYSTEM
    ldr     r0, [r0]
    bl      FieldSystem_GetVarPointer
    ldr     r4, =QoL_FlySelection
    ldr     r1, [r4, #0]
    strh    r1, [r0]
    cmp     r1, #0
    beq     @@none
    ldr     r0, [r4, #12]               ; z (case de carte) -> z * 32 + 16
    lsl     r0, r0, #5
    add     r0, #16
    str     r0, [sp, #0]
    mov     r0, #1                      ; regard vers le bas
    str     r0, [sp, #4]
    ldr     r3, [r4, #8]                ; x * 32 + 16
    lsl     r3, r3, #5
    add     r3, #16
    ldr     r1, [r4, #4]                ; carte d'arrivée
    mov     r2, #0
    mvn     r2, r2                      ; -1 : pas de warp précis
    mov     r0, r5
    add     r0, #SCRIPT_CTX_FIELDSYSTEM
    ldr     r0, [r0]
    bl      FieldTask_StartMapChangeFly
    mov     r0, #1
    b       @@ret
@@none:
    mov     r0, #0
@@ret:
    add     sp, #12
    pop     {r4, r5, pc}

; 0x006 var : var = résultat de la vérification de Vol du jeu (FieldMoves_CheckFly)
QoL_ScrCmd_CheckCanFly:
    push    {r4, r5, lr}
    sub     sp, #20
    mov     r5, r0
    bl      ScriptContext_ReadHalfWord
    mov     r1, r0
    mov     r0, r5
    add     r0, #SCRIPT_CTX_FIELDSYSTEM
    ldr     r0, [r0]
    bl      FieldSystem_GetVarPointer
    str     r0, [sp, #16]               ; variable de destination
    mov     r0, r5
    add     r0, #SCRIPT_CTX_FIELDSYSTEM
    ldr     r1, [r0]                    ; r1 = système de terrain
    ldr     r0, [r1, #FIELDSYSTEM_LOCATION]
    ldr     r0, [r0]                    ; numéro de la carte actuelle
    str     r0, [sp, #0]                ; FieldMoveContext.mapHeaderID
    str     r1, [sp, #4]                ; FieldMoveContext.fieldSystem
    mov     r0, #0
    str     r0, [sp, #8]                ; FieldMoveContext.mapObj
    str     r0, [sp, #12]               ; FieldMoveContext.usableMoves
    mov     r0, sp
    bl      FieldMoves_CheckFly
.if QOL_TEST_FLY_NO_BADGE
    ; ROM de test : « badge manquant » est ignoré, mais comme le jeu teste le badge
    ; avant la carte, on refait ensuite le test « Vol autorisé sur cette carte ».
    cmp     r0, #2
    bne     @@keep
    ldr     r0, [sp, #0]                ; numéro de la carte
    bl      MapHeader_IsFlyAllowed
    cmp     r0, #0
    beq     @@deny
    mov     r0, #0
    b       @@keep
@@deny:
    mov     r0, #1                      ; FIELD_MOVE_ERROR_LOCATION
@@keep:
.endif
    ldr     r1, [sp, #16]
    strh    r0, [r1]
    mov     r0, #0
    add     sp, #20
    pop     {r4, r5, pc}

.pool

.align 4
QoL_FlySelection:                       ; choisie ?, carte, x, z
    .word 0, 0, 0, 0
