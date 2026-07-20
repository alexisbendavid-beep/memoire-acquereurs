#!/usr/bin/env python3
"""Genere le dossier PDF de demonstration pour Christophe Raas (Agence RG)."""

import os
from datetime import date
from weasyprint import HTML

RACINE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(RACINE, "Memoire_des_acquereurs_Agence_RG.pdf")

NAVY = "#12232f"
OR = "#c9a227"
VERT = "#1f7a4d"
ROUGE = "#b03b3b"

CSS = """
@page { size:A4; margin:14mm 15mm 16mm; @bottom-center{ content:element(pied); } }
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Helvetica,Arial,sans-serif;color:#1f2933;font-size:10pt;line-height:1.5}
.pied{position:running(pied);font-size:7pt;color:#8a97a3;text-align:center;
border-top:1px solid #dfe4ea;padding-top:4px;width:100%}

.cover{background:@NAVY@;color:#fff;padding:26px 26px 22px;border-radius:8px;margin-bottom:18px}
.kick{font-size:7.5pt;letter-spacing:2.5px;text-transform:uppercase;color:#8fb2c4;margin-bottom:9px}
.cover h1{font-size:25pt;letter-spacing:-.5px;margin-bottom:8px;line-height:1.15}
.cover p{color:#c3d4de;font-size:10.5pt}
.cover .who{margin-top:16px;padding-top:12px;border-top:1px solid rgba(255,255,255,.16);
font-size:8.5pt;color:#8fb2c4}

h2{font-size:8pt;letter-spacing:2px;text-transform:uppercase;color:#5a7080;
margin:20px 0 5px;font-weight:bold}
.lead{font-size:13pt;color:@NAVY@;font-weight:bold;margin-bottom:12px;line-height:1.3}
p.t{margin-bottom:8px}

/* ---- schema ---- */
.flow{width:100%;border-collapse:collapse;margin:6px 0 4px}
.flow td{vertical-align:top;padding:0}
.bx{border:1.5px solid @NAVY@;border-radius:7px;padding:11px 12px;background:#fff}
.bx .n{display:inline-block;width:19px;height:19px;border-radius:50%;background:@NAVY@;
color:#fff;font-size:8.5pt;font-weight:bold;text-align:center;line-height:19px;margin-bottom:6px}
.bx h3{font-size:10.5pt;color:@NAVY@;margin-bottom:4px}
.bx p{font-size:8.5pt;color:#5a7080;line-height:1.45}
.ar{width:26px;text-align:center;font-size:17pt;color:@OR@;padding-top:32px !important}

.mem{border:1.5px dashed @OR@;border-radius:7px;background:#fdfaf1;padding:11px 13px;margin:9px 0}
.mem b{color:#8a6d14;font-size:9.5pt}
.mem p{font-size:8.5pt;color:#6b5a2a;margin-top:3px}

.pipe{width:100%;border-collapse:collapse;margin:8px 0}
.pipe td{padding:8px 10px;border:1px solid #dfe4ea;font-size:8.5pt;vertical-align:top}
.pipe .hd{background:@NAVY@;color:#fff;font-weight:bold;font-size:8pt;
text-transform:uppercase;letter-spacing:1px;border-color:@NAVY@}

/* ---- cas ---- */
.case{border:1px solid #dfe4ea;border-left:4px solid @VERT@;border-radius:6px;
padding:12px 14px;margin-bottom:9px;background:#fff}
.case.ko{border-left-color:@ROUGE@}
.case .hh{display:flex;justify-content:space-between;font-size:9.5pt;font-weight:bold;
color:@NAVY@;margin-bottom:7px}
.case .sc{color:@VERT@;font-size:9pt}
.case.ko .sc{color:@ROUGE@}
.case .say{background:#f4f7f9;border-radius:4px;padding:7px 9px;font-size:8.5pt;
font-style:italic;color:#43586a;margin-bottom:6px}
.case .out{background:#f1f7f4;border-radius:4px;padding:8px 9px;font-size:9pt;color:#123d28}
.case.ko .out{background:#faf1f1;color:#6d2020}

.warn{border:1px solid @OR@;background:#fdfaf1;border-radius:6px;padding:11px 13px;margin:10px 0}
.warn b{color:#8a6d14}
.warn p{font-size:9pt;color:#6b5a2a;margin-top:3px}

/* ---- mode d'emploi ---- */
.st{border:1px solid #dfe4ea;border-radius:6px;padding:11px 13px;margin-bottom:8px;background:#fff}
.st .num{color:@OR@;font-weight:bold;font-size:8pt;letter-spacing:1.5px;
text-transform:uppercase;margin-bottom:3px}
.st h4{font-size:10.5pt;color:@NAVY@;margin-bottom:4px}
.st p{font-size:9pt;color:#5a7080}
.ex{background:@NAVY@;color:#d8e4ea;border-radius:6px;padding:12px 14px;
font-family:'DejaVu Sans Mono',monospace;font-size:8pt;line-height:1.65;white-space:pre-wrap;
margin:7px 0}
.ex .g{color:@OR@}

.punch{background:@NAVY@;color:#fff;border-radius:8px;padding:18px 20px;margin-top:14px}
.punch h3{font-size:13pt;margin-bottom:8px}
.punch p{color:#c3d4de;font-size:9.5pt;margin-bottom:6px}
.sig{margin-top:12px;padding-top:10px;border-top:1px solid rgba(255,255,255,.16);
font-size:8.5pt;color:#8fb2c4}
.brk{page-break-before:always}
"""
CSS = (CSS.replace("@NAVY@", NAVY).replace("@OR@", OR)
          .replace("@VERT@", VERT).replace("@ROUGE@", ROUGE))


