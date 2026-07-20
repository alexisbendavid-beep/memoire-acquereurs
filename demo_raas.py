#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""La boucle de demonstration pour Christophe Raas.

Le scenario, vu de lui
----------------------
  1. Il dicte 90 secondes sur un acquereur et l'envoie par mail.
  2. Dix secondes plus tard, il recoit un accuse de reception. La machine
     est vivante, il le voit tout de suite.
  3. Pendant ce temps, le robot transcrit, extrait la fiche besoin, et
     confronte cet acquereur a l'integralite du portefeuille public.
  4. L'analyse complete arrive chez Alexis, pretee a relire et a transferer.

La regle de securite, et pourquoi elle est ainsi
------------------------------------------------
Le seul message qui part AUTOMATIQUEMENT vers le client est l'accuse de
reception, et son texte est ecrit en dur ici. Aucune phrase produite par
une IA ne part chez un client sans relecture humaine. Une analyse ratee
qui part toute seule chez un prospect sceptique, cela ne se rattrape pas.

Le compromis est donc : instantaneite sur la forme, relecture sur le fond.
"""

import os
import io
import ssl
import json
import time
import email
import base64
import imaplib
import smtplib
import tempfile
from datetime import date, datetime
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import parseaddr

from cerveau import demander
from oreille import transcrire, est_audio, OreilleIndisponible
from memoire_acquereurs import (CONSIGNE_EXTRACTION, CONSIGNE_MATCH,
                                _json_depuis)

RACINE = os.path.dirname(os.path.abspath(__file__))
PORTEFEUILLE = os.path.join(RACINE, "portefeuille_agence_rg.json")
JOURNAL = os.path.join(RACINE, "demo_raas_traites.json")

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")

# Qui a le droit de declencher la demonstration. Tout autre expediteur est
# ignore : le robot ne repond pas au premier venu.
EXPEDITEURS = [a.strip().lower() for a in os.environ.get(
    "EXPEDITEURS_DEMO", "christopheraas@agence-rg.fr").split(",") if a.strip()]

# Garde-fou : mis a 0, aucun accuse ne part, tout arrive chez Alexis.
ACCUSE_AUTO = os.environ.get("ACCUSE_AUTO", "1").strip() == "1"

SEUIL = int(os.environ.get("SEUIL_DEMO", "70"))
NAVY, OR, VERT, ROUGE = "#12232f", "#c9a227", "#1f7a4d", "#b03b3b"


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #
def _txt(valeur):
    try:
        return str(make_header(decode_header(valeur or "")))
    except (TypeError, ValueError, UnicodeDecodeError):
        return valeur or ""


def euros(n):
    try:
        return format(int(n), ",d").replace(",", " ") + " €"
    except (TypeError, ValueError):
        return "prix non communique"


def journal_lu():
    if os.path.exists(JOURNAL):
        try:
            with io.open(JOURNAL, encoding="utf-8") as fh:
                return json.load(fh)
        except (ValueError, OSError):
            return []
    return []


def journal_ecrit(ids):
    with io.open(JOURNAL, "w", encoding="utf-8") as fh:
        json.dump(ids, fh, ensure_ascii=False, indent=2)


def envoyer(destinataire, sujet, texte, html=None):
    em = EmailMessage()
    em["From"] = GMAIL_ADDRESS
    em["To"] = destinataire
    em["Subject"] = sujet
    em.set_content(texte)
    if html:
        em.add_alternative(html, subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465,
                          context=ssl.create_default_context()) as s:
        s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        s.send_message(em)
    print("  mail envoye a " + destinataire + " : " + sujet)


# --------------------------------------------------------------------------- #
# 1. Relever la boite
# --------------------------------------------------------------------------- #
def relever():
    """Renvoie les messages non traites venant des expediteurs autorises."""
    boite = imaplib.IMAP4_SSL("imap.gmail.com")
    boite.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
    boite.select("INBOX")

    deja = set(journal_lu())
    messages = []
    for expediteur in EXPEDITEURS:
        statut, donnees = boite.search(None, 'FROM', '"' + expediteur + '"')
        if statut != "OK":
            continue
        for num in donnees[0].split():
            statut, brut = boite.fetch(num, "(RFC822)")
            if statut != "OK":
                continue
            msg = email.message_from_bytes(brut[0][1])
            identifiant = msg.get("Message-ID", "").strip() or num.decode()
            if identifiant in deja:
                continue
            messages.append((identifiant, msg))
    boite.logout()
    return messages


def depiecer(msg):
    """Extrait le texte ecrit et les vocaux joints d'un message."""
    texte, vocaux = [], []
    for partie in msg.walk():
        if partie.is_multipart():
            continue
        nom = _txt(partie.get_filename())
        disposition = str(partie.get("Content-Disposition") or "")

        if nom and est_audio(nom):
            chemin = os.path.join(tempfile.mkdtemp(), os.path.basename(nom))
            with open(chemin, "wb") as fh:
                fh.write(partie.get_payload(decode=True) or b"")
            vocaux.append(chemin)
        elif partie.get_content_type() == "text/plain" and "attachment" not in disposition:
            charge = partie.get_payload(decode=True) or b""
            texte.append(charge.decode(partie.get_content_charset() or "utf-8",
                                       "ignore"))
    return "\n".join(texte).strip(), vocaux


