#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test de bout en bout de la demo Raas, hors ligne.

On bouchonne IMAP, SMTP, l'oreille et le cerveau. Aucun reseau, aucun cout,
et surtout : on verifie la promesse de securite, a savoir qu'AUCUN texte
produit par l'IA ne part chez le client.
"""
import os, sys, json, email, io, shutil, tempfile
SOURCE = os.path.dirname(os.path.abspath(__file__))
BAC = tempfile.mkdtemp(prefix="test_demo_")
for _n in ("demo_raas.py","cerveau.py","oreille.py","memoire_acquereurs.py"):
    shutil.copy(os.path.join(SOURCE, _n), BAC)
sys.path.insert(0, BAC)
os.chdir(BAC)

os.environ.update(GMAIL_ADDRESS="alexis.bendavid@gmail.com",
                  GMAIL_APP_PASSWORD="bouchon", GROQ_API_KEY="bouchon",
                  EXPEDITEURS_DEMO="christopheraas@agence-rg.fr")

ECHECS = []
def v(libelle, cond, detail=""):
    print(("  OK   " if cond else "  ECHEC") + " " + libelle + ("" if cond else "  -> " + str(detail)))
    if not cond: ECHECS.append(libelle)

# --- portefeuille factice, dont un bien hors budget et un appartement ------- #
BIENS = [
  {"ref":"59","titre":"Villa 8 pieces","adresse":"VAUCRESSON 92420","prix":1750000,
   "type":"Maison","chambres":5,"conseiller":"Christophe RAAS",
   "annonce":"Terrain arbore de 1145 m2, le fond du jardin ouvre sur les sentiers de la foret."},
  {"ref":"31","titre":"Maison 10 pieces","adresse":"GARCHES 92380","prix":1850000,
   "type":"Maison","chambres":6,"annonce":"Proche des ecoles, calme."},
  {"ref":"158","titre":"Maison 11 pieces","adresse":"VILLE D AVRAY 92410","prix":2700000,
   "type":"Maison","chambres":6,"annonce":"Vaste demeure."},
  {"ref":"77","titre":"Appartement 3 pieces","adresse":"GARCHES 92380","prix":600000,
   "type":"Appartement","chambres":2,"annonce":"Balcon expose sud."},
]
json.dump(BIENS, io.open("portefeuille_agence_rg.json","w",encoding="utf-8"), ensure_ascii=False)


# --- bouchons -------------------------------------------------------------- #
import cerveau, oreille
FICHE = json.dumps({"acquereur":"Famille Bonnet","date_echange":"2026-03-14",
  "type_bien":"Maison","budget_max":1800000,"chambres_min":4,"secteurs":["Vaucresson"],
  "criteres_durs":["4 chambres"],
  "criteres_qualitatifs":[{"besoin":"Acces direct a la foret",
    "verbatim":"il veut ouvrir sa porte et etre dans les bois",
    "pourquoi":"il court tous les matins"}],
  "redhibitoires":[],"maturite":"chaud","note_agent":""}, ensure_ascii=False)
MATCH = json.dumps({"score":92,"verdict":"Correspondance sur le critere decisif",
  "declencheur":"Acces direct a la foret",
  "preuve_annonce":"le fond du jardin ouvre sur les sentiers de la foret",
  "rappel_verbatim":"il veut ouvrir sa porte et etre dans les bois",
  "message_agent":"Rappelez la famille Bonnet, le jardin ouvre sur la foret.",
  "reserves":[]}, ensure_ascii=False)

APPELS = {"extraction":0,"match":0}
def cerveau_bouchon(consigne, invite, essais=3):
    if "Tu compares un bien" in consigne:
        APPELS["match"] += 1; return MATCH
    APPELS["extraction"] += 1; return FICHE
cerveau.demander = cerveau_bouchon
oreille.transcrire = lambda chemin, essais=3: "Alors la famille Bonnet, ils veulent ouvrir leur porte et etre dans les bois, il court tous les matins, budget un million huit maximum, minimum quatre chambres, plutot Vaucresson."

import demo_raas as d
d.demander = cerveau_bouchon
d.transcrire = oreille.transcrire

MAILS = []
d.envoyer = lambda dest, sujet, texte, html=None: MAILS.append(
    {"dest":dest,"sujet":sujet,"texte":texte,"html":html or ""})

# --- message entrant avec vocal joint -------------------------------------- #
BRUT = b"""From: Christophe RAAS <christopheraas@agence-rg.fr>
Subject: =?utf-8?B?TW9uIGFjcXXDqXJldXIgaW1wb3NzaWJsZQ==?=
Message-ID: <demo-1@agence-rg.fr>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="X"

