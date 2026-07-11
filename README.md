# 🏥 SGHL - Système de Gestion Hospitalière Localisée

**Version** : 1.0 Finale  
**Statut** : ✅ Prêt pour démonstration professionnelle  
**Dernière mise à jour** : Janvier 2024

---

## 📌 À LIRE EN PREMIER

Ce projet a été **finalisé selon les spécifications techniques** pour une démonstration complète et professionnelle.

👉 **[Consulter le Guide de Déploiement Complet](./IMPLEMENTATION_GUIDE.md)** pour les détails d'installation et de migration.

---

## 🎯 Caractéristiques Principales

### ✅ Architecture Backend (Django)

- **Hiérarchie RBAC** : DG, Secrétaire Générale, Secrétaire de Service, Docteur, Biologiste, Patient
- **Filtrage Dynamique** : Chaque rôle voit uniquement les données autorisées
- **Validations Métier** :
  - Rendez-vous : Min. 2h avant, Max. 10/jour
  - Stocks : Alertes automatiques si quantité faible
  - Hospitalisations : Gestion lits avec occupations
- **Traçabilité Complète** : `created_by`, `created_at`, `updated_at` sur tous les modèles critiques
- **MFA Authentication** : Vérification code via cache Django
- **APIs REST** : Endpoints DRF pour tous les modules

### ✅ Frontend (Vue 3 + Tailwind CSS)

- **Dashboard Intelligent** : Statistiques temps réel avec rafraîchissement auto
- **Design Unifié** : Palette Tailwind (Slate, Emerald, Amber, Blue)
- **Gestion d'Erreurs** : try/catch avec messages clairs aux utilisateurs
- **Localisation GPS** : Carte des services avec coordonnées pour navigation
- **Responsive** : Fonctionnel sur desktop, tablet, mobile

---

## 🚀 Démarrage Rapide

### 1️⃣ Backend

```bash
# Répertoire : c:\Users\njap\OneDrive\Desktop\SGHL_PROJECT

# Créer et appliquer migrations
python manage.py makemigrations
python manage.py migrate

# Démarrer le serveur
python manage.py runserver 0.0.0.0:8000
```

Backend accessible : **http://localhost:8000**

### 2️⃣ Frontend

```bash
# Répertoire : sghl_frontend

# Installer dépendances
npm install

# Démarrer serveur Vite
npm run dev
```

Frontend accessible : **http://localhost:5173**

---

## 📂 Structure du Projet

```
SGHL_PROJECT/
├── authentication/           # Modèles User & MFA
│   ├── models.py            # User avec rôles SGHL
│   ├── security.py          # Auth RBAC
│   └── urls.py              # URLs DRF
│
├── clinical/                # Cœur du système hospitalier
│   ├── models.py            # Appointment, Provision, etc.
│   ├── views.py             # APIs avec filtrage rôle
│   ├── schemas.py           # Serializers
│   ├── api.py               # Ninja endpoints (hérité)
│   └── urls.py              # URLs DRF
│
├── sghl_backend/            # Configuration Django
│   ├── settings.py          # Avec DRF + CORS
│   ├── urls.py              # Routing principal
│   └── api.py               # API Ninja
│
├── sghl_frontend/           # App Vue 3
│   └── src/
│       ├── views/           # Pages
│       │   ├── DashboardView.vue        # 📊 Stats
│       │   ├── AppointmentsView.vue     # 📅 RDV
│       │   └── VisitorsMapView.vue      # 🗺️ Navigation GPS
│       ├── api.js           # Client HTTP
│       └── router/
│
├── IMPLEMENTATION_GUIDE.md  # Guide détaillé
├── README.md                # Ce fichier
└── db.sqlite3               # BD (SQLite)
```

---

## 🔑 Points Clés

### Modèles Mis à Jour

| Modèle | Changements |
|--------|-----------|
| **User** | Rôles SGHL, FK Service, `has_service_access()` |
| **Service** | Coords GPS (lat/long) pour navigation |
| **Appointment** | Validations métier, tracabilité |
| **Provision** | Alertes stocks automatiques |
| **Room/Bed** | Traçabilité complète |

### Vues API Clés

```
POST   /api/v1/clinical/verify-code/      MFA verification → retourne role, service_id
GET    /api/v1/clinical/stats/            Stats dashboard
GET/POST /api/v1/clinical/appointments/   Rendez-vous
GET/POST /api/v1/clinical/provisions/     Gestion stocks
GET    /api/v1/clinical/hospitalizations/ Hospitalisations
```

