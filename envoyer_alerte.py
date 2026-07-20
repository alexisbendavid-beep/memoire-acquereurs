#!/usr/bin/env python3
"""Envoie l'alerte des rapprochements par Gmail, depuis GitHub Actions.

Destinataire : Alexis uniquement. Aucun client ne recoit jamais rien.

Anti-doublon : chaque couple acquereur/bien deja signale est memorise dans
alertes_envoyees.json. Le robot tourne toutes les 30 minutes mais ne t'ecrit
que lorsqu'il a du NOUVEAU. Sinon il se tait.
"""

import os
import sys
import ssl
import json
import smtplib
from datetime import date
from email.message import EmailMessage

RACINE = os.path.dirname(os.path.abspath(__file__))
RAPPROCHEMENTS = os.path.join(RACINE, "rapprochements.json")
BIENS = os.path.join(RACINE, "donnees_demo", "biens.json")
DEJA_VU = os.path.join(RACINE, "alertes_envoyees.json")

APERCU = "--apercu" in sys.argv

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "apercu@local")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
DESTINATAIRE = os.environ.get("ALERTE_DESTINATAIRE", GMAIL_ADDRESS)
SEUIL = int(os.environ.get("SEUIL_ALERTE", "70"))
SMTP_HOST = "smtp.gmail.com"
APERCU_HTML = os.path.join(RACINE, "apercu_alerte_mail.html")

NAVY = "#12232f"
OR = "#c9a227"
VERT = "#1f7a4d"
ROUGE = "#b03b3b"


def charger():
    with open(RAPPROCHEMENTS, encoding="utf-8") as fh:
        rapprochements = json.load(fh)
    with open(BIENS, encoding="utf-8") as fh:
        biens = {b["ref"]: b for b in json.load(fh)}
    deja = []
    if os.path.exists(DEJA_VU):
        with open(DEJA_VU, encoding="utf-8") as fh:
            deja = json.load(fh)
    return rapprochements, biens, deja


def cle(r):
    return str(r.get("acquereur")) + "|" + str(r.get("ref_bien"))


def euros(n):
    return format(int(n), ",d").replace(",", "\u202f") + "\u202f\u20ac"


# --------------------------------------------------------------------------- #
# Le mail. Mise en page en tableaux et styles en ligne : c'est la seule facon
# d'obtenir un rendu fiable dans Gmail, Outlook et sur mobile.
# --------------------------------------------------------------------------- #
def carte(r, bien):
    accent = VERT
    score = str(r.get("score")) + "/100"
    return f"""
<tr><td style="padding:0 0 14px">
 <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #dfe4ea;
   border-left:5px solid {accent};border-radius:8px;background:#ffffff">
  <tr><td style="padding:18px 20px">

   <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
     <td style="font:bold 17px Helvetica,Arial,sans-serif;color:{NAVY}">
       {r.get('acquereur')}</td>
     <td align="right" style="font:bold 13px Helvetica,Arial,sans-serif;color:{accent}">
       {score}</td>
    </tr>
    <tr><td colspan="2" style="font:11px Helvetica,Arial,sans-serif;color:#8a97a3;
      padding-top:3px">{r.get('ref_bien')} &middot; {bien.get('adresse','')}
      &middot; {euros(bien.get('prix',0))}</td></tr>
   </table>

   <div style="background:#f1f7f4;border-radius:6px;padding:13px 15px;margin:14px 0 12px;
     font:500 15px Helvetica,Arial,sans-serif;color:#123d28;line-height:1.5">
     {r.get('message_agent','')}</div>

   <div style="font:11px Helvetica,Arial,sans-serif;color:#8a97a3;text-transform:uppercase;
     letter-spacing:1px;margin-bottom:3px">
     Il avait dit, il y a {r.get('anciennete_besoin_jours', 0)} jours</div>
   <div style="font:italic 13px Helvetica,Arial,sans-serif;color:#43586a;
     line-height:1.5;margin-bottom:11px">&laquo;&nbsp;{r.get('rappel_verbatim','')}&nbsp;&raquo;</div>

   <div style="font:11px Helvetica,Arial,sans-serif;color:#8a97a3;text-transform:uppercase;
     letter-spacing:1px;margin-bottom:3px">Ce que dit l'annonce</div>
   <div style="font:italic 13px Helvetica,Arial,sans-serif;color:#43586a;
     line-height:1.5">&laquo;&nbsp;{r.get('preuve_annonce','')}&nbsp;&raquo;</div>

   {''.join('<div style="font:12px Helvetica,Arial,sans-serif;color:#a6704a;'
            'background:#fdf5ee;border-radius:4px;padding:6px 10px;margin-top:10px">'
            + res + '</div>' for res in r.get('reserves', []))}

  </td></tr>
 </table>
</td></tr>"""


