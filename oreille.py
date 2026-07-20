#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L'oreille des robots : transforme un vocal en texte.

Pourquoi ce fichier existe
--------------------------
Un agent immobilier ne remplit pas de formulaire, il parle. Christophe Raas
debriefe deja ses visites a l'oral. Lui demander d'ecrire, c'est lui
demander de changer d'habitude, et une demonstration qui exige un
changement d'habitude ne se fait jamais.

Choix technique
---------------
On passe par Groq, avec la MEME cle que le cerveau. Pas de compte
supplementaire, pas de carte bancaire, pas de service a surveiller en plus.
Le modele est Whisper, qui transcrit le francais parle, y compris mal
articule et avec du bruit de fond, ce qui est exactement le cas d'un vocal
dicte en voiture.

Aucune librairie a installer : le multipart est construit a la main avec
urllib. Une dependance de moins est une panne de moins.
"""

import os
import json
import time
import uuid
import mimetypes
import urllib.error
import urllib.request

URL_TRANSCRIPTION = "https://api.groq.com/openai/v1/audio/transcriptions"

# Le "turbo" est nettement plus rapide et suffit largement pour du debrief
# dicte. On garde le modele complet en repli si le premier disparait.
MODELES = [m for m in [
    os.environ.get("GROQ_WHISPER_MODEL"),
    "whisper-large-v3-turbo",
    "whisper-large-v3",
] if m]

EXTENSIONS_AUDIO = (".m4a", ".mp3", ".wav", ".ogg", ".oga", ".opus",
                    ".webm", ".mp4", ".mpeg", ".mpga", ".amr", ".aac", ".flac")


class OreilleIndisponible(RuntimeError):
    """Aucun modele n'a su transcrire."""


def est_audio(nom_fichier):
    return str(nom_fichier).lower().endswith(EXTENSIONS_AUDIO)


def _corps_multipart(chemin, modele):
    """Construit une requete multipart/form-data sans dependance externe."""
    frontiere = "----oreille" + uuid.uuid4().hex
    nom = os.path.basename(chemin)
    type_mime = mimetypes.guess_type(nom)[0] or "application/octet-stream"

    with open(chemin, "rb") as fh:
        contenu = fh.read()

    morceaux = []

    def champ(cle, valeur):
        morceaux.append(("--" + frontiere + "\r\n"
                         'Content-Disposition: form-data; name="' + cle + '"\r\n\r\n'
                         + valeur + "\r\n").encode("utf-8"))

    morceaux.append(("--" + frontiere + "\r\n"
                     'Content-Disposition: form-data; name="file"; filename="'
                     + nom + '"\r\n'
                     "Content-Type: " + type_mime + "\r\n\r\n").encode("utf-8"))
    morceaux.append(contenu)
    morceaux.append(b"\r\n")

    champ("model", modele)
    champ("language", "fr")
    champ("response_format", "json")
    # Le prompt oriente le vocabulaire : sans lui, Whisper ecrit "Vaux Cresson"
    # ou "Fosses Repos". Avec, il ecrit les noms de communes correctement.
    champ("prompt", "Debrief immobilier. Communes : Garches, Vaucresson, "
                    "Saint-Cloud, Marnes-la-Coquette, Ville-d'Avray, "
                    "La Celle-Saint-Cloud. Foret de Fausses-Reposes.")

    morceaux.append(("--" + frontiere + "--\r\n").encode("utf-8"))
    return b"".join(morceaux), frontiere


def transcrire(chemin, essais=3):
    """Renvoie le texte d'un fichier audio. Leve OreilleIndisponible sinon."""
    cle = os.environ.get("GROQ_API_KEY", "").strip()
    if not cle:
        raise OreilleIndisponible(
            "GROQ_API_KEY absente : l'oreille utilise la meme cle que le cerveau.")
    if not os.path.exists(chemin):
        raise OreilleIndisponible("Fichier introuvable : " + str(chemin))

    poids = os.path.getsize(chemin)
    if poids > 24 * 1024 * 1024:
        raise OreilleIndisponible(
            "Vocal trop lourd (" + str(round(poids / 1048576, 1)) + " Mo). "
            "Limite 24 Mo, soit environ deux heures de parole.")

    dernier = None
    for modele in MODELES:
        for tentative in range(essais):
            try:
                corps, frontiere = _corps_multipart(chemin, modele)
                requete = urllib.request.Request(
                    URL_TRANSCRIPTION, data=corps, method="POST",
                    headers={
                        "Authorization": "Bearer " + cle,
                        "Content-Type": "multipart/form-data; boundary=" + frontiere,
                        "Accept": "application/json",
                        # Meme raison que dans cerveau.py : Cloudflare refuse
                        # la signature par defaut de Python.
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X "
                                      "10_15_7) AppleWebKit/537.36 (KHTML, like "
                                      "Gecko) Chrome/124.0.0.0 Safari/537.36",
                    })
                with urllib.request.urlopen(requete, timeout=180) as reponse:
                    donnees = json.loads(reponse.read().decode("utf-8"))
                texte = (donnees.get("text") or "").strip()
                if texte:
                    print("Oreille : groq / " + modele + " ("
                          + str(len(texte)) + " caracteres)")
                    return texte
                dernier = "reponse vide"
                break
            except urllib.error.HTTPError as err:
                detail = err.read().decode("utf-8", "ignore")[:300]
                dernier = str(err.code) + " " + detail
                if err.code == 429 and tentative < essais - 1:
                    time.sleep(5 * (tentative + 1))
                    continue
                break
            except Exception as err:  # noqa: BLE001
                dernier = str(err)[:300]
                if tentative < essais - 1:
                    time.sleep(3)
                    continue
                break

    raise OreilleIndisponible(
        "Transcription impossible. Modeles essayes : " + ", ".join(MODELES)
        + ". Dernier probleme : " + str(dernier))


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage : python oreille.py <fichier_audio>")
        raise SystemExit(2)
    print(transcrire(sys.argv[1]))
