# 📋 SGHL - Guide de Finalisation et Déploiement

**Système de Gestion Hospitalière Localisée (SGHL)**  
*Déploiement pour démonstration professionnelle*

---

## 🎯 Vue d'Ensemble

Ce projet a été finalisé selon les spécifications techniques pour une démonstration professionnelle complète. Tous les composants backend et frontend sont prêts pour migration et déploiement.

### Composants Clés

✅ **Architecture RBAC** (DG, Secrétaire Générale, Secrétaire de Service, Docteur, Biologiste, Patient)  
✅ **Filtrage dynamique des données par rôle et service**  
✅ **Validation métier complète** (RDV 2h avant, quota 10/jour, alertes stocks)  
✅ **Dashboard avec statistiques temps réel**  
✅ **Localisation GPS des services** pour navigation visiteurs  
✅ **MFA Authentication** avec code via cache Django  
✅ **Style unifié Tailwind CSS** sur toutes les vues  

---

## 🚀 Instructions de Déploiement

### 1. Mise à Jour des Migrations

```bash
# Naviguer dans le répertoire du projet
cd c:\Users\njap\OneDrive\Desktop\SGHL_PROJECT

# Créer les migrations pour tous les changements de modèles
python manage.py makemigrations authentication
python manage.py makemigrations clinical

# Afficher les migrations à appliquer (vérification)
python manage.py showmigrations

# Appliquer toutes les migrations
python manage.py migrate
```

### 2. Démarrage du Serveur Backend

```bash
# Démarrer le serveur Django
python manage.py runserver 0.0.0.0:8000
```

### 3. Démarrage du Serveur Frontend

```bash
# Naviguer dans le répertoire frontend
cd sghl_frontend

# Installer les dépendances (si nécessaire)
npm install

# Démarrer le serveur Vite
npm run dev
```

Le frontend sera accessible sur `http://localhost:5173` (ou port spécifié).

---

## 📊 Architecture Backend

### Modèles Mis à Jour

#### **User (authentication/models.py)**
- Rôles : `DG`, `SECRETARY_GENERAL`, `SECRETARY_SERVICE`, `DOCTOR`, `BIOLOGIST`, `PATIENT`
- FK `service` pour filtrage des données
- Méthode `has_service_access(obj)` pour vérifications

#### **Service (clinical/models.py)**
- Nouveaux champs GPS : `location_lat`, `location_long`
- Support 24h/24 pour urgences/labo
- Métadonnées : `created_at`, `updated_at`

#### **Appointment (clinical/models.py)**
- **Validations métier** dans `clean()` :
  - Interdiction RDV < 2h avant
  - Limite 10 RDV/jour
- Traçabilité : `created_by`, `created_at`, `updated_at`
- Lien au service

#### **Provision (clinical/models.py)**
- Gestion des stocks avec **alertes automatiques**
- Seuil configurable `min_quantity_alert`
- Détection automatique stocks faibles

#### **SupportTask (clinical/models.py)**
- Types : CLEANING, SECURITY, MAINTENANCE
- Intégration GPS pour localisation
- Status workflow : PENDING → IN_PROGRESS → COMPLETED

### Vues API (clinical/views.py)

#### **VerifyCodeView (POST /api/v1/clinical/verify-code/)**
```json
Response:
{
  "token": "jwt_token",
  "role": "DG|SECRETARY_GENERAL|SECRETARY_SERVICE|DOCTOR|BIOLOGIST",
  "user_id": 1,
  "service_id": 5,
  "service_name": "Urgences"
}
```

#### **StatsView (GET /api/v1/clinical/stats/)**
```json
Response:
{
  "date": "2024-01-15",
  "appointments_count": 12,
  "hospitalized_count": 5,
  "low_stock_count": 3,
  "low_stock_items": [
    {
      "id": 1,
      "name": "Masques chirurgicaux",
      "quantity": 8,
      "service": "Urgences"
    }
  ]
}
```

#### **AppointmentListView (GET/POST /api/v1/clinical/appointments/)**
- Création avec validation métier automatique
- Gestion erreurs : délai insuffisant, quota atteint
- Filtrage automatique par rôle

#### **Autres Vues**
- `ProvisionListView` : Gestion stocks
- `HospitalizationListView` : Hospitalisations avec filtrage
- `SupportTaskListView` : Tâches support (nettoyage, sécurité)
- `ConsultationListView` : Historique consultations

### Filtrage par Rôle (FilteredQuerySetMixin)

```python
# DG & SECRETARY_GENERAL : Accès complet
# SECRETARY_SERVICE : Données du service uniquement
# DOCTOR : Ses propres rendez-vous/consultations
# BIOLOGIST : Consultations du service
```

---

## 🎨 Frontend - Vue.js Components

### **DashboardView.vue**

**Caractéristiques** :
- 3 cartes de statistiques (RDV, hospitalisations, alertes)
- Section alertes stocks détaillée
- Quick actions vers autres modules
- Rafraîchissement auto toutes les 30s

**Palette Tailwind** :
- 📅 Bleu (RDV)
- 🏥 Émeraude (Hospitalisations)
- ⚠️ Ambre (Alertes)
- ℹ️ Bleu (Informations)

### **AppointmentsView.vue**

