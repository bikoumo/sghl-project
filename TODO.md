# TODO - Implémentation Facturation & Visite

## Backend (Django)
- [x] 1. `clinical/models.py` — Ajouter CARD dans PAYMENT_METHODS + champ card_last_four
- [x] 2. `clinical/schemas.py` — Ajouter InvoiceCreateSchema, InvoiceLineSchema, enrichir PayInvoiceSchema
- [x] 3. `clinical/api.py` — 
  - [x] 3a. Ajouter endpoint POST /invoices/create (création manuelle facture)
  - [x] 3b. Ajouter GET /patients/search?q= (recherche textuelle patient)
  - [x] 3c. Enrichir pay_invoice avec logique carte bancaire
  - [x] 3d. Corriger bug "Cannot filter query once slice taken"

## Frontend (Vue 3)
- [x] 6. `src/api.js` — Ajouter méthodes createInvoice, searchPatients (déjà présentes)
- [x] 7. Créer `src/views/VisitView.vue` — ✅ Nouvelle page visite/recherche avec formulaire de création de facture
- [x] 8. `src/router/index.js` — ✅ Ajouter route /visit
- [x] 9. `src/views/PaymentsView.vue` — ✅ Ajouter mode CARD, bouton "+ Créer une facture" qui pointe vers /visit

