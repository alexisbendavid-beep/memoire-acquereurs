#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L'essai de bout en bout, sur un vrai vocal et un vrai portefeuille.

Ce que ca prouve, et qui n'avait jamais ete prouve ensemble :
  vocal reel -> transcription -> fiche besoin -> confrontation aux 59
  annonces publiees par l'Agence RG -> correspondances et refus motives.

Aucun mail n'est envoye. Le resultat est ecrit dans un fichier HTML que
l'on recupere en piece jointe du run. C'est volontaire : cet essai sert a
regarder ce que la machine produit AVANT que quiconque le recoive.
"""

import io
import os
import sys
import json
import argparse

from oreille import transcrire, OreilleIndisponible
from demo_raas import analyser, rapport, charger_portefeuille, euros

RACINE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(RACINE, "resultat_essai.html")


def main():
    p = argparse.ArgumentParser(description="Essai complet sur un vocal reel")
    p.add_argument("--vocal", default=os.path.join(RACINE, "echantillon_vocal.m4a"))
    p.add_argument("--texte", default="", help="court-circuite la transcription")
    args = p.parse_args()

    biens = charger_portefeuille()
    if not biens:
        print("Portefeuille vide : lancer aspirer_portefeuille.py d'abord.")
        return 1
    print(str(len(biens)) + " annonces reelles chargees.\n")

    if args.texte:
        source = args.texte
        print("Source : texte fourni en argument.\n")
    else:
        print("Transcription de " + os.path.basename(args.vocal) + "...")
        try:
            source = transcrire(args.vocal)
        except OreilleIndisponible as err:
            print("Transcription impossible : " + str(err))
            return 1
        print()

    print("=" * 68)
    print("CE QUE LA MACHINE A ENTENDU")
    print("=" * 68)
    print(source)
    print()

    fiche, retenus, ecartes, analyses = analyser(source, biens)

    print("=" * 68)
    print("LA FICHE BESOIN QU'ELLE EN A TIREE")
    print("=" * 68)
    print("Acquereur   : " + str(fiche.get("acquereur")))
    print("Type        : " + str(fiche.get("type_bien")))
    print("Budget max  : " + euros(fiche.get("budget_max")))
    print("Chambres    : " + str(fiche.get("chambres_min")))
    print("Redhibitoire: " + ", ".join(str(x) for x in (fiche.get("redhibitoires") or [])))
    print("\nCriteres qualitatifs, ceux qu'aucun logiciel ne stocke :")
    for c in (fiche.get("criteres_qualitatifs") or []):
        print("  - " + str(c.get("besoin")))
        if c.get("verbatim"):
            print("      il a dit : \"" + str(c.get("verbatim")) + "\"")
        if c.get("pourquoi"):
            print("      pourquoi : " + str(c.get("pourquoi")))
    print()

    print("=" * 68)
    print("LE TRI : " + str(len(biens)) + " annonces, " + str(len(ecartes))
          + " ecartees sans IA, " + str(analyses) + " analysees en profondeur")
    print("=" * 68)

    bons = [r for r in retenus if (r.get("score") or 0) >= 70]
    faibles = [r for r in retenus if (r.get("score") or 0) < 70]

    print("\n--- " + str(len(bons)) + " CORRESPONDANCE(S) A RAPPELER ---")
    for r in bons:
        b = r.get("bien", {})
        print("\n[" + str(r.get("score")) + "/100]  " + str(b.get("titre"))
              + "  " + str(b.get("adresse")) + "  " + euros(b.get("prix")))
        print("  " + str(r.get("message_agent")))
        if r.get("preuve_annonce"):
            print("  Dans l'annonce : \"" + str(r.get("preuve_annonce"))[:150] + "\"")
        for res in (r.get("reserves") or []):
            print("  Reserve : " + str(res))
    if not bons:
        print("  Aucune. La machine prefere ne rien proposer plutot que de meubler.")

    print("\n--- ECARTES APRES ANALYSE FINE, AVEC MOTIF ---")
    for r in sorted(faibles, key=lambda x: -(x.get("score") or 0))[:6]:
        b = r.get("bien", {})
        print("[" + str(r.get("score")) + "/100] " + str(b.get("titre"))
              + " : " + str(r.get("message_agent") or r.get("verdict"))[:160])

    print("\n--- ECARTES D'EMBLEE SUR CRITERES DURS ---")
    for e in ecartes[:10]:
        print("  " + str(e["bien"].get("titre"))[:44].ljust(46) + e["motif"])
    if len(ecartes) > 10:
        print("  et " + str(len(ecartes) - 10) + " autre(s).")

    html, texte, nb = rapport(fiche, retenus, ecartes, analyses, source, biens)
    with io.open(SORTIE, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("\nRapport visuel ecrit : " + SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