def page1():
    return """
<div class='cover'>
  <div class='kick'>Preparé pour l'Agence RG &middot; Garches et Vaucresson</div>
  <h1>La mémoire des acquéreurs</h1>
  <p>Vous m'avez dit qu'aucune API ne saurait retenir que Jean cherche une lisière
  de forêt parce qu'il y promène son chien. Vous aviez raison. Voici ce qui sait
  le faire, et comment vous pouvez le tester vous-même.</p>
  <div class='who'>Alexis Bendavid &middot; Employé IA et automatisation de process</div>
</div>

<h2>Le principe en une image</h2>
<div class='lead'>Soixante secondes de votre temps par client. Le reste tourne tout seul.</div>

<table class='flow'>
<tr>
  <td width='31%'><div class='bx'><span class='n'>1</span>
    <h3>Vous dictez</h3>
    <p>Après un appel ou une visite, soixante secondes de vocal, comme vous me
    l'auriez raconté au téléphone. Vous ne changez rien à votre façon de travailler.</p></div></td>
  <td class='ar'>&#10230;</td>
  <td width='31%'><div class='bx'><span class='n'>2</span>
    <h3>La mémoire retient</h3>
    <p>Le besoin réel est extrait, y compris ce que personne ne note jamais&nbsp;:
    la lisière de bois, l'école à pied, la belle-mère à vingt minutes.</p></div></td>
  <td class='ar'>&#10230;</td>
  <td width='31%'><div class='bx'><span class='n'>3</span>
    <h3>Elle vous rappelle</h3>
    <p>Chaque mandat qui entre est confronté à toute la mémoire. Quand ça
    correspond, même des mois après, vous recevez le rappel.</p></div></td>
</tr>
</table>

<div class='mem'>
  <b>Au centre : la mémoire, et c'est tout l'intérêt</b>
  <p>Un besoin dicté en mars est toujours vivant en juillet. Il ne dépend plus de
  votre carnet ni de ce dont vous vous souvenez un mardi matin. C'est la seule
  pièce que vos logiciels n'ont pas.</p>
</div>

<h2>Ce qui entre, ce qui sort</h2>
<table class='pipe'>
<tr><td class='hd' width='33%'>Entrée</td><td class='hd' width='34%'>Traitement</td>
    <td class='hd' width='33%'>Sortie</td></tr>
<tr>
 <td>Votre vocal de débrief, en langage parlé, sans structure imposée.<br><br>
     Vos mandats, tels qu'ils entrent au portefeuille.</td>
 <td>Extraction du besoin réel, critères chiffrés et critères humains.<br><br>
     Confrontation de chaque mandat à l'ensemble des acquéreurs en mémoire.</td>
 <td>Un rappel nommé, avec la phrase à lire avant de décrocher, la preuve dans
     l'annonce et le verbatim d'origine.<br><br>
     Et les rejets motivés.</td>
</tr>
</table>

<div class='warn'>
  <b>Un point que je préfère vous dire tout de suite</b>
  <p>Vous m'avez parlé d'un système qui écoute vos conversations. Je ne le fais pas,
  et c'est volontaire&nbsp;: enregistrer un client sans son accord est illégal, et je
  ne vous mettrai pas dans cette situation. C'est vous qui dictez, après coup.
  Même matière première, aucun risque juridique.</p>
</div>
"""


