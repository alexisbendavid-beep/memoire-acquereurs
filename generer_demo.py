#!/usr/bin/env python3
"""Genere la page de demonstration a partir des donnees reelles du moteur."""

import os
import json
import html
from datetime import date

RACINE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(RACINE, "demo_raas.html")

with open(os.path.join(RACINE, "memoire_acquereurs.json"), encoding="utf-8") as fh:
    FICHES = json.load(fh)
with open(os.path.join(RACINE, "rapprochements.json"), encoding="utf-8") as fh:
    RAPPROCHEMENTS = json.load(fh)
with open(os.path.join(RACINE, "donnees_demo", "biens.json"), encoding="utf-8") as fh:
    BIENS = {b["ref"]: b for b in json.load(fh)}
with open(os.path.join(RACINE, "donnees_demo", "vocaux", "2026-03-14_jean_vasseur.txt"),
          encoding="utf-8") as fh:
    VOCAL_JEAN = fh.read().strip()

e = html.escape
FICHE_JEAN = next(f for f in FICHES if f["acquereur"] == "Jean Vasseur")
retenus = sorted([r for r in RAPPROCHEMENTS if r.get("score", 0) >= 70],
                 key=lambda x: -x.get("score", 0))
rejets = [r for r in RAPPROCHEMENTS if r.get("score", 0) < 70]
nb_qualitatifs = sum(len(f.get("criteres_qualitatifs", [])) for f in FICHES)


def euros(n):
    return format(n, ",d").replace(",", " ") + " EUR"