def bloc_rejets(rejets, biens):
    if not rejets:
        return ""
    lignes = "".join(
        f"""<tr><td style="padding:9px 0;border-bottom:1px solid #f0f3f6">
          <span style="font:bold 13px Helvetica,Arial,sans-serif;color:{NAVY}">
            {r.get('acquereur')}</span>
          <span style="font:12px Helvetica,Arial,sans-serif;color:#8a97a3"> &middot;
            {biens.get(r.get('ref_bien'), {}).get('adresse', r.get('ref_bien'))}</span>
          <span style="font:bold 12px Helvetica,Arial,sans-serif;color:{ROUGE}"> &middot;
            {r.get('score')}/100</span>
          <div style="font:12px Helvetica,Arial,sans-serif;color:#5a7080;
            line-height:1.45;margin-top:3px">{r.get('message_agent','')}</div>
        </td></tr>""" for r in rejets)
    return f"""
<tr><td style="padding:8px 0 0">
  <div style="font:bold 11px Helvetica,Arial,sans-serif;color:#8a97a3;
    text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px">
    Écartés volontairement</div>
  <table width="100%" cellpadding="0" cellspacing="0"
    style="border:1px solid #dfe4ea;border-radius:8px;background:#fff;padding:4px 16px">
    {lignes}
  </table>
</td></tr>"""


def construire_mail(nouveaux, rejets, biens):
    cartes = "".join(carte(r, biens.get(r["ref_bien"], {})) for r in nouveaux)
    n = len(nouveaux)
    titre = "1 acquéreur à rappeler" if n == 1 else str(n) + " acquéreurs à rappeler"

    html = f"""<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#eef1f4">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#eef1f4;padding:24px 12px">
<tr><td align="center">
 <table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%">

  <tr><td style="background:{NAVY};border-radius:10px 10px 0 0;padding:26px 24px 22px">
    <div style="font:bold 10px Helvetica,Arial,sans-serif;color:#8fb2c4;
      letter-spacing:2.5px;text-transform:uppercase;margin-bottom:9px">
      Mémoire des acquéreurs</div>
    <div style="font:bold 25px Helvetica,Arial,sans-serif;color:#ffffff;
      line-height:1.2">{titre}</div>
    <div style="font:14px Helvetica,Arial,sans-serif;color:#c3d4de;margin-top:7px">
      De nouveaux mandats correspondent à des besoins exprimés il y a plusieurs mois.</div>
  </td></tr>

  <tr><td style="background:#ffffff;padding:20px 20px 8px">
    <table width="100%" cellpadding="0" cellspacing="0">
      {cartes}
      {bloc_rejets(rejets, biens)}
    </table>
  </td></tr>

  <tr><td style="background:#ffffff;border-radius:0 0 10px 10px;padding:4px 24px 24px;
    border-top:1px solid #f0f3f6">
    <div style="font:12px Helvetica,Arial,sans-serif;color:#8a97a3;line-height:1.6;
      padding-top:14px">
      Alerte interne, envoyée à vous seul. Aucun client n'a été contacté.<br>
      Robot Mémoire des acquéreurs &middot; {date.today().strftime('%d/%m/%Y')}
    </div>
  </td></tr>

 </table>
</td></tr></table>
</body></html>"""

    texte = [titre.upper(), ""]
    for r in nouveaux:
        texte.append("[" + str(r.get("score")) + "/100] " + str(r.get("acquereur"))
                     + " -> " + str(r.get("ref_bien")))
        texte.append("  " + str(r.get("message_agent")))
        texte.append("  Il avait dit : " + str(r.get("rappel_verbatim")))
        texte.append("")
    for r in rejets:
        texte.append("[ECARTE " + str(r.get("score")) + "/100] " + str(r.get("acquereur")))
        texte.append("  " + str(r.get("message_agent")))
        texte.append("")
    texte.append("Alerte interne. Aucun client n'a ete contacte.")
    return titre, html, "\n".join(texte)


def main():
    rapprochements, biens, deja = charger()
    retenus = [r for r in rapprochements if r.get("score", 0) >= SEUIL]
    rejets = [r for r in rapprochements if r.get("score", 0) < SEUIL]

    nouveaux = retenus if APERCU else [r for r in retenus if cle(r) not in deja]
    nouveaux.sort(key=lambda x: -x.get("score", 0))

    if not nouveaux:
        print("Aucun nouveau rapprochement. Pas de mail envoye.")
        return

    titre, html, texte = construire_mail(nouveaux, rejets, biens)

    if APERCU:
        with open(APERCU_HTML, "w", encoding="utf-8") as fh:
            fh.write(html)
        print("Apercu ecrit : " + APERCU_HTML)
        print("Objet du mail : Mémoire des acquéreurs : " + titre)
        print(str(len(nouveaux)) + " carte(s), " + str(len(rejets)) + " ecarte(s).")
        return

    em = EmailMessage()
    em["From"] = GMAIL_ADDRESS
    em["To"] = DESTINATAIRE
    em["Subject"] = "Mémoire des acquéreurs : " + titre
    em.set_content(texte)
    em.add_alternative(html, subtype="html")

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, 465, context=ctx) as s:
        s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        s.send_message(em)
    print("Alerte envoyee a " + DESTINATAIRE + " : " + titre)

    deja.extend(cle(r) for r in nouveaux)
    with open(DEJA_VU, "w", encoding="utf-8") as fh:
        json.dump(deja, fh, ensure_ascii=False, indent=2)
    print(str(len(deja)) + " rapprochements memorises, ils ne seront pas resignales.")


if __name__ == "__main__":
    main()
