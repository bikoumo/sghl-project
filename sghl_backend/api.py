from ninja import NinjaAPI
from clinical.api import router as clinical_router
from authentication.api import router as auth_router
from finance_logistics.api import router as finance_router

api = NinjaAPI(title="SGHL API", version="1.0.0", urls_namespace="api-v1")

# Branchement des différents modules de l'hôpital
api.add_router("/auth", auth_router)
api.add_router("/clinical", clinical_router)
api.add_router("/finance", finance_router)
