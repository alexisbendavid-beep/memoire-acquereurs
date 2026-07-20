# Mémoire des acquéreurs — « le test du chien de Jean »

Preuve construite pour Christophe Raas (Agence RG, Garches/Vaucresson).

## Ce que ça démontre

Les logiciels métier matchent sur des **champs** : prix, surface, pièces, code postal.
Ils ne peuvent pas retenir « lisière de forêt », « la belle-mère à moins de 20 minutes »
ou « elle ne peut pas travailler dans le noir ». Ces informations vivent dans les
conversations, puis se perdent.

Ce moteur les capture, les garde, et déclenche le rappel le jour où un mandat correspond.

## Fichiers

- `demo_raas.html` — **la pièce à montrer**. Déroule vocal brut → fiche extraite → alertes.
- `memoire_acquereurs.py` — le moteur réel (extraction + rapprochement via Gemini).
- `generer_demo.py` — génère la page HTML depuis les données.
- `donnees_demo/vocaux/` — 5 debriefs dictés, réalistes.
- `donnees_demo/biens.json` — 6 mandats entrants.
- `memoire_acquereurs.json` — les 5 fiches besoin extraites (14 critères qualitatifs).
- `rapprochements.json` — 5 rapprochements + 1 rejet motivé.

## Lancer le moteur en réel

```bash
export GEMINI_API_KEY="votre_clé"        # la même que les bots Abrek et Altenis
pip install google-generativeai
python3 memoire_acquereurs.py tout --seuil 70
```

`lire` extrait les fiches des vocaux. `alerter` confronte les mandats à la mémoire.
`tout` enchaîne les deux.

## Le résultat clé

Jean Vasseur, vu le 14 mars, cherchait une lisière de forêt pour promener son labrador.
**128 jours plus tard**, le 12 allée des Cèdres à Vaucresson entre au portefeuille : son
portillon ouvre sur la forêt de Fausses-Reposes. Score 94/100.

Et le moteur **écarte** le 17 avenue du Général Leclerc (score 31) alors qu'un filtre
classique l'aurait proposé : maison, 4 chambres, 1 180 000 € dans le budget. Mais avenue
passante et rénovation complète, ses deux rédhibitoires.

## Garde-fou RGPD

On n'enregistre jamais les clients. C'est l'agent qui dicte son debrief après coup.
Même matière première, aucun risque juridique.
