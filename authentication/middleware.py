from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from authentication.security import signer
from django.contrib.auth import get_user_model

User = get_user_model()


class RBACMiddleware(MiddlewareMixin):
    """Bloque les secrétaires sur les endpoints cliniques sensibles sous /api/v2/."""

    def process_request(self, request):
        try:
            path = request.path or ''
            if not path.startswith('/api/v2/clinical/'):
                return None

            method = (request.method or 'GET').upper()
            sensitive = False

            if '/record' in path or '/exam' in path:
                sensitive = True
            elif path.rstrip('/').endswith('/consultations') and method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
                sensitive = True
            # Pharmacie : vente autorisée pour secrétaires de service (stock géré côté API)

            if not sensitive:
                return None

            auth = request.META.get('HTTP_AUTHORIZATION', '')
            if not auth.startswith('Bearer '):
                return None

            token = auth.split(' ', 1)[1].strip()
            try:
                data = signer.unsign(token)
                user_id, username, _ = data.split(':')
                user = User.objects.filter(id=user_id, username=username).first()
            except Exception:
                return None

            role = (getattr(user, 'role', '') or '').upper()
            if user and role.startswith('SECRETARY'):
                return HttpResponseForbidden(
                    'Accès interdit : rôle secrétaire non autorisé sur cet endpoint clinique sensible'
                )
        except Exception:
            return None

        return None
