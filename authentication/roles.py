"""Rôles canoniques SGHL et alias UI/legacy."""

from __future__ import annotations

# Valeurs stockées en base (authentication.User.ROLE_CHOICES)
CANONICAL_ROLES = frozenset({
    'DG',
    'SECRETARY_GENERAL',
    'SECRETARY_SERVICE',
    'DOCTOR',
    'BIOLOGIST',
    'PATIENT',
})

# Alias formulaires / anciens endpoints → rôle DB
ROLE_ALIASES = {
    'ADMIN': 'DG',
    'SUPERADMIN': 'DG',
    'SECRETARY': 'SECRETARY_GENERAL',
    'RECEPCIONIST': 'SECRETARY_SERVICE',
    'RECEPTIONIST': 'SECRETARY_SERVICE',
    'PHARMACIST': 'BIOLOGIST',
    'OTHER': 'BIOLOGIST',
}

# Libellés pour messages d'erreur
ROLE_LABELS = {
    'DG': 'Directeur Général',
    'SECRETARY_GENERAL': 'Secrétaire Générale',
    'SECRETARY_SERVICE': 'Secrétaire de Service',
    'DOCTOR': 'Médecin',
    'BIOLOGIST': 'Biologiste',
    'PATIENT': 'Patient',
}

# Groupes pratiques pour les endpoints
STAFF_ROLES = ['DG', 'SECRETARY_GENERAL', 'SECRETARY_SERVICE', 'DOCTOR', 'BIOLOGIST']
SECRETARY_ROLES = ['SECRETARY_GENERAL', 'SECRETARY_SERVICE']
ADMIN_ROLES = ['DG']
CLINICAL_READ_ROLES = ['DG', 'SECRETARY_GENERAL', 'SECRETARY_SERVICE', 'DOCTOR', 'BIOLOGIST']
CLINICAL_WRITE_ROLES = ['DG', 'DOCTOR']
BILLING_ROLES = ['DG', 'SECRETARY_GENERAL', 'SECRETARY_SERVICE']
PHARMACY_ROLES = ['DG', 'BIOLOGIST', 'DOCTOR', 'SECRETARY_SERVICE']
ADMISSION_ROLES = ['DG', 'SECRETARY_GENERAL', 'SECRETARY_SERVICE', 'DOCTOR']
ALL_ROLES = list(CANONICAL_ROLES)


def canonicalize_role(role: str | None) -> str | None:
    if not role:
        return None
    normalized = str(role).strip().upper()
    return ROLE_ALIASES.get(normalized, normalized)


def expand_allowed_roles(allowed_roles: list[str] | None) -> set[str]:
    """Normalise une liste d'allowed_roles (avec alias) vers les rôles DB."""
    if not allowed_roles:
        return set()
    expanded: set[str] = set()
    for role in allowed_roles:
        canonical = canonicalize_role(role)
        if not canonical:
            continue
        expanded.add(canonical)
        # Réceptionniste historique → les deux profils secrétariat
        if role and role.upper() in {'RECEPCIONIST', 'RECEPTIONIST'}:
            expanded.update(SECRETARY_ROLES)
        if role and role.upper() == 'SECRETARY':
            expanded.update(SECRETARY_ROLES)
        if canonical == 'SECRETARY_SERVICE':
            expanded.add('SECRETARY_GENERAL')
    return expanded


def role_label(role: str | None) -> str:
    canonical = canonicalize_role(role) or ''
    return ROLE_LABELS.get(canonical, canonical or 'Inconnu')
