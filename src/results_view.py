"""Sukuria savarankišką HTML rezultatų peržiūrą ir slenksčių diagnostiką."""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd

from .evaluation import metric_row


def create_results_view(output_dir, y_true, probabilities, threshold, fp_cost, fn_cost):
    directory = Path(output_dir)
    ledger = pd.DataFrame({"actual_bad": np.asarray(y_true, dtype=int),
                           "bad_probability": probabilities})
    ledger.to_csv(directory / "test_predictions.csv", index=False)
    rows = [metric_row(y_true, probabilities, float(t), fp_cost, fn_cost)
            for t in sorted(set([0.0, 0.5, 1.0, float(threshold)] + list(np.arange(1, 100) / 100)))]
    pd.DataFrame(rows).to_csv(directory / "threshold_diagnostics.csv", index=False)
    summary = pd.read_csv(directory / "model_summary.csv")
    metrics = json.loads((directory / "final_test_metrics.json").read_text(encoding="utf-8"))
    display = summary[["model", "balanced_accuracy_mean", "pr_auc_mean", "brier_score_mean", "expected_cost_mean"]].copy()
    display.columns = ["Metodas", "Balanced accuracy", "AP (PR)", "Brier", "Klaidų kaina"]
    tables = []
    for title, filename in [("Požymių abliacija", "sensitive_feature_ablation.csv"),
                            ("Trūkstamų reikšmių bandymas", "missing_value_robustness.csv"),
                            ("Grupių diagnostika", "fairness_audit.csv"),
                            ("Klaidų pavyzdžiai", "error_examples.csv")]:
        table = pd.read_csv(directory / filename).to_html(index=False, float_format=lambda x: f"{x:.3f}", border=0)
        tables.append(f"<h2>{title}</h2><div class='scroll'>{table}</div>")
    html = """<!doctype html><html lang="lt"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kredito rizikos eksperimento rezultatai</title>
<style>body{font:17px/1.55 system-ui,sans-serif;max-width:1100px;margin:40px auto;padding:0 24px;color:#182434;background:#f8fafc}h1{font-size:34px;line-height:1.2}h2{margin-top:42px}table{border-collapse:collapse;background:white;width:100%;font-size:14px}td,th{padding:10px;border:1px solid #d9dfe7;text-align:left}th{background:#e8eef6}.scroll{overflow:auto}img{max-width:100%;background:white}input{width:100%;accent-color:#2463ac}output{font-weight:700}#matrix{max-width:650px}a{color:#165aa3}.muted{color:#526274}</style>
<h1>Kredito paraiškų rizikos analizė</h1>
<p>Karolis Lapinskas · PEPfm-26 · Galutinio darbo eksperimentas</p>
<p>OpenML credit-g: 1 000 įrašų, 20 požymių. Plėtros dalis: 800 įrašų, 5 × 3 kartotinis stratifikacinis vertinimas. Galutinis testas: 200 įrašų.</p>
<h2>Modelių palyginimas plėtros dalyje</h2>TABLE
<p>Parinktas modelis: <strong>MODEL</strong>. Pasirinkimo kriterijus: mažiausia vidutinė CV klaidų kaina, kai FN kaina yra FN_COST, o FP kaina FP_COST.</p>
<img src="model_comparison.png" alt="Metodų vidutinės klaidų kainos ir AP palyginimas">
<h2>Galutinio testo rezultatai</h2><p>Balanced accuracy: BA · AP: APVAL · Brier: BRIER · Kaina: COST.</p>
<p>AP apskaičiuotas funkcija average_precision_score. Failų stulpelis pr_auc reiškia AP, o ne trapecinę PR kreivės integraciją.</p>
<h2>Kaip slenkstis keičia klaidas</h2>
<p>Slenkstis pasirinktas tik plėtros duomenyse: <strong>THRESHOLD</strong>. Žemiau esantis valdiklis rodo galutinio testo diagnostiką; pagal jį modelis ir slenkstis neperrenkami.</p>
<label for="threshold">Diagnostinis slenkstis <output id="value"></output></label>
<input id="threshold" type="range" min="0" max="1" step="0.01" value="THRESHOLD">
<p id="cost"></p><div id="matrix"></div>
<img src="calibration_final_test.png" alt="Prognozuotų tikimybių ir stebėtos blogos rizikos dalies palyginimas">
TABLES
<h2>Ribos</h2><p>Tai istorinių mokomųjų duomenų prototipas. Klaidos kaina pateikta sąlyginiais vienetais. Mažos grupės ir persidengiantys CV skaidymai neleidžia šio rezultato laikyti banko sistemos patvirtinimu ar statistinio pranašumo įrodymu.</p>
<p><a href="model_summary.csv">CV lentelė CSV</a> · <a href="final_test_metrics.json">Testo metrikos JSON</a> · <a href="threshold_diagnostics.csv">Slenksčių diagnostika CSV</a></p>
<script>const data=DATA;const slider=document.getElementById('threshold');function update(){const t=Number(slider.value);let tn=0,fp=0,fn=0,tp=0;for(const r of data){const bad=r.bad_probability>=t;if(r.actual_bad){if(bad)tp++;else fn++;}else{if(bad)fp++;else tn++;}}document.getElementById('value').textContent=t.toFixed(2);document.getElementById('cost').textContent='Klaidų kaina: '+((FP_COST*fp+FN_COST*fn)/data.length).toFixed(3)+' = ('+FP_COST+' × '+fp+' + '+FN_COST+' × '+fn+') / '+data.length;document.getElementById('matrix').innerHTML='<table><tr><th></th><th>Prognozė good</th><th>Prognozė bad</th></tr><tr><th>Tikra good</th><td>TN '+tn+'</td><td>FP '+fp+'</td></tr><tr><th>Tikra bad</th><td>FN '+fn+'</td><td>TP '+tp+'</td></tr></table>';}slider.addEventListener('input',update);update();</script></html>"""
    replacements = {
        "TABLES": "".join(tables), "TABLE": display.to_html(index=False, border=0, float_format=lambda x: f"{x:.3f}"),
        "MODEL": escape(metrics["selected_model"]), "BA": f"{metrics['balanced_accuracy']:.3f}",
        "APVAL": f"{metrics['pr_auc']:.3f}", "BRIER": f"{metrics['brier_score']:.3f}",
        "COST": f"{metrics['expected_cost']:.3f}", "THRESHOLD": f"{threshold:.2f}",
        "DATA": ledger.to_json(orient="records"), "FP_COST": str(fp_cost), "FN_COST": str(fn_cost),
    }
    # Pakeisti ilgiausius žymenis pirmiausia, kad COST nepakeistų FN_COST dalies.
    for token in sorted(replacements, key=len, reverse=True):
        html = html.replace(token, replacements[token])
    (directory / "index.html").write_text(html, encoding="utf-8")
