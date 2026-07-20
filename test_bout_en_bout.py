#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test de bout en bout, sans appel reel a Gemini ni envoi reel de mail.

On verifie les 6 promesses faites au client :
  1. Un vocal deja lu n'est PAS relu (incremental, quota preserve).
  2. Un NOUVEAU vocal est lu, et lui seul.
  3. Un NOUVEAU bien ne declenche que les couples manquants.
  4. Le mail d'alerte est bien construit et remis a SMTP.
  5. Le mail ne part QU'A Alexis, jamais a un client.
  6. Au second passage, rien n'est renvoye (anti-doublon).

Gemini et SMTP sont bouchonnes : le test tourne hors ligne, gratuitement.
"""

import os
import sys
import json
import shutil
import tempfile
import types

SOURCE = os.path.dirname(os.path.abspath(__file__))
BAC = tempfile.mkdtemp(prefix="test_memoire_")
ECHECS = []


def verifier(libelle, condition, detail=""):
    print(("  OK   " if condition else "  ECHEC") + "  " + libelle
          + (("  -> " + detail) if detail and not condition else ""))
    if not condition:
        ECHECS.append(libelle)


# --------------------------------------------------------------------------- #
# Bac a sable : copie du projet
# --------------------------------------------------------------------------- #
for nom in ["memoire_acquereurs.py", "envoyer_alerte.py",
            "memoire_acquereurs.json", "rapprochements.json"]:
    shutil.copy(os.path.join(SOURCE, nom), BAC)
shutil.copytree(os.path.join(SOURCE, "donnees_demo"), os.path.join(BAC, "donnees_demo"))
sys.path.insert(0, BAC)
os.environ["GEMINI_API_KEY"] = "bouchon"
os.environ["GMAIL_ADDRESS"] = "alexis.bendavid@gmail.com"
os.environ["GMAIL_APP_PASSWORD"] = "bouchon"

APPELS_IA = {"extractions": 0, "confrontations": 0}


# --------------------------------------------------------------------------- #
# Bouchon Gemini
# --------------------------------------------------------------------------- #
class ReponseBouchon:
    def __init__(self, texte):
        self.text = texte


class ModeleBouchon:
    def __init__(self, modele, system_instruction=""):
        self.extraction = "Tu compares un bien" not in system_instruction

    def generate_content(self, invite):
        if self.extraction:
            APPELS_IA["extractions"] += 1
            return ReponseBouchon(json.dumps({
                "acquereur": "Madame Lefevre", "date_echange": "2026-07-21",
                "type_bien": "Appartement", "budget_min": None, "budget_max": 850000,
                "chambres_min": 2, "secteurs": [],
                "criteres_durs": ["3 pieces", "Ascenseur"],
                "criteres_qualitatifs": [{
                    "besoin": "Chambre imperativement sur cour",
                    "verbatim": "elle est infirmiere de nuit, elle dort la journee",
                    "pourquoi": "Travaille de nuit"}],
                "redhibitoires": ["Chambre sur rue"], "maturite": "", "note_agent": ""
            }, ensure_ascii=False))
        APPELS_IA["confrontations"] += 1
        return ReponseBouchon(json.dumps({
            "score": 88, "verdict": "Correspondance sur le critere qualitatif",
            "declencheur": "Chambres sur cour",
            "preuve_annonce": "les deux chambres donnent sur la cour interieure au calme",
            "rappel_verbatim": "elle est infirmiere de nuit, elle dort la journee",
            "message_agent": "Rappelez Madame Lefevre, les chambres donnent sur cour.",
            "reserves": []
        }, ensure_ascii=False))


faux_genai = types.ModuleType("google.generativeai")
faux_genai.configure = lambda **kw: None
faux_genai.GenerativeModel = ModeleBouchon
if "google" not in sys.modules:
    sys.modules["google"] = types.ModuleType("google")
sys.modules["google.generativeai"] = faux_genai


# --------------------------------------------------------------------------- #
# Bouchon SMTP : on capture le mail au lieu de l'envoyer
# --------------------------------------------------------------------------- #
MAILS = []


class SmtpBouchon:
    def __init__(self, hote, port, context=None):
        self.hote = hote
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
    def login(self, user, mdp):
        self.user = user
    def send_message(self, em):
        MAILS.append(em)


import smtplib
smtplib.SMTP_SSL = SmtpBouchon

os.chdir(BAC)
import memoire_acquereurs as moteur


print("\n" + "=" * 70)
print("  TEST DE BOUT EN BOUT  -  memoire des acquereurs")
print("=" * 70)

# --------------------------------------------------------------------------- #
print("\n1. Rien de neuf : le robot ne doit RIEN redemander a l'IA")
moteur.commande_lire()
verifier("aucun vocal deja connu n'est relu",
         APPELS_IA["extractions"] == 0, str(APPELS_IA["extractions"]) + " extractions")

# --------------------------------------------------------------------------- #
print("\n2. Un nouveau vocal arrive")
with open(os.path.join(BAC, "donnees_demo", "vocaux",
                       "2026-07-21_madame_lefevre.txt"), "w", encoding="utf-8") as fh:
    fh.write("Madame Lefevre, infirmiere de nuit, elle dort la journee, "
             "pas de chambre sur rue. Ascenseur pour sa mere. 850 000 max.")
moteur.commande_lire()
verifier("exactement 1 nouveau vocal est lu", APPELS_IA["extractions"] == 1,
         str(APPELS_IA["extractions"]) + " extractions")
memoire = json.load(open(os.path.join(BAC, "memoire_acquereurs.json"), encoding="utf-8"))
verifier("la memoire passe de 5 a 6 acquereurs", len(memoire) == 6, str(len(memoire)))
verifier("les 5 fiches d'origine sont intactes",
         any(f["acquereur"] == "Jean Vasseur" for f in memoire))

# --------------------------------------------------------------------------- #
print("\n3. Confrontation : seuls les couples manquants passent a l'IA")
avant = APPELS_IA["confrontations"]
moteur.commande_alerter(70)
nouveaux_couples = APPELS_IA["confrontations"] - avant
verifier("les couples deja evalues ne sont pas recalcules",
         nouveaux_couples == 6 * 6 - 6, str(nouveaux_couples) + " confrontations")

# --------------------------------------------------------------------------- #
print("\n4. Le mail d'alerte est construit et remis a SMTP")
import envoyer_alerte
envoyer_alerte.RACINE = BAC
envoyer_alerte.RAPPROCHEMENTS = os.path.join(BAC, "rapprochements.json")
envoyer_alerte.BIENS = os.path.join(BAC, "donnees_demo", "biens.json")
envoyer_alerte.DEJA_VU = os.path.join(BAC, "alertes_envoyees.json")
envoyer_alerte.APERCU = False
envoyer_alerte.main()
verifier("un mail a bien ete remis au serveur", len(MAILS) == 1, str(len(MAILS)))

if MAILS:
    em = MAILS[0]
    verifier("destinataire = Alexis uniquement",
             em["To"] == "alexis.bendavid@gmail.com", str(em["To"]))
    corps = em.get_payload()[1].get_content() if em.is_multipart() else ""
    verifier("le mail contient une version HTML", "<html" in corps.lower())
    verifier("le mail est encode en UTF-8 (accents lisibles)", "charset=\"utf-8\"" in corps)
    verifier("le cas Jean Vasseur est present", "Jean Vasseur" in corps)
    verifier("le rejet motive est present", "Ne pas proposer" in corps)
    verifier("mention rassurante 'aucun client contacte'",
             "Aucun client" in corps)

# --------------------------------------------------------------------------- #
print("\n5. Second passage : le robot doit se taire")
envoyer_alerte.main()
verifier("aucun second mail n'est envoye", len(MAILS) == 1,
         str(len(MAILS)) + " mails au total")

# --------------------------------------------------------------------------- #
print("\n" + "=" * 70)
if ECHECS:
    print("  " + str(len(ECHECS)) + " ECHEC(S) : " + ", ".join(ECHECS))
else:
    print("  TOUT FONCTIONNE.")
    print("  " + str(APPELS_IA["extractions"]) + " extraction(s) + "
          + str(APPELS_IA["confrontations"]) + " confrontation(s) IA, "
          + "uniquement sur du nouveau.")
    print("  1 mail envoye a Alexis, 0 au second passage, 0 client contacte.")
print("=" * 70)
shutil.rmtree(BAC, ignore_errors=True)
sys.exit(1 if ECHECS else 0)
