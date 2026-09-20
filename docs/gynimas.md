# Gyvo gynimo eiga

1. Atverti `results/final/index.html`. Paaiškinti skirtumą tarp CV, pagal kurį pasirinktas modelis, ir galutinio testo. Parodyti SVM laimėjimą pagal kainą bei beveik vienodą SVM ir logistinės regresijos AP.
2. Parodyti `src/evaluation.py` funkcijas `expected_cost` ir `choose_cost_threshold`. Rankomis patikrinti `(90 + 5*3)/200 = 0.525`.
3. Pakeisti slenkstį HTML valdiklyje iš 0,15 į 0,50. Paaiškinti, kad tai diagnostika; galutinio modelio taip neperrenkame.
4. Parodyti SVM kalibraciją `src/models.py`. Paaiškinti, kodėl transformacijos yra kalibratoriaus viduje. Arba paaiškinti fuzzy narystę: kai trukmė 27 mėnesiai, `(27-6)/(48-6) = 0.5`.
5. Dėstytojo CSV įrašyti į `examples/unseen.csv` su tais pačiais 20 stulpelių. Paleisti `python -m src.predict --input examples/unseen.csv --output results/unseen_predictions.csv`. Tikros baigties nereikia prognozei, bet jos reikia tikslumui vertinti.
6. Nedideliam pakeitimui nukopijuoti `config/experiment.yaml` į `config/defence.yaml`, nustatyti `false_negative: 2.0` ir paleisti `python -m src.main --config config/defence.yaml --quick --output results/defence`. Tai greitas naujos sąlygos demonstravimas, nelygintinas su pilnu 15 skaidymų bandymu kaip lygiavertis įrodymas.
7. Paaiškinti abliacijos rezultatą: mažesnė kaina nereiškia, kad pagerėjo visos metrikos. Parodyti, kad vienas mažas auditas neįrodo grupių teisingumo.

Prieš gynimą reikia pačiam suprasti kiekvieną žingsnį. Veikianti programa nepakeičia asmeninio paaiškinimo ir nematyto bandymo.