# --------------------------------------------------------------------------- #
# 2. L'accuse de reception : texte fige, jamais genere par une IA
# --------------------------------------------------------------------------- #
def accuser_reception(destinataire, nb_vocaux, nb_biens):
    matiere = ("votre vocal" if nb_vocaux == 1 else
               str(nb_vocaux) + " vocaux" if nb_vocaux else "votre message")
    sujet = "Bien recu, j'analyse"
    texte = (
        "Bonjour Christophe,\n\n"
        "Message automatique : " + matiere + " vient d'arriver et le traitement "
        "a demarre.\n\n"
        "La machine est en train de transcrire ce que vous avez dit, d'en "
        "extraire la fiche besoin, puis de la confronter une par une aux "
        + str(nb_biens) + " annonces publiees sur agence-rg.fr.\n\n"
        "Alexis vous renvoie le resultat complet, correspondances et refus "
        "motives, dans la journee. Il le relit avant de vous l'envoyer : "
        "aucune analyse ne part chez vous sans qu'un humain l'ait validee.\n\n"
        "Ce message-ci, en revanche, est parti tout seul. C'est deja un debut "
        "de reponse a votre question de l'autre jour.\n\n"
        "Alexis Bendavid\n06 80 55 18 36")
    html = (
        '<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;'
        'line-height:1.6;color:#1b2436;max-width:620px">'
        "<p>Bonjour Christophe,</p>"
        "<p><b>Message automatique</b> : " + matiere + " vient d'arriver et le "
        "traitement a demarre.</p>"
        "<p>La machine transcrit ce que vous avez dit, en extrait la fiche "
        "besoin, puis la confronte une par une aux <b>" + str(nb_biens)
        + " annonces</b> publiees sur agence-rg.fr.</p>"
        "<p>Alexis vous renvoie le resultat complet, correspondances "
        "<i>et</i> refus motives, dans la journee. Il le relit avant envoi : "
        "aucune analyse ne part chez vous sans qu'un humain l'ait validee.</p>"
        '<p style="background:#f4f7f9;border-left:4px solid ' + OR + ';'
        'padding:12px 14px">Ce message-ci, en revanche, est parti tout seul.'
        "<br>C'est deja un debut de reponse a votre question de l'autre jour.</p>"
        '<p style="color:#7a8296;font-size:12px;border-top:1px solid #e2e6ee;'
        'padding-top:8px">Alexis Bendavid &middot; 06 80 55 18 36</p></div>')
    envoyer(destinataire, sujet, texte, html)


# --------------------------------------------------------------------------- #
# 3. Analyser
# --------------------------------------------------------------------------- #
def charger_portefeuille():
    if not os.path.exists(PORTEFEUILLE):
        return []
    with io.open(PORTEFEUILLE, encoding="utf-8") as fh:
        return json.load(fh)


def incompatible(fiche, bien):
    """Ecarte sans IA les biens manifestement hors sujet.

    On reste TRES tolerant : 15 % au-dessus du budget, parce qu'un acquereur
    qui trouve exactement ce qu'il cherchait negocie ou se stretch. Le but
    n'est pas de filtrer finement, c'est d'eviter de payer une analyse fine
    sur un bien a 2,7 millions pour un budget de 900 000.
    """
    budget = fiche.get("budget_max")
    prix = bien.get("prix")
    if isinstance(budget, (int, float)) and isinstance(prix, (int, float)):
        if prix > budget * 1.15:
            return "hors budget (" + euros(prix) + " pour " + euros(budget) + " max)"
    souhaite = str(fiche.get("type_bien") or "").strip().lower()
    propose = str(bien.get("type") or "").strip().lower()
    if souhaite and propose and souhaite[:5] != propose[:5]:
        if souhaite in ("maison", "appartement") and propose in ("maison", "appartement"):
            return "type different (" + propose + " au lieu de " + souhaite + ")"
    return None