--X
Content-Type: text/plain; charset="utf-8"

Voila, je vous mets le pire cas que j'ai eu.
--X
Content-Type: audio/mp4; name="debrief.m4a"
Content-Disposition: attachment; filename="debrief.m4a"
Content-Transfer-Encoding: base64

AAAAIGZ0eXBNNEEgAAAAAA==
--X--
"""
d.relever = lambda: [("<demo-1@agence-rg.fr>", email.message_from_bytes(BRUT))]

print("\n" + "="*70)
print("  TEST DE LA DEMO RAAS")
print("="*70)

print("\n1. Le depiecage du message")
corps, vocaux = d.depiecer(email.message_from_bytes(BRUT))
v("le texte ecrit est recupere", "pire cas" in corps, corps[:60])
v("le vocal joint est extrait", len(vocaux) == 1, str(vocaux))
v("le vocal est bien un fichier sur disque", vocaux and os.path.exists(vocaux[0]))

print("\n2. Le tri grossier avant l'IA")
fiche_test = json.loads(FICHE)
v("le bien a 2,7 M est ecarte sans IA", d.incompatible(fiche_test, BIENS[2]) is not None,
  d.incompatible(fiche_test, BIENS[2]))
v("l'appartement est ecarte sans IA", d.incompatible(fiche_test, BIENS[3]) is not None)
v("la villa dans le budget passe a l'IA", d.incompatible(fiche_test, BIENS[0]) is None)
v("tolerance de 15 % appliquee (1,85 M pour 1,8 M)",
  d.incompatible(fiche_test, BIENS[1]) is None, d.incompatible(fiche_test, BIENS[1]))

print("\n3. Le cycle complet")
d.main()
v("deux mails sont partis", len(MAILS) == 2, str(len(MAILS)))

accuse = next((m for m in MAILS if "agence-rg.fr" in m["dest"]), None)
rapport = next((m for m in MAILS if m["dest"] == "alexis.bendavid@gmail.com"), None)

print("\n4. LA REGLE DE SECURITE")
v("l'accuse part bien chez Christophe", accuse is not None)
v("le rapport ne part QU'A Alexis", rapport is not None and rapport["dest"] == "alexis.bendavid@gmail.com")
if accuse:
    corps_accuse = accuse["texte"] + accuse["html"]
    v("AUCUNE phrase de l'IA dans l'accuse",
      "Rappelez la famille Bonnet" not in corps_accuse and "Bonnet" not in corps_accuse)
    v("aucun nom d'acquereur ne fuit chez le client", "Bonnet" not in corps_accuse)
    v("l'accuse annonce le bon nombre d'annonces", "4 annonces" in corps_accuse)
    v("l'accuse dit qu'un humain relira", "valid" in corps_accuse.lower())
if rapport:
    h = rapport["html"]
    v("le rapport contient la correspondance", "Rappelez la famille Bonnet" in h)
    v("le rapport montre la transcription entendue", "ouvrir leur porte" in h)
    v("le rapport montre les criteres qualitatifs", "Acces direct a la foret" in h)
    v("le rapport montre les rejets sur criteres durs", "hors budget" in h)
    v("le rapport rappelle de relire avant transfert", "relire avant de transferer" in h.lower() or "A relire" in h)

print("\n5. L'economie d'appels IA")
v("1 seule extraction", APPELS["extraction"] == 1, str(APPELS["extraction"]))
v("seuls les 2 biens plausibles sont analyses", APPELS["match"] == 2, str(APPELS["match"]))

print("\n6. Le robot ne traite pas deux fois le meme message")
MAILS.clear(); APPELS["match"] = 0
d.main()
v("aucun second envoi", len(MAILS) == 0, str(len(MAILS)))
v("aucun second appel IA", APPELS["match"] == 0)

print("\n" + "="*70)
print("  TOUT FONCTIONNE." if not ECHECS else "  " + str(len(ECHECS)) + " ECHEC(S) : " + ", ".join(ECHECS))
print("="*70)
shutil.rmtree(BAC, ignore_errors=True)
sys.exit(1 if ECHECS else 0)
