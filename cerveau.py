#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le cerveau des robots. Un seul point d'entree : demander().

Pourquoi ce fichier existe :
  Le 20/07/2026, Gemini a cesse de repondre avec "limit: 0" parce que Google
  exige desormais une carte bancaire rattachee au projet pour debloquer le
  quota gratuit. Plutot que de dependre d'un seul fournisseur, ce module
  permet d'en changer avec une variable d'environnement, sans toucher au
  code des robots.

FOURNISSEUR_IA = "groq"    (defaut) gratuit, sans carte bancaire
FOURNISSEUR_IA = "gemini"  si un jour la facturation Google est rattachee

Aucune librairie a installer pour Groq : on passe par urllib, present dans
Python. Une dependance de moins, c'est une panne de moins.

Les noms de modeles changent vite (les Llama ont ete deprecies chez Groq en
2026). Le module essaie donc plusieurs modeles dans l'ordre et garde le
premier qui repond, au lieu de tomber en panne sur un nom obsolete.
"""

import os
import json
import time
import urllib.error
import urllib.request

FOURNISSEUR = os.environ.get("FOURNISSEUR_IA", "groq").strip().lower()

# Ordre de preference. Le premier qui repond est retenu pour la session.
MODELES_GROQ = [m for m in [
    os.environ.get("GROQ_MODEL"),
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
] if m]

MODELES_GEMINI = [m for m in [
    os.environ.get("GEMINI_MODEL"),
    "gemini-2.0-flash",
] if m]

URL_GROQ = "https://api.groq.com/openai/v1/chat/completions"

_modele_retenu = {"nom": None}


class CerveauIndisponible(RuntimeError):
    """Aucun modele n'a repondu."""


# --------------------------------------------------------------------------- #
# Groq : API compatible OpenAI, appelee en HTTP pur
# --------------------------------------------------------------------------- #
def _appel_groq(modele, consigne, invite, timeout=90):
    cle = os.environ.get("GROQ_API_KEY", "").strip()
    if not cle:
        raise CerveauIndisponible(
            "GROQ_API_KEY absente. Cree une cle gratuite sur console.groq.com "
            "puis ajoute-la en secret GitHub."
        )
    corps = json.dumps({
        "model": modele,
        "messages": [
            {"role": "system", "content": consigne},
            {"role": "user", "content": invite},
        ],
        "temperature": 0.2,
    }).encode("utf-8")

    # Groq est derriere Cloudflare, qui bloque la signature par defaut de
    # Python (erreur 403 code 1010). On se presente donc comme un client
    # HTTP normal. C'est la seule raison d'etre de User-Agent et Accept.
    requete = urllib.request.Request(
        URL_GROQ, data=corps, method="POST",
        headers={
            "Authorization": "Bearer " + cle,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0.0.0 Safari/537.36",
        },
    )
    with urllib.request.urlopen(requete, timeout=timeout) as reponse:
        donnees = json.loads(reponse.read().decode("utf-8"))
    return donnees["choices"][0]["message"]["content"]


# --------------------------------------------------------------------------- #
# Gemini : conserve au cas ou la facturation Google serait rattachee un jour
# --------------------------------------------------------------------------- #
def _appel_gemini(modele, consigne, invite):
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    m = genai.GenerativeModel(modele, system_instruction=consigne)
    return m.generate_content(invite).text


# --------------------------------------------------------------------------- #
# Point d'entree unique
# --------------------------------------------------------------------------- #
def demander(consigne, invite, essais=3):
    """Pose une question au cerveau et renvoie sa reponse en texte.

    Bascule automatiquement de modele si le premier est deprecie ou sature,
    et repete en cas de limite de debit passagere.
    """
    if FOURNISSEUR == "gemini":
        modeles, appeler = MODELES_GEMINI, _appel_gemini
    else:
        modeles, appeler = MODELES_GROQ, _appel_groq

    # Si un modele a deja fonctionne, on le reessaie en premier.
    if _modele_retenu["nom"] in modeles:
        modeles = [_modele_retenu["nom"]] + [m for m in modeles
                                             if m != _modele_retenu["nom"]]

    dernier_probleme = None
    for modele in modeles:
        for tentative in range(essais):
            try:
                reponse = appeler(modele, consigne, invite)
                if _modele_retenu["nom"] != modele:
                    print("Cerveau : " + FOURNISSEUR + " / " + modele)
                    _modele_retenu["nom"] = modele
                return reponse
            except urllib.error.HTTPError as err:
                detail = err.read().decode("utf-8", "ignore")[:300]
                dernier_probleme = str(err.code) + " " + detail
                # 429 = trop de requetes : on patiente et on reessaie.
                if err.code == 429 and tentative < essais - 1:
                    time.sleep(5 * (tentative + 1))
                    continue
                # 404 / 400 = modele inconnu ou deprecie : on passe au suivant.
                break
            except Exception as err:  # noqa: BLE001
                dernier_probleme = str(err)[:300]
                if tentative < essais - 1:
                    time.sleep(3)
                    continue
                break

    raise CerveauIndisponible(
        "Aucun modele n'a repondu (" + FOURNISSEUR + "). "
        "Modeles essayes : " + ", ".join(modeles) + ". "
        "Dernier probleme : " + str(dernier_probleme)
    )


if __name__ == "__main__":
    print("Fournisseur :", FOURNISSEUR)
    print("Modeles     :", MODELES_GROQ if FOURNISSEUR == "groq" else MODELES_GEMINI)
    print(demander("Reponds en un seul mot.", "Dis bonjour."))
