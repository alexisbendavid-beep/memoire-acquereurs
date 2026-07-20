#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aspire le portefeuille public d'une agence et le range en JSON.

Pourquoi ce fichier existe
--------------------------
Christophe Raas a deux objections : trop de logiciels, et les API ne
repondent pas a son probleme. Ce module repond aux deux d'un coup : on ne
se branche sur RIEN. On lit ses annonces publiques, exactement comme le
ferait un acquereur qui visite son site. Aucun acces a son logiciel metier,
aucune cle, aucune integration a maintenir.

Choix technique important
-------------------------
On ne s'accroche pas aux balises ni aux classes CSS, qui changent a chaque
refonte de site. On transforme la page en texte, puis on lit les intitules
que l'agence affiche a ses propres visiteurs : "Reference", "Prix",
"Presentation", "Caracteristiques". Ces intitules-la ne bougent pas, parce
que ce sont eux que lisent les clients. Un aspirateur qui survit aux
refontes vaut mieux qu'un aspirateur elegant qui casse tous les six mois.

Ce qu'on garde surtout : le DESCRIPTIF COMPLET. C'est la seule partie de
l'annonce qui contient les criteres qualitatifs (terrain arbore, proximite
des ecoles, exposition, calme). Les cases chiffrees, n'importe quel filtre
sait deja les traiter.
"""

import io
import os
import re
import ssl
import json
import time
import argparse
import urllib.error
import urllib.request
from datetime import date
from html.parser import HTMLParser

RACINE = os.path.dirname(os.path.abspath(__file__))
# Fichier separe : on ne touche JAMAIS aux donnees de demonstration, qui
# servent de reference stable pour le PDF et les tests.
SORTIE = os.path.join(RACINE, "portefeuille_agence_rg.json")

SITE = "https://www.agence-rg.fr"
LISTE = SITE + "/annonces/?transaction=vente"

NAVIGATEUR = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
}


# --------------------------------------------------------------------------- #
# Lecture des pages
# --------------------------------------------------------------------------- #
def lire(url, essais=3):
    for tentative in range(essais):
        try:
            requete = urllib.request.Request(url, headers=NAVIGATEUR)
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(requete, timeout=40, context=ctx) as r:
                return r.read().decode("utf-8", "ignore")
        except (urllib.error.URLError, OSError) as err:
            if tentative == essais - 1:
                print("  page illisible : " + url + " (" + str(err)[:80] + ")")
                return ""
            time.sleep(2 * (tentative + 1))
    return ""


class EnTexte(HTMLParser):
    """Transforme le HTML en texte lisible, en jetant scripts et styles."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.morceaux = []
        self.ignorer = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.ignorer += 1
        elif tag in ("br", "p", "div", "li", "tr", "h1", "h2", "h3", "h4", "section"):
            self.morceaux.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self.ignorer:
            self.ignorer -= 1
        elif tag in ("p", "div", "li", "tr", "h1", "h2", "h3", "h4", "section"):
            self.morceaux.append("\n")

    def handle_data(self, data):
        if not self.ignorer and data.strip():
            self.morceaux.append(data.strip())
            self.morceaux.append(" ")


def en_texte(html):
    p = EnTexte()
    p.feed(html)
    brut = "".join(p.morceaux)
    brut = re.sub(r"[ \t]+", " ", brut)
    brut = re.sub(r"\n\s*\n+", "\n", brut)
    return brut.strip()


# --------------------------------------------------------------------------- #
# Reperage des annonces
# --------------------------------------------------------------------------- #
def urls_des_annonces(limite_pages=25):
    """Parcourt la liste page par page jusqu'a ne plus rien decouvrir.

    Deux pieges observes sur ce site, notes ici pour la prochaine fois :
      - la pagination est dans le CHEMIN (/annonces/page2/), pas dans un
        parametre. Un "&page=2" renvoie silencieusement la page 1, ce qui
        donne un aspirateur qui a l'air de marcher mais ne ramene que 9
        biens sur 59.
      - le parametre "limit" est plafonne a 9 cote serveur : inutile de
        demander tout d'un coup, il faut vraiment tourner les pages.
    """
    trouvees = []
    connues = set()
    for page in range(1, limite_pages + 1):
        url = (LISTE if page == 1
               else SITE + "/annonces/page" + str(page) + "/?transaction=vente")
        html = lire(url)
        if not html:
            break
        slugs = [s for s in re.findall(
            r'href="[^"]*?/annonces/([a-z0-9][a-z0-9\-]{6,})/?"', html)
            if not re.match(r"^page\d+$", s)]
        nouveaux = [s for s in dict.fromkeys(slugs) if s not in connues]
        if not nouveaux:
            break
        for s in nouveaux:
            connues.add(s)
            trouvees.append(SITE + "/annonces/" + s + "/")
        print("  page " + str(page) + " : " + str(len(nouveaux)) + " annonce(s)")
    return trouvees


# --------------------------------------------------------------------------- #
# Extraction d'une fiche
# --------------------------------------------------------------------------- #
def _entre(texte, debut, fins):
    """Renvoie ce qui se trouve entre un intitule et le suivant."""
    i = texte.find(debut)
    if i < 0:
        return ""
    i += len(debut)
    coupe = len(texte)
    for f in fins:
        j = texte.find(f, i)
        if 0 <= j < coupe:
            coupe = j
    return texte[i:coupe].strip()


def _nombre(texte, motif):
    m = re.search(motif, texte)
    if not m:
        return None
    brut = m.group(1).replace(" ", "").replace(" ", "").replace(" ", "")
    brut = brut.replace(",", ".")
    try:
        return int(float(brut))
    except ValueError:
        return None