def analyser(texte_source, biens):
    fiche = _json_depuis(demander(
        CONSIGNE_EXTRACTION, "VOCAL DE DEBRIEF :\n\n" + texte_source).strip())
    fiche["source"] = "demo_raas"
    fiche.setdefault("date_echange", date.today().isoformat())

    retenus, ecartes_durs, analyses = [], [], 0
    for bien in biens:
        motif = incompatible(fiche, bien)
        if motif:
            ecartes_durs.append({"bien": bien, "motif": motif})
            continue
        invite = ("FICHE BESOIN DE L'ACQUEREUR :\n"
                  + json.dumps(fiche, ensure_ascii=False, indent=2)
                  + "\n\nBIEN DU PORTEFEUILLE :\n"
                  + json.dumps({k: v for k, v in bien.items()
                                if k not in ("url",)},
                               ensure_ascii=False, indent=2))
        try:
            r = _json_depuis(demander(CONSIGNE_MATCH, invite).strip())
        except (ValueError, KeyError, RuntimeError) as err:
            print("  bien " + str(bien.get("ref")) + " non evalue : " + str(err)[:80])
            continue
        r["ref_bien"] = bien.get("ref")
        r["bien"] = bien
        r["acquereur"] = fiche.get("acquereur")
        retenus.append(r)
        analyses += 1
        time.sleep(0.7)  # on reste poli avec le quota gratuit

    retenus.sort(key=lambda x: -(x.get("score") or 0))
    return fiche, retenus, ecartes_durs, analyses


# --------------------------------------------------------------------------- #
# 4. Le rapport, envoye a Alexis, pret a etre transfere
# --------------------------------------------------------------------------- #
def carte(r):
    b = r.get("bien", {})
    accent = VERT if (r.get("score") or 0) >= SEUIL else ROUGE
    reserves = "".join(
        '<div style="font:12px Helvetica,Arial,sans-serif;color:#a6704a;'
        'background:#fdf5ee;border-radius:4px;padding:6px 10px;margin-top:8px">'
        + str(x) + "</div>" for x in (r.get("reserves") or []))
    return (
        '<div style="border:1px solid #dfe4ea;border-left:5px solid ' + accent
        + ';border-radius:8px;padding:16px 18px;margin-bottom:12px">'
        '<div style="font:bold 16px Helvetica,Arial,sans-serif;color:' + NAVY + '">'
        + str(b.get("titre") or b.get("ref"))
        + '<span style="float:right;color:' + accent + ';font-size:13px">'
        + str(r.get("score")) + "/100</span></div>"
        '<div style="font:11px Helvetica,Arial,sans-serif;color:#8a97a3;'
        'margin:3px 0 10px">Ref. ' + str(b.get("ref")) + " &middot; "
        + str(b.get("adresse")) + " &middot; " + euros(b.get("prix"))
        + (" &middot; " + str(b.get("conseiller")) if b.get("conseiller") else "")
        + "</div>"
        + ('<div style="background:#f1f7f4;border-radius:6px;padding:12px 14px;'
           'font:15px Helvetica,Arial,sans-serif;color:#123d28;line-height:1.5">'
           + str(r.get("message_agent") or "") + "</div>" if r.get("message_agent") else "")
        + ('<div style="font:11px Helvetica,Arial,sans-serif;color:#8a97a3;'
           'text-transform:uppercase;letter-spacing:1px;margin:12px 0 3px">'
           "Il avait dit</div>"
           '<div style="font:italic 13px Helvetica,Arial,sans-serif;color:#43586a">'
           "&laquo;&nbsp;" + str(r.get("rappel_verbatim")) + "&nbsp;&raquo;</div>"
           if r.get("rappel_verbatim") else "")
        + ('<div style="font:11px Helvetica,Arial,sans-serif;color:#8a97a3;'
           'text-transform:uppercase;letter-spacing:1px;margin:10px 0 3px">'
           "Ce que dit votre annonce</div>"
           '<div style="font:italic 13px Helvetica,Arial,sans-serif;color:#43586a">'
           "&laquo;&nbsp;" + str(r.get("preuve_annonce")) + "&nbsp;&raquo;</div>"
           if r.get("preuve_annonce") else "")
        + reserves + "</div>")


