# Kredito paraiškų rizikos klasifikavimas

Karolis Lapinskas · PEPfm-26 · Intelektualiosios sistemos

Veikiantis galutinio egzamino projektas pagal OpenML `credit-g` (ID 31). Palygina daugumos klasę, visada `bad` taisyklę, logistinę regresiją, SVM, MLP ir fuzzy tipo modelį. Teigiama klasė: `bad = 1`.

## Darbas ir rezultatai

- [Išsami Word ataskaita](docs/Karolis_Lapinskas_Galutinio_darbo_ataskaita.docx)
- [Galutinė ataskaita Markdown formatu](docs/galutinis_darbas.md)
- [Vertinimo kriterijų 1.1–4.3 ir egzamino reikalavimų atitiktis](docs/reikalavimu_atitiktis.md)
- [Rezultatų peržiūra](results/final/index.html) – atsisiuntus projektą atverti naršyklėje; GitHub failo rodinys HTML nevykdo.
- [Pilno bandymo lentelė](results/final/model_summary.csv)
- [AI naudojimo žurnalas](docs/ai_usage_log.md)
- [Gynimo eiga](docs/gynimas.md)

![Modelių palyginimas](results/final/model_comparison.png)

2026-09-20 paleidime mažiausią 15 išorinių CV skaidymų vidutinę klaidų kainą pasiekė **SVM: 0,558**. Galutiniame 200 įrašų teste: BA 0,654, AP 0,678, Brier 0,153, kaina 0,525. Slenkstis 0,15; TN 50, FP 90, FN 3, TP 57. Aptikta 95 % blogos rizikos atvejų, bet atmesta 64,3 % geros rizikos atvejų. Tai mokomasis prototipas, o ne banko sistemos patvirtinimas.

## Diegimas

Rekomenduojamas Python 3.12. Iš projekto šaknies Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\Activate.ps1
```

Jei aktyvinimą riboja PowerShell politika, vietoje `python` naudokite `.\.venv\Scripts\python.exe`. Linux ir macOS: `python3 -m venv .venv`, `source .venv/bin/activate`, `python -m pip install -r requirements.txt`.

## Viena pagrindinio eksperimento komanda

```powershell
python -m src.main --config config/experiment.yaml
```

Pirmą kartą reikia interneto viešiems OpenML duomenims gauti. Komanda paruošia duomenis, atlieka 15 bendrų CV skaidymų, išrenka modelį, patikrina galutinį testą, atlieka abliaciją ir atsparumo bandymą bei sukuria CSV, grafikus, HTML ir modelį `results/final/`. Modelio failas į Git neįtraukiamas; jį sukuria ši komanda. Duomenų kopijų pateikti nereikia: [OpenML ID 31](https://www.openml.org/d/31). Šaltinio manifestas su SHA-256 leidžia tikrinti gautą rinkinį.

Trumpas techninis visos grandinės patikrinimas (rašo į atskirą katalogą):

```powershell
python -m src.main --config config/experiment.yaml --quick
```

`--models logistic,svm` leidžia pasirinkti metodus, `--output results/other` – atskirą išvestį. Galutinės ataskaitos rezultatai gauti pilnu režimu, o ne su `--quick`.

## Pamatyti rezultatus

Atverkite `results/final/index.html` naršyklėje arba paleiskite vietinį serverį:

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

Tada atverkite [vietinę suvestinę](http://127.0.0.1:8000/results/final/index.html). Slenksčio valdiklis perskaičiuoja galutinio testo klaidų matricą ir kainą. Tai diagnostika, pagal kurią modelis neperrenkamas.

## Naujų paraiškų prognozė

Po pagrindinio eksperimento:

```powershell
python -m src.predict --input examples/applications.csv --output results/predictions.csv
```

Įvesties CSV turi turėti visus 20 pavyzdyje esančių stulpelių; tikslinės klasės nereikia. Trūkstamas reikšmes užpildo modelio transformacijos. Išvestis: eilutės numeris, `bad_probability`, `threshold`, `predicted_class`. Pateikti du įrašai sukurti demonstracijai ir neturi tikrų baigčių. Naudokite tik patikimą savo sugeneruotą `joblib` failą.

## Eksperimento taisyklės

- 1 000 įrašų, 20 požymių, 700 `good` ir 300 `bad`; 80/20 stratifikuotas plėtros ir testo skaidymas.
- Sėkla 2026; išorinis 5 × 3 kartotinis stratifikacinis CV; vidinis 3 dalių CV ir 5 parametrų bandiniai.
- Transformacijos mokomos tik mokymo dalyse, SVM atveju ir kalibravimo skaidymuose.
- Parametrų atranka pagal AP; slenksčio ir modelio šeimos atranka pagal kainą `C=(FP+5*FN)/n`.
- `pr_auc` stulpelis reiškia `average_precision_score` (AP), ne trapecinį integralą.
- Galutinis testas nenaudojamas modelio, parametrų ar slenksčio atrankai. Abliacija ir slenksčio valdiklis yra diagnostika.

## Svarbiausi failai

| Failas | Paskirtis |
|---|---|
| `src/main.py` | Visa eksperimento seka |
| `src/data.py`, `src/preprocess.py` | Duomenų patikra, skaidymas ir transformacijos |
| `src/models.py`, `src/fuzzy.py` | Metodai, parametrų erdvės, fuzzy formulė |
| `src/evaluation.py` | Kaštai, slenkstis, CV ir metrikos |
| `src/predict.py` | Naujo CSV prognozavimas |
| `results/final/run_manifest.json` | Tikslios paketų versijos ir nustatymai |
| `results/final/outer_fold_results.csv` | Visos 90 CV rezultatų eilučių |
| `results/final/sensitive_feature_ablation.csv` | Bandymas be amžiaus ir asmeninės būsenos |
| `results/final/missing_value_robustness.csv` | 5 % ir 10 % atsitiktinio maskavimo bandymai |
| `results/final/fairness_audit.csv` | Mažų grupių diagnostika |
| `results/final/error_examples.csv` | Konkretūs klaidingų prognozių pavyzdžiai |

## Testai

```powershell
python -m pytest -q
```

GitHub Actions paleidžia tuos pačius testus. Pilnas eksperimentas CI automatiškai nevykdomas. Istoriniai duomenys, mažos grupės, ribota parametrų paieška ir demonstraciniai kaštai riboja rezultatų pritaikymą. Išsami interpretacija pateikta ataskaitoje.

