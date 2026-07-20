# Migrer le robot sur GitHub — pas à pas

Objectif : le robot tourne dans le cloud toutes les 30 minutes, comme tes bots
Abrek et Altenis. Ton ordinateur peut être éteint.

Compte GitHub : `alexisbendavid-beep`. Clé Gemini : la même que les deux autres bots.

---

## Étape 1 — Créer le dépôt (2 minutes)

1. Va sur **https://github.com/new**
2. Dans **Repository name**, tape exactement : `memoire-acquereurs`
3. Juste en dessous, coche **Private** (surtout pas Public, il y a des données clients)
4. Ne coche RIEN d'autre. Pas de README, pas de .gitignore, pas de licence.
5. Clique le bouton vert **Create repository**

Tu arrives sur une page qui dit « Quick setup ». Laisse-la ouverte.

---

## Étape 2 — Envoyer les fichiers (3 minutes)

Sur cette page, clique le lien **uploading an existing file**
(dans la phrase « …or push an existing repository from the command line »,
juste au-dessus il y a « uploading an existing file »).

Si tu ne le trouves pas, va directement sur :
`https://github.com/alexisbendavid-beep/memoire-acquereurs/upload/main`

1. Ouvre le dossier `memoire-acquereurs` sur ton Mac
2. **Sélectionne tout** (Cmd+A) et **fais-le glisser** dans la zone du navigateur
3. Attends que la liste des fichiers apparaisse (environ 15 fichiers)
4. En bas, dans **Commit changes**, laisse le message par défaut
5. Clique **Commit changes**

⚠️ **Vérifie que ces fichiers sont bien montés** :
- `memoire_acquereurs.py`
- `generer_demo.py`
- `generer_pdf_raas.py`
- `requirements.txt`
- le dossier `donnees_demo` (avec `vocaux` dedans)
- le dossier `.github` (avec `workflows` dedans)

Le dossier `.github` commence par un point, donc il est **caché sur Mac**.
Si tu ne le vois pas dans le Finder : appuie sur **Cmd + Maj + .** (point)
pour afficher les fichiers cachés, puis refais le glisser-déposer.

Sans ce dossier, le robot ne tournera jamais.

---

## Étape 3 — Donner les 3 clés au robot (4 minutes)

Le robot a besoin de la clé Gemini pour réfléchir, et de ton Gmail pour t'envoyer
l'alerte. On ne les met JAMAIS dans le code.

Va sur :
`https://github.com/alexisbendavid-beep/memoire-acquereurs/settings/secrets/actions`

Puis, **trois fois de suite**, clique le bouton vert **New repository secret** :

| Name (à taper exactement) | Secret (à coller) |
|---|---|
| `GEMINI_API_KEY` | ta clé Gemini, celle qui commence par `AIza` |
| `GMAIL_ADDRESS` | `alexis.bendavid@gmail.com` |
| `GMAIL_APP_PASSWORD` | `lqxwolvvxftlwwie` |

Ce sont exactement les mêmes que tes bots Abrek et Altenis.

Tu dois voir trois lignes avec un cadenas. Si tu n'en vois que deux, il en manque
une et le robot échouera.

**À qui le robot écrit-il ?** À toi, et à toi seul, sur `alexis.bendavid@gmail.com`.
Aucun client ne reçoit jamais rien. Christophe Raas n'a pas besoin d'un compte
GitHub ni de quoi que ce soit : il recevra simplement un email de ta part le jour
où tu décideras de lui en envoyer un.

---

## Étape 4 — Lancer le robot une première fois (1 minute)

1. Va sur :
   `https://github.com/alexisbendavid-beep/memoire-acquereurs/actions`
2. Dans la colonne de gauche, clique **Memoire des acquereurs**
3. À droite, clique le bouton **Run workflow**, puis le bouton vert
   **Run workflow** qui apparaît dans le petit menu
4. Attends 30 secondes, puis **recharge la page** (Cmd+R)

**Si tu vois une pastille verte** : c'est gagné, le robot tourne.
**Si tu vois une pastille rouge** : clique dessus, envoie-moi ce qui est écrit
en rouge, je corrige.

Puis **va voir ta boîte Gmail**. Tu dois avoir reçu un mail intitulé
« Mémoire des acquéreurs : 5 acquéreurs à rappeler ». C'est ce mail que tu
montreras à Christophe Raas sur ton téléphone.

⚠️ Le robot ne t'écrit que lorsqu'il a du **nouveau**. Au deuxième passage il se
taira, c'est normal et voulu : sinon tu recevrais le même mail toutes les
30 minutes. Pour refaire une démonstration, supprime le fichier
`alertes_envoyees.json` dans le dépôt et relance le workflow.

---

## Étape 5 — Récupérer ce que le robot a produit

Clique sur le run vert. Tout en bas de la page, section **Artifacts**,
il y a un fichier `memoire-acquereurs` à télécharger. Dedans :

- `rapprochements.json` — les rappels trouvés
- `demo_raas.html` — la page de démonstration
- `Memoire_des_acquereurs_Agence_RG.pdf` — le dossier pour Christophe Raas

---

## C'est fini

À partir de maintenant le robot tourne **tout seul, toutes les 30 minutes, 24h/24**.
Ton ordinateur peut être éteint. Rien ne part vers un client sans toi : il n'écrit
qu'à toi.

### Ce qu'il consomme, et pourquoi ça ne s'emballe pas

Le robot est **incrémental**. Il ne repasse jamais à l'IA ce qu'il a déjà compris.

- Un vocal déjà lu n'est pas relu. Sa fiche besoin ne bouge plus.
- Un couple acquéreur/bien déjà évalué n'est pas réévalué.
- Il ne t'envoie un mail que s'il a du **nouveau** à te signaler.

Concrètement : le premier passage fait le rattrapage, les suivants ne consomment
rien tant que tu n'ajoutes pas de matière. Le jour où tu déposes un vocal ou un
bien, il est traité dans la demi-heure.

Sans ça, tu brûlerais ton quota Gemini gratuit en une journée et tu recevrais le
même mail 48 fois.

---

## Pour ajouter un vrai acquéreur plus tard

1. Va dans `donnees_demo/vocaux/` sur GitHub
2. Clique **Add file** puis **Create new file**
3. Nomme-le par exemple `2026-07-21_madame_lefevre.txt`
4. Colle le texte du vocal (transcrit), même mal écrit, même sans accents
5. **Commit changes**

Au prochain passage, le robot le lira et le confrontera à tous les mandats.

## Pour ajouter un vrai bien

Même principe, mais tu modifies `donnees_demo/biens.json`.
Copie un bloc existant entre accolades, change les valeurs, garde les virgules.
Si tu as un doute sur la syntaxe, envoie-moi le bien en texte, je le formate.
