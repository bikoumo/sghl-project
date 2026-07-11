from ninja.security import HttpBearer
from django.core.signing import Signer, BadSignature
from authentication.models import User
from ninja.errors import HttpError

signer = Signer(salt='sghl-auth')

class RoleBasedAuth(HttpBearer):
    def __init__(self, allowed_roles: list = None):
        super().__init__()
        self.allowed_roles = allowed_roles or []

    def authenticate(self, request, token):
        try:
            # 1. Vérifier la validité de la signature du token
            # Le token doit contenir "id:username:timestamp"
            data = signer.unsign(token)
            user_id, username, timestamp = data.split(':')
            
            # 2. Récupérer l'utilisateur
            user = User.objects.get(id=user_id, username=username)
            
            # 3. Intégration DG (Accès total)
            if user.role == 'DG':
                request.auth_user = user
                return token
            
            # 4. Vérification des rôles
            if self.allowed_roles and user.role not in self.allowed_roles:
                raise HttpError(403, f"Accès refusé pour le rôle : {user.role}")
                
            request.auth_user = user
            return token
            
        except (BadSignature, ValueError):
            raise HttpError(401, "Token invalide ou corrompu.")
        except User.DoesNotExist:
            raise HttpError(401, "Utilisateur introuvable.")