def rapport(fiche, retenus, ecartes_durs, analyses, transcription, biens):
    bons = [r for r in retenus if (r.get("score") or 0) >= SEUIL]
    faibles = [r for r in retenus if (r.get("score") or 0) < SEUIL]
    nom = fiche.get("acquereur") or "l'acquereur"

    qualitatifs = "".join(
        '<li style="margin-bottom:6px"><b>' + str(c.get("besoin")) + "</b>"
        + (' <span style="color:#8a97a3">(' + str(c.get("pourquoi")) + ")</span>"
           if c.get("pourquoi") else "")
        + ('<br><i style="color:#43586a">&laquo;&nbsp;' + str(c.get("verbatim"))
           + "&nbsp;&raquo;</i>" if c.get("verbatim") else "") + "</li>"
        for c in (fiche.get("criteres_qualitatifs") or []))

    html = (
        '<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;'
        'line-height:1.6;color:#1b2436;max-width:680px">'
        '<div style="background:' + NAVY + ';color:#fff;border-radius:10px;'
        'padding:22px 24px;margin-bottom:18px">'
        '<div style="font-size:10px;letter-spacing:2.5px;text-transform:uppercase;'
        'color:#8fb2c4;margin-bottom:8px">Demonstration Agence RG</div>'
        '<div style="font-size:22px;font-weight:bold">' + nom + "</div>"
        '<div style="color:#c3d4de;font-size:13px;margin-top:6px">'
        + str(len(biens)) + " annonces passees &middot; " + str(len(ecartes_durs))
        + " ecartees sur criteres durs &middot; " + str(analyses)
        + " analysees en profondeur</div></div>"

        '<p style="color:' + NAVY + ';font-weight:700;margin:18px 0 4px">'
        "Ce que la machine a entendu</p>"
        '<div style="background:#f4f7f9;border-radius:6px;padding:12px 14px;'
        'font-style:italic;color:#43586a;font-size:13px">'
        + (transcription[:900] + ("..." if len(transcription) > 900 else ""))
        + "</div>"

        + ('<p style="color:' + NAVY + ';font-weight:700;margin:18px 0 4px">'
           "Les criteres qualitatifs qu'elle en a tires</p><ul>" + qualitatifs
           + "</ul>" if qualitatifs else "")

        + '<p style="color:' + NAVY + ';font-weight:700;margin:20px 0 8px">'
        + (str(len(bons)) + " correspondance(s) a rappeler" if bons
           else "Aucune correspondance au-dessus de " + str(SEUIL) + "/100")
        + "</p>"
        + "".join(carte(r) for r in bons)

        + ('<p style="color:' + NAVY + ';font-weight:700;margin:20px 0 8px">'
           "Ecartes apres analyse fine, avec le motif</p>"
           + "".join(carte(r) for r in faibles[:6]) if faibles else "")

        + ('<p style="color:' + NAVY + ';font-weight:700;margin:20px 0 6px">'
           "Ecartes d'emblee sur criteres durs</p>"
           '<div style="font-size:12px;color:#5a7080;line-height:1.7">'
           + "<br>".join("Ref. " + str(e["bien"].get("ref")) + " &middot; "
                         + str(e["bien"].get("titre") or "")[:44] + " &middot; "
                         + e["motif"] for e in ecartes_durs[:12])
           + ("<br>et " + str(len(ecartes_durs) - 12) + " autre(s)."
              if len(ecartes_durs) > 12 else "")
           + "</div>" if ecartes_durs else "")

        + '<p style="background:#fdfaf1;border:1px solid ' + OR + ';border-radius:6px;'
        'padding:12px 14px;margin-top:20px;font-size:13px;color:#6b5a2a">'
        "<b>A relire avant de transferer.</b> Christophe a deja recu l'accuse "
        "de reception automatique. Cette analyse-ci n'est partie qu'a vous.</p>"
        "</div>")

    texte = [nom.upper(), "",
             str(len(biens)) + " annonces passees, " + str(len(ecartes_durs))
             + " ecartees sur criteres durs, " + str(analyses) + " analysees.", ""]
    for r in bons:
        texte.append("[" + str(r.get("score")) + "/100] "
                     + str(r.get("bien", {}).get("titre")))
        texte.append("  " + str(r.get("message_agent")))
        texte.append("")
    texte.append("A relire avant transfert. Rien n'a ete envoye au client.")
    return html, "\n".join(texte), len(bons)


