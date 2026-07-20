#!/usr/bin/env python3
"""Memoire des acquereurs - le test du chien de Jean.

Ce que ca fait, en trois temps :
  1. LIRE   : chaque vocal de debrief est transforme en fiche besoin structuree,
              y compris les criteres QUALITATIFS que personne ne note jamais.
  2. GARDER : les fiches sont stockees, elles ne se perdent pas.
  3. ALERTER: chaque nouveau mandat est confronte a toute la memoire, et
              declenche un rappel quand ca correspond, meme des mois apres.

Ce qu'aucun logiciel metier ne fait : matcher sur "lisiere de foret" ou
"la belle-mere a moins de 20 minutes", parce que ce ne sont pas des champs.
"""

import os
import re
import json
import glob
import argparse
from datetime import date

from cerveau import demander

RACINE = os.path.dirname(os.path.abspath(__file__))
DOSSIER_VOCAUX = os.path.join(RACINE, "donnees_demo", "vocaux")
FICHIER_BIENS = os.path.join(RACINE, "donnees_demo", "biens.json")
MEMOIRE = os.path.join(RACINE, "memoire_acquereurs.json")
RAPPROCHEMENTS = os.path.join(RACINE, "rapprochements.json")

# Le choix du fournisseur et du modele vit desormais dans cerveau.py


# --------------------------------------------------------------------------- #
# 1. LIRE : le vocal devient une fiche besoin
# --------------------------------------------------------------------------- #
CONSIGNE_EXTRACTION = (
    "Tu es l'assistant d'un agent immobilier. On te donne le vocal de debrief "
    "qu'il dicte apres un appel ou une visite. Tu en extrais la fiche besoin de "
    "l'acquereur.\n\n"
    "REGLE CAPITALE : les criteres qui font vendre ne sont presque jamais les "
    "criteres chiffres. Ce sont les criteres qualitatifs, souvent glisses au "
    "milieu d'une phrase : promener le chien dans les bois, emmener les enfants "
    "a l'ecole a pied, etre a moins de vingt minutes d'un parent age, avoir de "
    "la lumiere pour travailler. Tu dois TOUS les capturer, avec le verbatim "
    "exact de l'agent. C'est ce qui differencie cette fiche d'un formulaire.\n\n"
    "N'invente jamais. Si une information est absente, mets null.\n\n"
    "Reponds UNIQUEMENT en JSON valide, sans texte autour :\n"
    '{"acquereur":"", "date_echange":"", "type_bien":"", "budget_min":0, '
    '"budget_max":0, "chambres_min":0, "secteurs":[], '
    '"criteres_durs":["critere factuel et filtrable"], '
    '"criteres_qualitatifs":[{"besoin":"formule courte", '
    '"verbatim":"ce que l agent a dicte", "pourquoi":"la raison humaine"}], '
    '"redhibitoires":[], "maturite":"", "note_agent":""}'
)


def _json_depuis(texte):
    bloc = re.search(r"\{.*\}", texte, re.DOTALL)
    return json.loads(bloc.group(0) if bloc else texte)


def extraire_fiche(vocal, nom_fichier):
    reponse = demander(CONSIGNE_EXTRACTION, "VOCAL DE DEBRIEF :\n\n" + vocal)
    fiche = _json_depuis(reponse.strip())
    fiche["source"] = os.path.basename(nom_fichier)
    return fiche


# --------------------------------------------------------------------------- #
# 2. ALERTER : le mandat entrant est confronte a la memoire
# --------------------------------------------------------------------------- #
CONSIGNE_MATCH = (
    "Tu compares un bien qui vient d'entrer au portefeuille d'une agence avec "
    "la fiche besoin d'un acquereur rencontre il y a parfois plusieurs mois.\n\n"
    "Ton travail n'est PAS de filtrer sur le prix et le nombre de pieces, "
    "n'importe quel logiciel sait le faire. Ton travail est de reperer si le "
    "bien repond aux besoins QUALITATIFS, meme quand l'annonce ne le dit pas "
    "avec les memes mots. Exemple : une annonce qui mentionne un portillon "
    "ouvrant sur les sentiers de la foret repond au besoin d'un acquereur qui "
    "voulait promener son chien dans les bois le matin, alors qu'aucun mot-cle "
    "ne correspond.\n\n"
    "Sois honnete et severe : un score eleve doit etre merite. Si le budget ou "
    "le type de bien ne collent pas, le score est bas quoi qu'il arrive.\n\n"
    "Reponds UNIQUEMENT en JSON valide :\n"
    '{"score":0, "verdict":"", "declencheur":"le critere qualitatif qui fait '
    'mouche", "preuve_annonce":"extrait exact de l annonce", '
    '"rappel_verbatim":"ce que l acquereur avait dit", '
    '"message_agent":"la phrase a lire par l agent avant de decrocher", '
    '"reserves":[]}'
)