**Fonctionnalités** :
- Table avec statuts colorés (Planifié, Confirmé, Annulé, Terminé)
- Gestion d'erreurs exhaustive avec `try/catch`
- Affichage des erreurs métier :
  - "Moins de 2h avant le créneau"
  - "Capacité maximale atteinte"
  - Autres erreurs détaillées
- Formulaire modal avec validation
- Actions : Confirmer, Annuler

### **VisitorsMapView.vue** (Nouveau)

**Intégration GPS** :
- Affichage coordonnées latitude/longitude
- Cliquable : Ouvre Google Maps
- Liste services avec statut 24h/24
- Vue chambres et lits associés
- Préparation pour Leaflet/OpenStreetMap

**Structure** :
```
┌─────────────────────────┬──────────────────┐
│     Carte (Placeholder)  │  Services        │
│  pour Leaflet/OSM       │  Détails         │
│  [Future Integration]   │  Localisation    │
├─────────────────────────┴──────────────────┤
│  Chambres & Lits du Service Sélectionné   │
└─────────────────────────────────────────────┘
```

---

## 🔐 Sécurité et Traçabilité

### MFA Flow

```
1. User → POST /api/v1/clinical/verify-code/ avec user_id + code
2. Backend → Vérifie code via cache Django
3. Backend ← Retourne role, service_id pour filtrage client
4. Frontend → Utilise role pour contrôle d'accès UI
5. Backend ← Filtre données API par rôle/service
```

### Traçabilité Complète

Tous les modèles critiques incluent :
- `created_by` : FK User qui a créé l'enregistrement
- `created_at` : DateTimeField auto_now_add
- `updated_at` : DateTimeField auto_now

---

## 🧪 Tests et Validations

### Tests Manuels Recommandés

#### 1. **Authentification MFA**
```bash
# Login et vérifier le retour du rôle
curl -X POST http://localhost:8000/api/v1/clinical/verify-code/ \
  -d '{"user_id": 1, "code": "123456"}'
```

#### 2. **Validation Métier - RDV**
- Essayer de créer un RDV < 2h : Doit échouer
- Créer 10 RDV le même jour : Le 11e doit échouer
- Vérifier l'affichage des erreurs dans AppointmentsView

#### 3. **Filtrage par Rôle**
- Connecter en tant que SECRETARY_SERVICE
- Vérifier que seules les données du service s'affichent
- Connecter en tant que DG : Toutes les données visibles

#### 4. **Alertes Stocks**
- Créer une Provision avec quantity < min_quantity_alert
- Dashboard doit afficher l'alerte
- Vérifier la liste des items en alerte

#### 5. **Dashboard Stats**
- Vérifier le comptage des RDV confirmés du jour
- Vérifier le comptage des hospitalisations actives
- Vérifier le comptage des stocks bas

---

## 📝 Checklist Pré-Déploiement

- [ ] Migrations créées et appliquées sans erreurs
- [ ] Backend démarre sans errors (port 8000)
- [ ] Frontend démarre sans errors (port 5173)
- [ ] MFA vérifie correctement les codes
- [ ] Dashboard charge les statistiques
- [ ] AppointmentsView affiche les RDV
- [ ] Filtrage fonctionne par rôle
- [ ] Alertes stocks s'affichent
- [ ] VisitorsMapView affiche les services
- [ ] Navigation GPS fonctionne (Google Maps)
- [ ] Style Tailwind unifié sur toutes les pages
- [ ] Erreurs métier affichées correctement aux utilisateurs

---

## 🐛 Troubleshooting

### Migration échoue
```bash
# Vérifier les dépendances FK
python manage.py check

# Réinitialiser en dev (ATTENTION - supprime les données)
python manage.py migrate --fake-initial
```

### API retourne 404
```bash
# Vérifier les URLs sont incluses
cat sghl_backend/urls.py
# Doit inclure : path('api/v1/clinical/', include('clinical.urls'))
```

### Frontend ne se connecte pas au backend
```bash
# Vérifier le serveur tourne
curl http://localhost:8000/admin/

# Vérifier les CORS settings dans settings.py
# ALLOWED_HOSTS doit inclure le frontend URL
```

### Erreurs de permission 403
```bash
# Vérifier l'utilisateur a le rôle correct
# Vérifier FilteredQuerySetMixin pour le modèle
# Vérifier user.service est défini pour SECRETARY_SERVICE
```

---

## 📚 Ressources

- **Django Docs** : https://docs.djangoproject.com/
- **Django REST Framework** : https://www.django-rest-framework.org/
- **Vue 3 Docs** : https://vuejs.org/
- **Tailwind CSS** : https://tailwindcss.com/

---

## 🎓 Points Clés pour la Démo

**À démontrer** :

1. **RBAC Fonctionnel**
   - Montrer DG voit tout
   - Montrer SECRETARY_SERVICE voit son service uniquement

2. **Validations Métier**
   - Essayer RDV < 2h → Erreur
   - Essayer 11e RDV jour → Erreur
   - Vérifier messages d'erreur clairs

3. **Dashboard Intelligent**
   - Stats temps réel
   - Alertes stocks colorées
   - Rafraîchissement automatique

4. **Navigation GPS**
   - Cliquer service → Coordonnées affichées
   - "Ouvrir dans Maps" → Google Maps

5. **Style Professionnel**
   - Design Tailwind épuré
   - Cohérence des couleurs
   - Responsive design

---

**Dernière mise à jour** : 2024  
**Statut** : ✅ Prêt pour démonstration professionnelle
