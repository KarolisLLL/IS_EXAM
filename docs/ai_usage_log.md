# AI naudojimo žurnalas

## 2026-09-20 galutinės versijos patikra

Užklausa: perskaityti `PEPfm-26_Karolis_Lapinskas.docx`, užbaigti galutinį darbą, paleisti kodą ir parengti įkėlimą į `KarolisLLL/IS_EXAM`, padengiant kriterijus 1.1–4.3. Pradinis dokumentas iš tikrųjų perskaitytas, kai naudotojas atlaisvino failo užraktą.

Priimta: išsaugoti esamo projekto duomenų rinkinį ir metodus, pataisyti kalibravimo grandinę, įtraukti visada bad atskaitą, pridėti CSV prognozavimą, slenksčio diagnostiką ir HTML peržiūrą. Patikra: naujas pilnas 90 CV eilučių eksperimentas, išsaugotos metrikos ir prognozavimo pavyzdžiai. Šio paleidimo įrodymai yra `results/final/`, o ankstesnės versijos `outputs/` į pateikiamą saugyklą neįtrauktos.

Aptiktos ir pataisytos AI parengtos ankstesnės versijos klaidos arba nepatikrintos prielaidos:

1. SVM transformacijos buvo mokomos prieš kalibratoriaus vidinį skaidymą. Pataisyta: `CalibratedClassifierCV` apgaubia visą `Pipeline`. Taip kalibravimo validavimo dalis neįtraukiama į transformacijų mokymą. Patikrinta pagal oficialią scikit-learn dokumentaciją, `tests/test_calibration.py` ir pilną paleidimą.
2. Vien daugumos klasės kaina 1,5 sudarė pernelyg silpną ekonominę atskaitą: esant 5:1 kainai visada bad taisyklė pasiekia 0,7. Pridėta `reject_all` atskaita ir patikrintas jos rezultatas visuose 15 skaidymų. Prielaida, kad 70 % bendras tikslumas reiškia gerą sprendimą, atmesta.
3. Stulpelis `pr_auc` iš tikrųjų skaičiuojamas `average_precision_score`, o ne trapeciniu integralu. Išlaikytas failų suderinamumas, bet ataskaitoje ir HTML aiškiai nurodyta AP formulė. Šios dvi metrikos nevadinamos visiškai tapačiomis.
4. Senoje ataskaitoje įrašyti skaičiai negali būti automatiškai laikomi naujo paleidimo rezultatais. Galutinė ataskaita sutikrinta su `results/final/model_summary.csv`; ankstesni teiginiai apie beveik vienodą CV kainą nepersikelia į naują lentelę.

Atmesta: teigti statistiškai įrodytą SVM pranašumą iš persidengiančių CV skaidymų; teigti, kad rankinis fuzzy balas yra kalibruota tikimybė; laikyti 5:1 tikrais banko nuostoliais. Šaltiniai patikrinti per leidėjų DOI puslapius, UCI, myFICO ir oficialią scikit-learn dokumentaciją. Studentui dar reikia pačiam atlikti gyvo gynimo veiksmus.

Toliau išsaugotas ankstesnės projekto versijos žurnalas kaip istorija; jo failų keliai ir skaičiai nepriskiriami naujam eksperimentui.

Vien AI atsakymas nėra rezultato ar šaltinio įrodymas. Žurnalas fiksuoja tikrintas užklausas ir sprendimus, panaudotus šiame projekte.

| Data | Užklausa arba užduotis | Ką pasiūlė AI | Priimta ar atmesta | Kaip patikrinta |
|---|---|---|---|---|
| 2026-09-15 | Sukurti atkuriamą kredito rizikos klasifikavimo projektą | Duomenų gavimą iš OpenML, vienodą modelių vertinimo grandinę ir rezultatų failus | Priimta | Paleistas pilnas eksperimentas; `outputs/data_manifest.json` patvirtina ID 31, 1 000 eilučių ir SHA-256 kontrolinę sumą. |
| 2026-09-15 | Parinkti ir palyginti bazinį bei intelektualiuosius metodus | Daugumos klasę, loginę regresiją, SVM, MLP ir aiškinamą fuzzy taisyklių sistemą | Priimta | Visi metodai vertinti tais pačiais 15 išorinių kartotinio stratifikacinio CV skaidymų; rezultatai `outputs/model_summary.csv`. |
| 2026-09-15 | Papildyti galutinio egzamino įrodymus | Abliaciją be `age` ir `personal_status`, trūkstamų reikšmių testą ir klaidų pavyzdžius | Priimta | Vykdyti 7 vienetiniai testai ir pilnas eksperimentas; sukurti atitinkami CSV failai `outputs/`. |

## Aptiktos klaidos arba nepatikrintos prielaidos

1. Pradinis SVM variantas naudojo `SVC(probability=True)`, kuri dabartinėje scikit-learn versijoje generavo įspėjimą. Pasiūlymas nekritiškai palikti šį variantą atmestas. Pakeista į `CalibratedClassifierCV(SVC(...), method="sigmoid")`; patikrinta pagal oficialią scikit-learn dokumentaciją ir pakartotinai paleidus testus be įspėjimo.
2. Klaidų kainų santykis 5:1 iš pradžių galėjo būti suprastas kaip reali banko politika. Tai nepatikrinta demonstracinė prielaida, todėl ji palikta tik `config/experiment.yaml`, aiškiai pažymėta ataskaitoje ir neinterpretuojama kaip tikras finansinis nuostolis.