def page2():
    return """
<div class='brk'></div>
<h2>La démonstration, sur six mandats</h2>
<div class='lead'>Cinq acquéreurs dictés entre mars et mai. Six biens entrés en juillet.</div>

<div class='case'>
  <div class='hh'><span>Jean Vasseur &middot; besoin dicté le 14 mars</span><span class='sc'>94/100</span></div>
  <div class='say'>Il avait dit&nbsp;: «&nbsp;il voulait pouvoir sortir de chez lui et être dans
  les bois en cinq minutes à pied. Une lisière de forêt, c'est le mot qu'il a employé.
  Il promène son labrador tous les matins à six heures et demie.&nbsp;»</div>
  <div class='say'>L'annonce dit&nbsp;: «&nbsp;Le fond du jardin donne directement sur le bois&nbsp;:
  le portillon ouvre sur les sentiers de la forêt de Fausses-Reposes.&nbsp;»</div>
  <div class='out'><b>Rappelez Jean Vasseur.</b> Le 12 allée des Cèdres à Vaucresson a un
  portillon qui ouvre sur la forêt de Fausses-Reposes. Il cherchait exactement ça en mars.
  Budget, maison, quatre chambres&nbsp;: tout colle.</div>
</div>

<p class='t'><b>Cent vingt-huit jours séparent le besoin du bien.</b> Aucun logiciel ne
vous aurait rappelé Jean, parce que «&nbsp;lisière de forêt&nbsp;» n'est pas une case à cocher.</p>

<h2>Et surtout, ce qu'il refuse de vous proposer</h2>
<div class='lead'>Un outil qui dit toujours oui ne sert à rien.</div>

<div class='case ko'>
  <div class='hh'><span>Jean Vasseur &middot; 17 avenue du Général Leclerc</span><span class='sc'>31/100 &middot; rejeté</span></div>
  <div class='say'>Maison, quatre chambres, 1&nbsp;180&nbsp;000&nbsp;&euro;. Dans son budget,
  dans son type de bien. <b>N'importe quel filtre le lui aurait proposé.</b></div>
  <div class='out'><b>Ne pas proposer à Jean Vasseur.</b> L'avenue passante contredit sa
  recherche de calme, et la rénovation complète est un rédhibitoire qu'il a formulé
  explicitement. Deux critères que le filtre ne voit pas.</div>
</div>

<p class='t'>Les quatre autres acquéreurs ont également trouvé leur bien&nbsp;: la famille
Ricci sur l'école à trois minutes à pied, les Delaunay sur les vingt minutes maximum
de la mère de madame, Sophie Marchand sur la lumière pour travailler, Madame Ouazana
sur l'absence de travaux votés. Quatorze critères humains captés au total, dont aucun
n'existe comme champ dans un logiciel métier.</p>

<div class='warn'>
  <b>En toute transparence sur cette démonstration</b>
  <p>Ces cinq acquéreurs et ces six biens sont fictifs, construits sur votre secteur
  réel. Je vous le dis parce que vous pourriez légitimement penser que j'ai écrit la
  question et la réponse. C'est exactement pour cela que la page suivante vous propose
  de le tester avec vos mots à vous, sur vos dossiers.</p>
</div>
"""