# --------------------------------------------------------------------------- #
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
color:#1a1a1a;line-height:1.6;background:#f7f8fa}
.wrap{max-width:920px;margin:0 auto;padding:0 24px 80px}
header{background:#12232f;color:#fff;padding:54px 24px 46px;margin-bottom:0}
header .wrap{padding-bottom:0}
.kicker{font-size:11px;letter-spacing:2.5px;text-transform:uppercase;color:#8fb2c4;margin-bottom:14px}
h1{font-size:34px;font-weight:700;letter-spacing:-.5px;margin-bottom:12px}
header p{color:#c3d4de;font-size:16px;max-width:640px}
.stats{display:flex;gap:0;margin:34px 0 0;border-top:1px solid rgba(255,255,255,.15);padding-top:24px}
.stat{flex:1}
.stat b{display:block;font-size:26px;color:#fff;font-weight:700}
.stat span{font-size:12px;color:#8fb2c4;text-transform:uppercase;letter-spacing:1px}
section{margin-top:44px}
h2{font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#5a7080;
margin-bottom:8px;font-weight:700}
.lead{font-size:18px;color:#12232f;margin-bottom:22px;font-weight:600}
.card{background:#fff;border:1px solid #e2e7ec;border-radius:10px;padding:24px;margin-bottom:16px}
.step{display:flex;gap:16px;align-items:flex-start;margin-bottom:14px}
.num{flex:0 0 30px;height:30px;border-radius:50%;background:#12232f;color:#fff;
display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700}
.step h3{font-size:16px;margin-bottom:2px}
.step p{font-size:14px;color:#5a7080}
.vocal{background:#12232f;color:#d8e4ea;border-radius:10px;padding:22px 24px;
font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px;line-height:1.75;
white-space:pre-wrap}
.vocal .hl{background:#c9a227;color:#12232f;padding:1px 4px;border-radius:3px;font-weight:600}
.arrow{text-align:center;color:#9aa8b3;font-size:22px;margin:12px 0}
.crit{border-left:3px solid #c9a227;padding:12px 0 12px 16px;margin-bottom:14px}
.crit b{display:block;font-size:15px;color:#12232f}
.crit .vb{font-size:13px;color:#5a7080;font-style:italic;margin-top:4px}
.crit .wy{font-size:12px;color:#7a8b96;margin-top:4px}
.tag{display:inline-block;background:#eef1f4;color:#43586a;font-size:11px;
padding:3px 9px;border-radius:20px;margin:0 6px 6px 0;font-weight:600}
.alert{border:1px solid #e2e7ec;border-left:5px solid #1f7a4d;border-radius:10px;
background:#fff;padding:22px 24px;margin-bottom:14px}
.alert.rej{border-left-color:#b03b3b}
.ah{display:flex;justify-content:space-between;align-items:baseline;
border-bottom:1px solid #eef1f4;padding-bottom:12px;margin-bottom:14px;gap:16px}
.ah b{font-size:17px;color:#12232f}
.ah .ref{font-size:12px;color:#7a8b96;font-family:ui-monospace,monospace}
.score{font-size:13px;font-weight:700;color:#1f7a4d;white-space:nowrap}
.alert.rej .score{color:#b03b3b}
.msg{background:#f2f7f4;border-radius:7px;padding:14px 16px;font-size:15px;
color:#123d28;margin-bottom:14px;font-weight:500}
.alert.rej .msg{background:#faf1f1;color:#6d2020}
.pair{font-size:13px;margin-bottom:9px}
.pair span{display:block;color:#7a8b96;font-size:11px;text-transform:uppercase;
letter-spacing:1px;margin-bottom:2px}
.pair i{color:#43586a;font-style:italic}
.age{font-size:12px;color:#a6704a;background:#fdf5ee;border-radius:4px;
padding:4px 9px;display:inline-block;margin-top:8px}
.punch{background:#12232f;color:#fff;border-radius:10px;padding:32px}
.punch h3{font-size:20px;margin-bottom:12px}
.punch p{color:#c3d4de;font-size:15px;margin-bottom:10px}
.punch .sig{margin-top:22px;padding-top:18px;border-top:1px solid rgba(255,255,255,.15);
font-size:13px;color:#8fb2c4}
footer{text-align:center;color:#9aa8b3;font-size:12px;margin-top:40px}
@media(max-width:640px){.stats{flex-wrap:wrap;gap:18px}.stat{flex:0 0 45%}h1{font-size:26px}}
"""


def bloc_vocal():
    """Surligne les passages decisifs, meme coupes par un retour a la ligne."""
    import re as _re
    txt = e(VOCAL_JEAN)
    fragments = ["lisiere de foret",
                 "sortir de chez lui et etre dans les bois en cinq minutes a pied",
                 "il le promene tous les matins a six heures et demie",
                 "pas de gros travaux de structure"]
    for frag in fragments:
        motif = r"\s+".join(_re.escape(mot) for mot in e(frag).split())
        txt = _re.sub(motif,
                      lambda m: "<span class='hl'>" + m.group(0) + "</span>",
                      txt, count=1)
    return "<div class='vocal'>" + txt + "</div>"


def bloc_fiche():
    h = ["<div class='card'>"]
    h.append("<div style='margin-bottom:16px'>")
    h.append("<b style='font-size:18px'>" + e(FICHE_JEAN["acquereur"]) + "</b>")
    h.append("<div style='font-size:13px;color:#7a8b96'>Echange du "
             + e(FICHE_JEAN["date_echange"]) + " . Source : " + e(FICHE_JEAN["source"]) + "</div>")
    h.append("</div>")
    h.append("<div style='margin-bottom:18px'>")
    for c in FICHE_JEAN["criteres_durs"]:
        h.append("<span class='tag'>" + e(c) + "</span>")
    for c in FICHE_JEAN["redhibitoires"]:
        h.append("<span class='tag' style='background:#faf1f1;color:#b03b3b'>Redhibitoire : "
                 + e(c) + "</span>")
    h.append("</div>")
    h.append("<div style='font-size:11px;letter-spacing:1.5px;text-transform:uppercase;"
             "color:#c9a227;font-weight:700;margin-bottom:12px'>"
             "Criteres qualitatifs captures</div>")
    for c in FICHE_JEAN["criteres_qualitatifs"]:
        h.append("<div class='crit'><b>" + e(c["besoin"]) + "</b>"
                 + "<div class='vb'>\"" + e(c["verbatim"]) + "\"</div>"
                 + "<div class='wy'>Pourquoi : " + e(c["pourquoi"]) + "</div></div>")
    h.append("</div>")
    return "".join(h)


def bloc_alerte(r, rejet=False):
    """Tolerant aux champs manquants : les rapprochements viennent de l'IA,
    qui peut omettre une cle. Un affichage ne doit jamais casser le robot."""
    bien = BIENS.get(r.get("ref_bien"), {})
    cls = "alert rej" if rejet else "alert"
    prix = bien.get("prix")
    h = ["<div class='" + cls + "'>"]
    h.append("<div class='ah'><div><b>" + e(str(r.get("acquereur", "?"))) + "</b>"
             "<div class='ref'>" + e(str(r.get("ref_bien", ""))) + " . "
             + e(str(bien.get("adresse", "")))
             + (" . " + euros(prix) if isinstance(prix, int) else "") + "</div></div>"
             "<div class='score'>" + str(r.get("score", 0)) + "/100</div></div>")
    if r.get("message_agent"):
        h.append("<div class='msg'>" + e(str(r["message_agent"])) + "</div>")
    if r.get("rappel_verbatim"):
        h.append("<div class='pair'><span>Il avait dit, il y a "
                 + str(r.get("anciennete_besoin_jours", 0)) + " jours</span><i>\""
                 + e(str(r["rappel_verbatim"])) + "\"</i></div>")
    if r.get("preuve_annonce"):
        h.append("<div class='pair'><span>Ce que dit l'annonce</span><i>\""
                 + e(str(r["preuve_annonce"])) + "\"</i></div>")
    for res in r.get("reserves", []) or []:
        h.append("<div class='age'>" + e(str(res)) + "</div>")
    h.append("</div>")
    return "".join(h)


doc = ["<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'>",
       "<meta name='viewport' content='width=device-width,initial-scale=1'>",
       "<title>La memoire des acquereurs - Agence RG</title>",
       "<style>" + CSS + "</style></head><body>"]

doc.append("<header><div class='wrap'>")
doc.append("<div class='kicker'>Demonstration preparee pour l'Agence RG</div>")
doc.append("<h1>Le test du chien de Jean</h1>")
doc.append("<p>Vous m'avez dit qu'aucune API ne saurait retenir que Jean cherche une "
           "lisiere de foret parce qu'il y promene son chien. Vous avez raison. "
           "Voici ce qui sait le faire, teste sur cinq acquereurs et six mandats.</p>")
doc.append("<div class='stats'>")
doc.append("<div class='stat'><b>" + str(len(FICHES)) + "</b><span>vocaux lus</span></div>")
doc.append("<div class='stat'><b>" + str(nb_qualitatifs) + "</b><span>criteres qualitatifs captures</span></div>")
doc.append("<div class='stat'><b>" + str(len(retenus)) + "</b><span>rapprochements trouves</span></div>")
doc.append("<div class='stat'><b>" + str(len(rejets)) + "</b><span>faux positif ecarte</span></div>")
doc.append("</div></div></header>")

doc.append("<div class='wrap'>")

doc.append("<section><h2>Le principe</h2>"
           "<div class='lead'>Trois etapes, soixante secondes de votre temps par client.</div>"
           "<div class='card'>"
           "<div class='step'><div class='num'>1</div><div><h3>Vous dictez</h3>"
           "<p>Apres un appel ou une visite, soixante secondes de vocal, comme vous me "
           "l'auriez raconte au telephone. Vos clients ne sont jamais enregistres.</p></div></div>"
           "<div class='step'><div class='num'>2</div><div><h3>La memoire retient</h3>"
           "<p>Le besoin reel est extrait, y compris ce que personne ne note jamais. "
           "Il ne se perd plus dans un carnet ni dans votre tete.</p></div></div>"
           "<div class='step'><div class='num'>3</div><div><h3>Elle vous rappelle</h3>"
           "<p>Chaque mandat entrant est confronte a toute la memoire. Quand ca correspond, "
           "meme des mois plus tard, vous recevez le rappel.</p></div></div>"
           "</div></section>")

doc.append("<section><h2>Etape 1 . Ce que vous dictez</h2>"
           "<div class='lead'>Votre vocal du 14 mars, tel quel.</div>")
doc.append(bloc_vocal())
doc.append("<div class='arrow'>&#8595;</div></section>")

doc.append("<section><h2>Etape 2 . Ce que la memoire en retient</h2>"
           "<div class='lead'>En jaune ci-dessus, ce qu'aucun champ de logiciel ne stocke. "
           "En voici la traduction.</div>")
doc.append(bloc_fiche())
doc.append("<div class='arrow'>&#8595;</div></section>")

doc.append("<section><h2>Etape 3 . Ce qui arrive sur votre telephone</h2>"
           "<div class='lead'>Six mandats entrent au portefeuille. Voici les rappels declenches.</div>")
for r in retenus:
    doc.append(bloc_alerte(r))
doc.append("</section>")

doc.append("<section><h2>Et surtout, ce qu'elle refuse de vous proposer</h2>"
           "<div class='lead'>Un moteur qui dit toujours oui ne sert a rien.</div>")
for r in rejets:
    doc.append(bloc_alerte(r, rejet=True))
doc.append("</section>")

doc.append("<section><div class='punch'>"
           "<h3>Pourquoi votre logiciel metier ne peut pas faire ca</h3>"
           "<p>Agence Plus, votre outil de demarchage cadastre et vos entrants prequalifies "
           "travaillent tous sur des champs : prix, surface, nombre de pieces, code postal. "
           "Ils font tres bien ce pour quoi ils sont faits.</p>"
           "<p>Mais &laquo; lisiere de foret &raquo; n'est pas un champ. "
           "&laquo; La belle-mere a moins de vingt minutes &raquo; n'est pas un champ. "
           "&laquo; Elle ne peut pas travailler dans le noir &raquo; n'est pas un champ. "
           "Ces informations vivent dans vos conversations, puis dans votre tete, "
           "et elles finissent par se perdre.</p>"
           "<p>Je ne remplace aucun de vos outils et je ne vous en ajoute pas un. "
           "J'ajoute une memoire au-dessus de ceux que vous avez deja.</p>"
           "<div class='sig'>Alexis Bendavid . Employe IA et automatisation de process<br>"
           "06 80 55 18 36 . alexis.bendavid@gmail.com</div>"
           "</div></section>")

doc.append("<footer>Demonstration generee le " + date.today().strftime("%d/%m/%Y")
           + " sur donnees fictives representatives du secteur Garches, Vaucresson, "
             "Saint-Cloud, Ville-d'Avray.</footer>")
doc.append("</div></body></html>")

with open(SORTIE, "w", encoding="utf-8") as fh:
    fh.write("".join(doc))

print("Page generee : " + SORTIE)
print(str(len(FICHES)) + " fiches, " + str(nb_qualitatifs) + " criteres qualitatifs, "
      + str(len(retenus)) + " rapprochements, " + str(len(rejets)) + " rejet.")