def confronter(fiche, bien):
    invite = (
        "FICHE BESOIN DE L'ACQUEREUR :\n" + json.dumps(fiche, ensure_ascii=False, indent=2)
        + "\n\nBIEN QUI VIENT D'ENTRER AU PORTEFEUILLE :\n"
        + json.dumps(bien, ensure_ascii=False, indent=2)
    )
    resultat = _json_depuis(demander(CONSIGNE_MATCH, invite).strip())
    resultat["ref_bien"] = bien["ref"]
    resultat["acquereur"] = fiche.get("acquereur")
    resultat["anciennete_besoin_jours"] = _anciennete(fiche, bien)
    return resultat


def _anciennete(fiche, bien):
    """Nombre de jours entre le besoin exprime et l'entree du bien.

    Calcule a partir des dates reelles, jamais demande a l'IA : une date
    inventee ferait perdre toute credibilite a l'argument "128 jours apres".
    """
    from datetime import datetime
    try:
        d1 = datetime.strptime(fiche.get("date_echange", ""), "%Y-%m-%d")
        d2 = datetime.strptime(bien.get("entree_portefeuille", ""), "%Y-%m-%d")
        return max((d2 - d1).days, 0)
    except (ValueError, TypeError):
        return 0


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def commande_lire():
    """Incremental : on ne relit QUE les vocaux jamais traites.

    Un vocal deja en memoire n'est pas repasse a l'IA. La memoire ne bouge
    donc pas toute seule, et le quota Gemini n'est pas gaspille.
    """
    fiches = []
    if os.path.exists(MEMOIRE):
        with open(MEMOIRE, "r", encoding="utf-8") as fh:
            fiches = json.load(fh)
    deja = {f.get("source") for f in fiches}

    nouveaux = 0
    for chemin in sorted(glob.glob(os.path.join(DOSSIER_VOCAUX, "*.txt"))):
        nom = os.path.basename(chemin)
        if nom in deja:
            continue
        with open(chemin, "r", encoding="utf-8") as fh:
            vocal = fh.read()
        print("Nouveau vocal : " + nom)
        fiches.append(extraire_fiche(vocal, chemin))
        nouveaux += 1

    if nouveaux:
        with open(MEMOIRE, "w", encoding="utf-8") as fh:
            json.dump(fiches, fh, ensure_ascii=False, indent=2)
    print(str(nouveaux) + " nouveau(x) vocal(aux) lu(s). "
          + str(len(fiches)) + " acquereurs en memoire.")


def commande_alerter(seuil):
    with open(MEMOIRE, "r", encoding="utf-8") as fh:
        fiches = json.load(fh)
    with open(FICHIER_BIENS, "r", encoding="utf-8") as fh:
        biens = json.load(fh)

    # Incremental : on ne confronte que les couples jamais evalues.
    # Un nouveau bien ou un nouvel acquereur cree de nouveaux couples, eux seuls
    # passent a l'IA. Les rapprochements deja calcules sont conserves tels quels.
    existants = []
    if os.path.exists(RAPPROCHEMENTS):
        with open(RAPPROCHEMENTS, "r", encoding="utf-8") as fh:
            existants = json.load(fh)
    deja = {(str(r.get("acquereur")), str(r.get("ref_bien"))) for r in existants}

    calcules = 0
    for bien in biens:
        for fiche in fiches:
            if (str(fiche.get("acquereur")), str(bien["ref"])) in deja:
                continue
            existants.append(confronter(fiche, bien))
            calcules += 1

    if calcules:
        with open(RAPPROCHEMENTS, "w", encoding="utf-8") as fh:
            json.dump(existants, fh, ensure_ascii=False, indent=2)
    print(str(calcules) + " nouveau(x) couple(s) evalue(s).")

    alertes = [r for r in existants if r.get("score", 0) >= seuil]
    alertes.sort(key=lambda x: x.get("score", 0), reverse=True)

    print("\n" + "=" * 66)
    print("  RAPPELS DU JOUR  " + date.today().strftime("%d/%m/%Y"))
    print("=" * 66)
    if not alertes:
        print("Aucun rapprochement au-dessus de " + str(seuil) + ".")
    for a in alertes:
        print("\n[" + str(a["score"]) + "/100]  " + str(a["acquereur"]) + "  ->  " + a["ref_bien"])
        print("  " + a.get("message_agent", ""))
        print("  Declencheur : " + str(a.get("declencheur")))
        print("  Il avait dit : \"" + str(a.get("rappel_verbatim")) + "\"")
        print("  Dans l'annonce : \"" + str(a.get("preuve_annonce")) + "\"")
        for reserve in a.get("reserves", []):
            print("  Reserve : " + reserve)
    return alertes


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Memoire des acquereurs")
    p.add_argument("commande", choices=["lire", "alerter", "tout"])
    p.add_argument("--seuil", type=int, default=70)
    args = p.parse_args()

    if args.commande in ("lire", "tout"):
        commande_lire()
    if args.commande in ("alerter", "tout"):
        commande_alerter(args.seuil)