# --------------------------------------------------------------------------- #
def main():
    biens = charger_portefeuille()
    if not biens:
        print("Portefeuille vide : lancez d'abord aspirer_portefeuille.py")
        return

    messages = relever()
    if not messages:
        print("Aucun nouveau message de " + ", ".join(EXPEDITEURS) + ".")
        return

    deja = journal_lu()
    for identifiant, msg in messages:
        # Seconde barriere anti-doublon. La premiere est dans relever().
        # Deux verrous valent mieux qu'un quand la consequence d'une panne
        # est d'ecrire deux fois au meme client.
        if identifiant in deja:
            print("Message deja traite, ignore : " + str(identifiant))
            continue

        expediteur = parseaddr(msg.get("From"))[1]
        print("\nNouveau message de " + expediteur + " : " + _txt(msg.get("Subject")))

        corps, vocaux = depiecer(msg)

        if ACCUSE_AUTO:
            try:
                accuser_reception(expediteur, len(vocaux), len(biens))
            except (smtplib.SMTPException, OSError) as err:
                print("  accuse non envoye : " + str(err)[:120])

        transcriptions = []
        for chemin in vocaux:
            try:
                transcriptions.append(transcrire(chemin))
            except OreilleIndisponible as err:
                print("  vocal illisible : " + str(err)[:150])

        source = "\n\n".join([t for t in transcriptions if t] + ([corps] if corps else []))
        if len(source.strip()) < 40:
            envoyer(GMAIL_ADDRESS, "Demo Raas : message inexploitable",
                    "Message recu de " + expediteur + " mais ni vocal lisible "
                    "ni texte suffisant. A traiter a la main.")
            deja.append(identifiant)
            journal_ecrit(deja)
            continue

        fiche, retenus, ecartes, analyses = analyser(source, biens)
        html, texte, nb = rapport(fiche, retenus, ecartes, analyses, source, biens)

        sujet = ("Demo Raas : " + str(nb) + " correspondance(s) sur "
                 + str(fiche.get("acquereur") or "l'acquereur"))
        envoyer(GMAIL_ADDRESS, sujet, texte, html)

        deja.append(identifiant)
        journal_ecrit(deja)
        print("  traite. " + str(nb) + " correspondance(s) retenue(s).")


def surveiller(minutes, intervalle=60):
    """Surveille la boite en continu pendant N minutes.

    Pourquoi ce mode existe
    -----------------------
    Le planificateur de GitHub n'est pas ponctuel : une tache reglee toutes
    les 10 minutes peut n'etre lancee qu'une heure plus tard. Or on a promis
    a Christophe Raas un accuse de reception rapide, et une promesse tenue
    en retard est pire qu'une promesse non faite.

    Plutot que de dependre du planificateur, on lance UNE execution longue
    qui regarde la boite toutes les 60 secondes. Le planificateur ne sert
    plus qu'a relancer la surveillance quand elle se termine, et son retard
    n'a plus d'importance.

    Une panne passagere (reseau, quota) n'interrompt pas la surveillance :
    on note l'incident et on reessaie au tour suivant.
    """
    fin = time.time() + minutes * 60
    tour, incidents = 0, 0
    print("Surveillance de la boite pendant " + str(minutes) + " minutes, "
          "toutes les " + str(intervalle) + " secondes.\n")
    while time.time() < fin:
        tour += 1
        try:
            main()
        except Exception as err:  # noqa: BLE001
            incidents += 1
            print("Tour " + str(tour) + " : incident ignore (" + str(err)[:120] + ")")
        restant = fin - time.time()
        if restant <= 0:
            break
        time.sleep(min(intervalle, restant))
    print("\nSurveillance terminee. " + str(tour) + " tour(s), "
          + str(incidents) + " incident(s).")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Boucle de demonstration Raas")
    p.add_argument("--boucle", type=int, default=0,
                   help="minutes de surveillance continue (0 = un seul passage)")
    p.add_argument("--intervalle", type=int, default=60,
                   help="secondes entre deux relevees")
    args = p.parse_args()
    if args.boucle:
        surveiller(args.boucle, args.intervalle)
    else:
        main()
