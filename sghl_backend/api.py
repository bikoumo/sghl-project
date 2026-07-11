from ninja import NinjaAPI
from clinical.api import router as clinical_router
from authentication.api import router as auth_router # <-- Ajoute cette ligne

api = NinjaAPI(title="SGHL API", version="1.0.0", urls_namespace="api-v1")

# Branchement des différents modules de l'hôpital
api.add_router("/auth/", auth_router)            # <-- Ajoute cette ligne
api.add_router("/clinical/", clinical_router)