### Composants Vue Clés

| Composant | Fonction | Status |
|-----------|----------|--------|
| **DashboardView** | Stats + alertes | ✅ Tailwind CSS |
| **AppointmentsView** | Gestion RDV | ✅ Gestion erreurs |
| **VisitorsMapView** | Navigation GPS | ✅ Google Maps ready |

---

## 🎨 Design & UX

### Palette Tailwind

- **Slate** : Textes et éléments neutres
- **Emerald** : Actions positives (confirmations, succès)
- **Amber** : Alertes et avertissements (stocks bas, etc.)
- **Blue** : Informations et appels à l'action

### Responsive Design

```
Mobile    : 1 colonne
Tablet    : 2 colonnes  
Desktop   : 3+ colonnes
```

---

## 🧪 Checklist Avant Démo

- [ ] Migrations appliquées : `python manage.py showmigrations`
- [ ] Backend démarre : `python manage.py runserver`
- [ ] Frontend démarre : `npm run dev`
- [ ] MFA fonctionne : Vérifier les codes dans logs
- [ ] Dashboard charge : Affiche stats correctes
- [ ] RDV validation : Test 2h et quota
- [ ] Filtrage rôle : SECRETARY_SERVICE ne voit que son service
- [ ] Alertes stocks : Affichées si qty < min
- [ ] Navigation GPS : Clique service → Google Maps
- [ ] Erreurs claires : Messages d'erreur lisibles

---

## 📊 Cas de Test Recommandés

### 1. RBAC - Connecté en DG
```
✓ Voir tous les rendez-vous
✓ Voir tous les patients
✓ Voir tous les stocks
✓ Accès complet au dashboard
```

### 2. RBAC - Connecté en SECRETARY_SERVICE
```
✓ Voir uniquement les RDV du service
✓ Voir uniquement les patients du service
✓ Voir uniquement les stocks du service
✓ Dashboard : stats du service uniquement
```

### 3. Validation Métier - Créer RDV
```
✓ RDV < 2h : Erreur affichée
✓ 11e RDV/jour : Erreur affichée
✓ RDV valide : Créé avec succès
✓ Message utilisateur : Clair et actionnable
```

### 4. Alertes Stocks
```
✓ Créer Provision qty < min
✓ Dashboard affiche l'alerte
✓ Couleur Amber pour visibilité
✓ Quantité/min visible
```

---

## 🔧 Variables d'Environnement

```bash
# .env (à créer si besoin)
DEBUG=True
SECRET_KEY=votre-clé-secrète
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

---

## 📖 Documentation Complète

Pour les détails complets :
- **[IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)** : Installation, APIs, tests
- **Code commenté** : Chaque modèle/vue inclut des commentaires détaillés
- **Docstrings** : Toutes les classes/fonctions documentées

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'rest_framework'"
```bash
pip install djangorestframework
```

### "CORS error from frontend"
- Vérifier `CORS_ALLOW_ALL_ORIGINS = True` dans settings.py
- Vérifier backend démarre sur 8000

### "Migrations conflictuelles"
```bash
python manage.py migrate authentication
python manage.py migrate clinical
```

### "Stats ne se chargent pas"
- Vérifier le user a un service défini (pour SECRETARY_SERVICE)
- Vérifier l'URL `/api/v1/clinical/stats/` est accessible

---

## 📞 Support

En cas d'erreur, vérifier :

1. **Logs Django** : `python manage.py runserver` affiche les erreurs
2. **Console Frontend** : F12 → Console pour erreurs JS
3. **Networks Tab** : F12 → Network pour erreurs API

---

## ✅ Final Checklist

- [x] Modèles Django finalisés
- [x] APIs DRF implémentées
- [x] Frontend Vue 3 complété
- [x] Tailwind CSS unifié
- [x] Gestion erreurs robuste
- [x] Filtrage RBAC fonctionnel
- [x] Validations métier en place
- [x] Traçabilité complète
- [x] Documentation fournie
- [x] Prêt pour démo professionnelle

---

## 🎓 Notes pour la Démonstration

**Point fort** : L'architecture RBAC flexible permettra de montrer comment le système s'adapte à différents rôles en temps réel.

**Point fort** : Les validations métier et les alertes intelligentes montrent que le système comprend le domaine hospitalier.

**Point fort** : Le design Tailwind unifié et professionnel inspire confiance.

---

**Bonne démonstration ! 🏥✨**