def extraire_bien(url):
    html = lire(url)
    if not html:
        return None
    t = en_texte(html)

    prix = _nombre(t, r"Prix\s*:?\s*([\d\s  ]{4,})\s*€")
    if prix is None:
        return None

    ref = ""
    m = re.search(r"Référence\s*:?\s*([A-Za-z0-9\-]{1,12})", t)
    if m:
        ref = m.group(1)

    ville, code_postal = "", ""
    m = re.search(r"Localisation\s*:?\s*([A-ZÉÈÀÂÎÔÛÇ' \-]{3,40}?)\s*(\d{5})", t)
    if m:
        ville, code_postal = m.group(1).strip(), m.group(2)

    descriptif = _entre(t, "Présentation", ["Caractéristiques"])
    # la premiere ligne du bloc est le titre de l'annonce, on la garde a part
    lignes = [l.strip() for l in descriptif.split("\n") if l.strip()]
    titre = lignes[0] if lignes else ""
    descriptif = " ".join(lignes[1:]) if len(lignes) > 1 else ""

    caracteristiques = _entre(t, "Caractéristiques", ["Détail financier",
                                                      "Informations Légales"])
    caracteristiques = " ".join(l.strip() for l in caracteristiques.split("\n")
                                if l.strip())

    conseiller = ""
    m = re.search(r"Votre conseiller dédié\s*\n?\s*([A-ZÉÈÀÂÎÔÛÇ][\w' \-]{2,40})", t)
    if m:
        conseiller = m.group(1).strip()

    return {
        "ref": ref or url.rstrip("/").split("/")[-1][:20],
        "titre": titre,
        "adresse": (ville + " " + code_postal).strip(),
        "ville": ville,
        "code_postal": code_postal,
        "prix": prix,
        "type": (re.search(r"\bType\s+(\w+)", t).group(1)
                 if re.search(r"\bType\s+(\w+)", t) else ""),
        "surface": _nombre(t, r"Surface habitable\s*([\d\s.,]{2,12})\s*m"),
        "surface_terrain": _nombre(t, r"Surface terrain\s*([\d\s.,]{2,12})\s*m"),
        "pieces": _nombre(t, r"\bPièces\s*(\d{1,2})\b"),
        "chambres": _nombre(t, r"\bChambres\s*(\d{1,2})\b"),
        "conseiller": conseiller,
        "annonce": descriptif,
        "caracteristiques": caracteristiques,
        "url": url,
    }


# --------------------------------------------------------------------------- #
def main():
    p = argparse.ArgumentParser(description="Aspire le portefeuille public")
    p.add_argument("--sortie", default=SORTIE)
    p.add_argument("--pause", type=float, default=1.0,
                   help="secondes entre deux fiches, par correction envers le site")
    p.add_argument("--si-plus-vieux-que", type=float, default=0,
                   help="ne re-aspire que si le fichier a plus de N heures")
    args = p.parse_args()

    # Politesse envers le site de l'agence. Le robot se reveille toutes les
    # 10 minutes pour relever les mails, mais un portefeuille immobilier ne
    # bouge pas toutes les 10 minutes. Sans ce garde-fou, on taperait 8 000
    # fois par jour sur leur serveur, ce qui serait grossier et finirait par
    # nous faire bloquer.
    if args.si_plus_vieux_que and os.path.exists(args.sortie):
        age_heures = (time.time() - os.path.getmtime(args.sortie)) / 3600.0
        if age_heures < args.si_plus_vieux_que:
            print("Portefeuille vieux de " + str(round(age_heures, 1))
                  + " h, seuil a " + str(args.si_plus_vieux_que)
                  + " h : rien a refaire.")
            return

    # On conserve la date de premiere observation de chaque bien : c'est elle
    # qui permet de dire "ce mandat est entre il y a X jours" sans l'inventer.
    anciens = {}
    if os.path.exists(args.sortie):
        try:
            with io.open(args.sortie, encoding="utf-8") as fh:
                for b in json.load(fh):
                    if b.get("ref"):
                        anciens[str(b["ref"])] = b.get("entree_portefeuille")
        except (ValueError, OSError):
            anciens = {}

    print("Lecture de la liste des annonces...")
    urls = urls_des_annonces()
    print(str(len(urls)) + " annonce(s) reperee(s).\n")

    biens, echecs = [], 0
    for n, url in enumerate(urls, 1):
        bien = extraire_bien(url)
        if not bien:
            echecs += 1
            continue
        ref = str(bien["ref"])
        bien["entree_portefeuille"] = anciens.get(ref) or date.today().isoformat()
        biens.append(bien)
        print(str(n) + "/" + str(len(urls)) + "  " + ref.ljust(6)
              + bien["adresse"].ljust(28)
              + format(bien["prix"], ",d").replace(",", " ") + " EUR")
        time.sleep(args.pause)

    os.makedirs(os.path.dirname(args.sortie), exist_ok=True)
    with io.open(args.sortie, "w", encoding="utf-8") as fh:
        json.dump(biens, fh, ensure_ascii=False, indent=2)

    avec_texte = sum(1 for b in biens if len(b.get("annonce", "")) > 120)
    print("\n" + str(len(biens)) + " bien(s) enregistre(s) dans " + args.sortie)
    print(str(avec_texte) + " avec un descriptif exploitable, "
          + str(echecs) + " fiche(s) illisible(s).")
    if biens and avec_texte < len(biens) * 0.6:
        print("ATTENTION : trop de descriptifs vides, le site a peut-etre change.")


if __name__ == "__main__":
    main()
