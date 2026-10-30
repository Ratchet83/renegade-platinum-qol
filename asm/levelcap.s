; ============================================================================
;  Level caps (inclus dans le module de code par main.s)
;
;  - Trois tests « niveau < 100 » / « niveau != 100 » du jeu lisent le niveau
;    via LevelCap_AdjustedLevel, qui renvoie min(niveau + 100 - cap, 100).
;    Pour le jeu, un Pokémon au cap est donc « niveau 100 ».
;  - En combat, l'expérience gagnée est plafonnée à celle du niveau du cap.
;  - Cap = table[nombre de badges] ; 100 (aucun cap) une fois le jeu terminé.
; ============================================================================

TRAINERINFO_BADGES              equ 0x1A
MON_DATA_SPECIES                equ 5
MON_DATA_EXPERIENCE             equ 8

; int LevelCap_Get(void) : niveau maximum actuel
LevelCap_Get:
    push    {r4, lr}
    bl      SaveData_Ptr
    mov     r4, r0
    bl      SaveData_GetVarsFlags
    bl      SystemFlag_CheckGameCompleted
    cmp     r0, #0
    bne     @@no_cap
    mov     r0, r4
    bl      SaveData_GetTrainerInfo
    ldrb    r1, [r0, #TRAINERINFO_BADGES]
    mov     r0, #0                      ; r0 = nombre de badges
@@count:
    cmp     r1, #0
    beq     @@lookup
    lsr     r1, r1, #1                  ; bit sorti dans la retenue
    bcc     @@count
    add     r0, #1
    b       @@count
@@lookup:
    ldr     r1, =LevelCapTable
    ldrb    r0, [r1, r0]
    pop     {r4, pc}
@@no_cap:
    mov     r0, #100
    pop     {r4, pc}

; u32 LevelCap_AdjustedLevel(Pokemon *mon, int param, void *dest)
; Remplace Pokemon_GetValue(mon, MON_DATA_LEVEL, NULL) devant un test à 100.
LevelCap_AdjustedLevel:
    push    {r4, lr}
    bl      Pokemon_GetValue            ; r0 = vrai niveau
    mov     r4, r0
    bl      LevelCap_Get                ; r0 = cap
    sub     r4, r4, r0
    add     r4, #100                    ; niveau + 100 - cap
    cmp     r4, #100
    ble     @@done
    mov     r4, #100                    ; au-dessus du cap : traité comme 100
@@done:
    mov     r0, r4
    pop     {r4, pc}

; void LevelCap_SetExp(Pokemon *mon, int param, u32 *exp)
; Remplace Pokemon_SetValue(mon, MON_DATA_EXPERIENCE, &newExp) en combat :
; l'expérience ne dépasse pas celle du niveau du cap.
LevelCap_SetExp:
    push    {r4-r6, lr}
    mov     r4, r0
    mov     r6, r2
    bl      LevelCap_Get
    cmp     r0, #100
    bhs     @@store
    mov     r5, r0                      ; r5 = cap
    mov     r0, r4
    mov     r1, #MON_DATA_SPECIES
    mov     r2, #0
    bl      Pokemon_GetValue            ; r0 = espèce
    mov     r1, r5
    bl      Pokemon_GetSpeciesBaseExpAt ; r0 = expérience minimale du niveau cap
    ldr     r1, [r6]
    cmp     r1, r0
    bls     @@store
    str     r0, [r6]
@@store:
    mov     r0, r4
    mov     r1, #MON_DATA_EXPERIENCE
    mov     r2, r6
    bl      Pokemon_SetValue
    pop     {r4-r6, pc}

.pool

; Niveau maximum selon le nombre de badges (0 à 8)
LevelCapTable:
    .byte 16    ; 0 badge  -> Pierrick
    .byte 26    ; 1 badge  -> Flo
    .byte 33    ; 2 badges -> Kiméra
    .byte 39    ; 3 badges -> Mélina
    .byte 44    ; 4 badges -> Lovis
    .byte 53    ; 5 badges -> Charles
    .byte 56    ; 6 badges -> Gladys
    .byte 62    ; 7 badges -> Tanguy
    .byte 78    ; 8 badges -> Ligue Pokémon
.align 2
