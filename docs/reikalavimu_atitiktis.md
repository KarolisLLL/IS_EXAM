# Reikalavimų atitiktis

Vertinimo įrodymai nurodyti pagal galutinę ataskaitą `docs/galutinis_darbas.md` ir 2026-09-20 pilną paleidimą `results/final/`.

| Kriterijus | Ataskaitos vieta | Įgyvendinimo arba patikros įrodymas |
|---|---|---|
| 1.1 Problemos neaiškumai | 1.1 | Maža imtis, kainų neapibrėžtumas, kalibracija, grupės, FICO pavyzdys |
| 1.2 Išskaidymas | 1.2 | Šeši etapai ir patikrinami rezultatai |
| 1.3 Suprantamos užduotys | 1.3 | Prasmė vadovui, finansininkui, vadybininkui ir darbuotojų mokymui |
| 2.1 Nuo 2 iki 4 metodų | 2 | Logistinė regresija, SVM, MLP, fuzzy ir pastovūs baseline |
| 2.2 Argumentai ir šaltiniai | 2 ir literatūra | Pirminiai straipsniai su DOI, atskirtas teorinis ir empirinis pagrindimas |
| 3.1 Pasirinktas sprendimas | 3.1 ir 3.2 | SVM pagal mažiausią CV kainą; `model_summary.csv` |
| 3.2 Privalumai prieš alternatyvas | 3.2 | Skaitinis ir savybių palyginimas, kompromisai ir išvadų ribos |
| 4.1 Įvestis ir išvestis | 4.1 | `examples/applications.csv`, `src/predict.py`, `results/predictions.csv` |
| 4.2 Veiksmų seka | 4.2 | 11 žingsnių algoritmas, įgyvendintas `src/main.py` |
| 4.3 Formulės ir kintamieji | 4.3 | Standartizavimas, RBF SVM, kalibracija, slenkstis, fuzzy, metrikos ir funkcijų pavadinimai |

## Pradinio DOCX galutinio egzamino reikalavimai

| Reikalavimas | Įrodymas |
|---|---|
| Baseline ir duomenų grandinė | `src/data.py`, `src/preprocess.py`, `src/models.py` |
| Bent du intelektualieji metodai | Mokomi SVM ir MLP; papildomas fuzzy |
| Vienodas kartotinis stratifikacinis vertinimas | 15 bendrų skaidymų, 6 metodai, 90 eilučių `outer_fold_results.csv` |
| Galutinis testas nenaudojamas parinkimui | `src/main.py` išrenka modelį iš CV suvestinės |
| Abliacija | `sensitive_feature_ablation.csv` |
| Atsparumo bandymas | `missing_value_robustness.csv` |
| Lentelė, grafikas, klaidų pavyzdžiai | `model_summary.csv`, `model_comparison.png`, `error_examples.csv` |
| Kalibracija ir grupių ribos | `calibration_final_test.png`, `fairness_audit.csv` |
| Kaštų ir slenksčio poveikis | `threshold_diagnostics.csv`, interaktyvus `index.html` |
| Paleidimas ir priklausomybės | `README.md`, `requirements.txt`, `run_manifest.json` |
| AI auditas ir dvi klaidos | `docs/ai_usage_log.md` |
| Nematytas bandymas ir pakeitimas | `src/predict.py`, `docs/gynimas.md`; gyvai atlieka studentas |

Ši lentelė parodo pateiktus įrodymus, bet nėra dėstytojo įvertinimas ar pažymio garantija.
