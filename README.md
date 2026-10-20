# Kauno vietovių atlasas

Kaip gyvena kiekviena Kauno seniūnija ir rinkimų apylinkė: darželiai ir mokyklos, sveikatos priežiūra, žaluma, renovacija – vienam gyventojui.

**Atlasas:** atidarykite `index.html` naršyklėje arba šios repozitorijos GitHub Pages puslapį. Tai vienas savarankiškas failas – visi duomenys jame, serverio nereikia.

Atlasą parengė koalicija „Kaunas gali geriau“ (Laisvės partija ir Lietuvos žaliųjų partija) iš viešų duomenų. Duomenis teikiančios institucijos atlaso nerengė ir jo nevertina. Tai nėra oficiali statistika.

## Kas čia yra

```
index.html              atlasas – vienas failas su įdėtais duomenimis
v2/index.html           atlaso puslapio šaltinis (duomenys – v2/data/)
v2/data/                žemėlapio ribos (GeoJSON) ir rodiklių reikšmės, kurias naudoja puslapis
data/processed/         apdoroti duomenys: rodikliai seniūnijoms ir apylinkėms (CSV), įstaigų sąrašai
scripts/                skriptai, kurie atsisiunčia pirminius duomenis ir juos apdoroja
```

Pirminiai duomenys (`data/raw/`, ~200 MB) į repozitoriją nededami – juos atsisiunčia `scripts/*_fetch_*.py`.

## Kaip atkurti

Reikia Python 3 su `shapely`, `pyproj` ir `pyshp` (`pip install shapely pyproj pyshp`).

```
python3 scripts/14_fetch_geografija.py      # ribos, gyventojų gardelė, rinkimų apylinkės
python3 scripts/15_geografija_kaunas.py
python3 scripts/16_fetch_osm_rodikliai.py   # OpenStreetMap objektai
python3 scripts/12_fetch_apva_renovacija.py # APVA renovacijos žemėlapis
python3 scripts/17_rodikliai_ribose.py      # objektai → seniūnijos ir apylinkės, vienam gyventojui
python3 scripts/18_v2_eksportas.py
python3 scripts/22_v2_build_data.py         # → v2/data/
python3 scripts/23_v2_standalone.py         # → vienas failas v2/dist/atlasas.html
```

Mokyklų ir darželių sąrašas (`data/processed/education_facilities.csv`) gaunamas skriptais `03`–`05`, socialinių paslaugų vietos – `04`.

## Svarbu skaitant duomenis

- Rodikliai rodo paslaugų ir infrastruktūros **pasiūlą** – ne jų kokybę ir ne tai, ar yra laisvų vietų.
- Žmonės naudojasi paslaugomis ir už savo teritorijos ribų, ypač prie ribų ir miesto centre.
- Gyventojų skaičius – 2021 m. surašymo 100 m gardelė, paskirstyta pagal ribas. Naujuose kvartaluose gyventojų nuo to laiko gali būti daugiau.
- Rinkimų apylinkės – 2024 m. Seimo rinkimų ribos; 2027 m. savivaldybių tarybų rinkimų apylinkės dar nepaskelbtos.
- OpenStreetMap duomenys ne visur išsamūs; kultūros vietų rodiklis dėl to kol kas nerodomas.

## Šaltiniai ir licencijos

| Duomenys | Šaltinis | Licencija |
|---|---|---|
| Žemėlapio objektai (sveikata, žaluma, sportas, takai, žaidimų aikštelės) | © OpenStreetMap bendraautoriai | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/) |
| Seniūnijų ribos | Registrų centras, Adresų registras | CC BY 4.0 |
| Rinkimų apylinkių ribos ir rinkėjų skaičius | Vyriausioji rinkimų komisija | – |
| Gyventojai pagal 100 m gardelę (2021 m. surašymas) | Valstybės duomenų agentūra | – |
| Renovuoti daugiabučiai | Aplinkos projektų valdymo agentūra (APVA), „Lietuvos renovacijos žemėlapis“ | – |
| Švietimo įstaigos | Švietimo ir mokslo institucijų registras (ŠMIR) | – |

Duomenų bazės, išvestos iš OpenStreetMap (`data/processed/`, `v2/data/`), platinamos pagal ODbL 1.0.
