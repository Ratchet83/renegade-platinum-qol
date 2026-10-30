; ============================================================================
;  Repousse infini (inclus dans le module de code par main.s)
;
;  - Le compteur de pas du Repousse ne diminue plus (hook dans l'overlay 6).
;  - Utiliser un Repousse l'active sans le consommer (hook dans l'overlay 84).
;  - L'utiliser alors qu'il est actif le désactive (Repel_TurnOff ci-dessous),
;    avec le texte 62 de l'archive du Sac remplacé par build_qol.py.
; ============================================================================

; Appelée depuis TryUseRepel (Sac) à la place de « strh #0, [controller, r0] ».
;   r0 = décalage de selectedItemCount dans le contrôleur
;   r4 = contrôleur du Sac (registre préservé par TryUseRepel)
Repel_TurnOff:
    push    {r3, lr}
    mov     r1, #0
    strh    r1, [r4, r0]                ; aucun objet consommé
    mov     r0, r4
    bl      Bag_GetSpecialEncounter
    bl      SpecialEncounter_GetRepelSteps
    mov     r1, #0
    strb    r1, [r0]                    ; Repousse désactivé
    pop     {r3, pc}