def page3():
    return """
<div class='brk'></div>
<h2>Mode d'emploi</h2>
<div class='lead'>Deux essais, dix minutes en tout, et vous saurez si ça marche.</div>

<p class='t'>Vous n'avez rien à installer et rien à apprendre. Vous dictez, je fais tourner
le robot, vous recevez le résultat. Voici les deux essais que je vous conseille, dans cet
ordre. Le second est le plus important.</p>

<div class='st'>
  <div class='num'>Essai 1 &middot; le test à l'aveugle</div>
  <h4>Vous savez la réponse, pas le robot</h4>
  <p>Prenez un acquéreur que vous connaissez bien et un bien de votre portefeuille dont
  vous savez qu'il lui correspond, pour une raison qui n'est écrite nulle part. Dictez-moi
  l'acquéreur sans jamais nommer le bien. Envoyez-moi le bien séparément. Si le robot fait
  le lien tout seul, et vous dit pourquoi, vous avez votre réponse.</p>
</div>

<div class='st'>
  <div class='num'>Essai 2 &middot; le piège</div>
  <h4>Essayez de le faire se tromper</h4>
  <p>Envoyez-moi un bien qui coche toutes les cases chiffrées de cet acquéreur, prix,
  surface, nombre de pièces, mais qui ne lui conviendrait jamais dans la vraie vie.
  Un outil sérieux doit le refuser et vous expliquer pourquoi. C'est ce test-là qui vous
  dira si vous pouvez lui faire confiance.</p>
</div>

<h2>Un exemple de ce que vous pouvez dicter</h2>
<p class='t'>Parlez comme vous parlez, le désordre n'est pas un problème. Voici la forme
que ça peut prendre&nbsp;:</p>

<div class='ex'><span class='g'>&#9654; Votre vocal, 50 secondes</span>

Alors j'ai vu Madame Lefevre ce matin. Budget huit cent cinquante
mille, elle veut un trois pieces. Ce qui compte pour elle c'est
qu'elle est infirmiere de nuit, donc elle dort la journee. Elle m'a
dit qu'elle ne supporterait pas une chambre sur rue. Il lui faut
aussi un ascenseur, sa mere de quatre-vingts ans vient tous les
dimanches. Le reste elle s'en arrange.

<span class='g'>&#9654; Ce que le robot en retient</span>

Critere humain 1 : chambre imperativement sur cour ou jardin
  Verbatim : "elle est infirmiere de nuit, elle dort la journee,
  elle ne supporterait pas une chambre sur rue"
Critere humain 2 : ascenseur indispensable
  Verbatim : "sa mere de quatre-vingts ans vient tous les dimanches"

<span class='g'>&#9654; Trois semaines plus tard, un mandat entre</span>

"Trois pieces de 68 m2, 839 000 EUR, deuxieme etage avec ascenseur,
les deux chambres donnent sur la cour interieure au calme."

<span class='g'>&#9654; Ce que vous recevez</span>

Rappelez Madame Lefevre. Les deux chambres donnent sur cour, elle
dort la journee. Ascenseur present pour sa mere. 839 000 EUR, dans
son budget.
</div>

<div class='punch'>
  <h3>Pourquoi votre logiciel métier ne peut pas faire ça</h3>
  <p>Agence Plus, votre outil de démarchage cadastre et vos entrants préqualifiés
  travaillent tous sur des champs&nbsp;: prix, surface, nombre de pièces, code postal.
  Ils font très bien ce pour quoi ils sont faits.</p>
  <p>Mais «&nbsp;lisière de forêt&nbsp;» n'est pas un champ. «&nbsp;Elle dort la journée&nbsp;»
  n'est pas un champ. «&nbsp;La belle-mère à moins de vingt minutes&nbsp;» n'est pas un champ.
  Ces informations vivent dans vos conversations, puis dans votre tête, et elles finissent
  par se perdre.</p>
  <p><b>Je ne remplace aucun de vos outils et je ne vous en ajoute pas un.
  J'ajoute une mémoire au-dessus de ceux que vous avez déjà.</b></p>
  <div class='sig'>Alexis Bendavid &middot; 06 80 55 18 36 &middot; alexis.bendavid@gmail.com</div>
</div>

<h2>Si les deux essais vous convainquent</h2>
<div class='lead'>Trois étapes, et vous n'avez toujours rien à installer.</div>

<div class='st'>
  <div class='num'>Étape 1 &middot; mise en route</div>
  <h4>Je branche vos mandats</h4>
  <p>Vos biens entrent dans le robot au fil de l'eau, dans le format qui vous arrange.
  Rien ne change dans Agence Plus, qui reste votre outil de transaction.</p>
</div>

<div class='st'>
  <div class='num'>Étape 2 &middot; au quotidien</div>
  <h4>Vous dictez, c'est tout</h4>
  <p>Soixante secondes après un rendez-vous, depuis votre téléphone, dans la voiture.
  Vous ne remplissez aucun formulaire et vous n'ouvrez aucun logiciel de plus.</p>
</div>

<div class='st'>
  <div class='num'>Étape 3 &middot; le retour</div>
  <h4>Vous recevez les rappels</h4>
  <p>Chaque mandat entrant est confronté à toute votre mémoire acquéreurs. Vous ne
  recevez que les correspondances qui méritent un appel, avec la raison et la preuve.
  Rien n'est jamais envoyé à un client sans vous.</p>
</div>

<p class='t'>Le premier mois sert à valider sur vos vrais dossiers, sans engagement de
votre part. Si la mémoire ne vous fait pas gagner un rendez-vous, elle ne vaut rien et
nous en restons là.</p>
"""


pied = ("<div class='pied'>Mémoire des acquéreurs &middot; préparé pour l'Agence RG &middot; "
        + date.today().strftime("%d/%m/%Y") + "</div>")

html = ("<html><head><meta charset='utf-8'><style>" + CSS + "</style></head><body>"
        + pied + page1() + page2() + page3() + "</body></html>")

HTML(string=html).write_pdf(SORTIE)
print("PDF genere : " + SORTIE)
