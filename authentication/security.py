from ninja.security import HttpBearer
from django.core.signing import Signer, BadSignature
from authentication.models import User
from authentication.roles import expand_allowed_roles
from ninja.errors import HttpError

signer = Signer(salt='sghl-auth')


class RoleBasedAuth(HttpBearer):
    def __init__(self, allowed_roles: list = None):
        super().__init__()
        self.allowed_roles = allowed_roles or []

    def authenticate(self, request, token):
        try:
            data = signer.unsign(token)
            user_id, username, _timestamp = data.split(':')
            user = User.objects.get(id=user_id, username=username)

            # DG : accès total
            if user.role == 'DG':
                request.auth_user = user
                return token

            if self.allowed_roles:
                allowed = expand_allowed_roles(self.allowed_roles)
                if user.role not in allowed:
                    raise HttpError(403, f"Accès refusé pour le rôle : {user.role}")

            request.auth_user = user
            return token

        except (BadSignature, ValueError):
            raise HttpError(401, "Token invalide ou corrompu.")
        except User.DoesNotExist:
            raise HttpError(401, "Utilisateur introuvable.")
