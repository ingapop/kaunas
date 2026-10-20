"""
Export stage-2 indicators in the shape the v2 site loads (coordinator's spec, 2026-10-19):
  data/processed/v2_rodikliai.json
    { sugeneruota, rodikliai: [ {id, pavadinimas, vienetas, aprasymas, kryptis, saltinis, data,
      faktai, skaitiklis, vardiklis, slenkstis} ],
      reiksmes: { seniunijos: {id: {rodiklis: {reiksme, kiekis}}}, apylinkes: {...} },
      miestas: {rodiklis: {reiksme, kiekis}} }

Reads data/processed/geo/rodikliai_{seniunijos,apylinkes}.csv (script 17).

Publication thresholds (reiksme = null, kiekis kept):
  MIN_GYV       per-resident rates and green m2/resident: 2021 population < 1 500
  MIN_VAIKU     per-child rates: 2021 residents aged 0-14 < 250
  MIN_RENO      renovation shares: APVA denominator (finished + in progress + potential) < 20
  MIN_GATVIU_KM footway / street ratio: < 2 km of mapped streets
Undefined values (division by zero) are null as well.
"""
import csv
import datetime
import json
import os

GEO = "data/processed/geo"
OUT = "data/processed/v2_rodikliai.json"
MIN_GYV, MIN_VAIKU, MIN_RENO, MIN_GATVIU_KM = 1500, 250, 20, 2.0

OSM_DATE = "OpenStreetMap duomenų būklė 2026-10-19"
CENSUS = "2021 m. gyventojų ir būstų surašymas, 100 m gardelė (Valstybės duomenų agentūra)"
RODIKLIAI = [
    dict(id="vaikai", pavadinimas="Darželiai ir mokyklos", vienetas="įstaigų 1 000 vaikų (0–14 m.)",
         aprasymas="Kiek ikimokyklinį ugdymą teikiančių įstaigų ir bendrojo ugdymo mokyklų tenka 1 000 vaikų (0–14 m.).",
         kryptis="daugiau", saltinis=f"Švietimo ir mokslo institucijų registras (ŠMIR); {CENSUS}", data="ŠMIR 2022-08-30; gyventojai 2021-01-01",
         faktai="F-069", skaitiklis="skirtingos ikimokyklinio ugdymo įstaigos ir bendrojo ugdymo mokyklos (F-064 taisyklė)",
         vardiklis="0–14 m. gyventojai, 2021", slenkstis=f"vaikų < {MIN_VAIKU}",
         col_n="vaikai_istaigos", col_r="vaikai_istaigos_1000_vaiku", den="vaik"),
    dict(id="sveikata", pavadinimas="Sveikatos įstaigos ir vaistinės", vienetas="objektų 10 000 gyventojų",
         aprasymas="Kiek OpenStreetMap pažymėtų sveikatos priežiūros įstaigų ir vaistinių tenka 10 000 gyventojų.",
         kryptis="daugiau", saltinis=f"OpenStreetMap; {CENSUS}", data=OSM_DATE, faktai="F-070",
         skaitiklis="klinikos, ligoninės, gydytojų kabinetai, odontologijos ir kitos healthcare=* vietos, vaistinės",
         vardiklis="gyventojai, 2021", slenkstis=f"gyventojų < {MIN_GYV}",
         col_n=("sveikatos_istaigos", "vaistines"), col_r="sveikata_10000_gyv", den="gyv"),
    dict(id="socialines_paslaugos", pavadinimas="Socialinių paslaugų vietos", vienetas="vietų skaičius",
         aprasymas="Kiek Kauno miesto socialinių paslaugų centro padalinių ir paslaugų vietų yra teritorijoje. Dalis jų aptarnauja visą miestą.",
         kryptis="kontekstas", saltinis="kaunospc.lt kontaktai (adresai patikrinti 2026-10-19)",
         data="adresai 2026-09-14, patikrinta 2026-10-19", faktai="F-071",
         skaitiklis="15 paslaugų vietų (14 tebėra kaunospc.lt kontaktuose)", vardiklis="nėra (kiekis)",
         slenkstis="netaikoma", col_n="socialiniu_paslaugu_taskai", col_r=None, den=None),
    dict(id="zalieji_plotai", pavadinimas="Žalieji plotai", vienetas="m² vienam gyventojui",
         aprasymas="Kiek parkų, miškų, pievų ir kitų žaliųjų plotų tenka vienam gyventojui (persidengiantys plotai skaičiuojami vieną kartą).",
         kryptis="daugiau", saltinis=f"OpenStreetMap; {CENSUS}", data=OSM_DATE, faktai="F-072",
         skaitiklis="žaliųjų plotų sąjunga, apkirpta pagal ribas (ha)", vardiklis="gyventojai, 2021",
         slenkstis=f"gyventojų < {MIN_GYV}", col_n="zaluma_ha", col_r="zaluma_m2_gyv", den="gyv"),
    dict(id="zalieji_plotai_dalis", pavadinimas="Žaliųjų plotų dalis", vienetas="proc. teritorijos",
         aprasymas="Kokią teritorijos dalį užima žalieji plotai.",
         kryptis="daugiau", saltinis="OpenStreetMap; Registrų centras / VRK ribos", data=OSM_DATE, faktai="F-072",
         skaitiklis="žaliųjų plotų sąjunga (ha)", vardiklis="teritorijos plotas", slenkstis="netaikoma",
         col_n="zaluma_ha", col_r="zaluma_ploto_dalis_proc", den=None),
    dict(id="pesciuju_takai", pavadinimas="Pėsčiųjų ir dviračių takai", vienetas="takų km vienam gatvių km",
         aprasymas="Kiek kilometrų atskirai pažymėtų pėsčiųjų ir dviračių takų tenka vienam vietinių gatvių kilometrui.",
         kryptis="daugiau", saltinis="OpenStreetMap", data=OSM_DATE, faktai="F-073",
         skaitiklis="footway, path, pedestrian, living_street, cycleway (km)",
         vardiklis="residential, service, tertiary, unclassified gatvės (km)",
         slenkstis=f"gatvių < {MIN_GATVIU_KM:g} km", col_n="pesciuju_km", col_r="pesciuju_gatviu_santykis", den="gatv"),
    dict(id="renovacija", pavadinimas="Renovuoti daugiabučiai", vienetas="proc. APVA atrinktų daugiabučių",
         aprasymas="Kokia dalis daugiabučių, kuriuos Aplinkos projektų valdymo agentūra (APVA) laiko galinčiais dalyvauti atnaujinimo programose, jau renovuota.",
         kryptis="daugiau", saltinis="APVA „Lietuvos renovacijos žemėlapis“", data="2026-10-19", faktai="F-074",
         skaitiklis="baigti renovacijos projektai", vardiklis="baigti + vykdomi + potencialūs (APVA)",
         slenkstis=f"vardiklis < {MIN_RENO}", col_n="reno_baigta", col_r="reno_baigta_proc", den="reno"),
    dict(id="renovacija_pradeta", pavadinimas="Renovuoti ir renovuojami daugiabučiai",
         vienetas="proc. APVA atrinktų daugiabučių",
         aprasymas="Kokia dalis APVA atrinktų daugiabučių jau renovuota arba turi suderintą investicijų planą.",
         kryptis="daugiau", saltinis="APVA „Lietuvos renovacijos žemėlapis“", data="2026-10-19", faktai="F-074",
         skaitiklis="baigti ir vykdomi projektai", vardiklis="baigti + vykdomi + potencialūs (APVA)",
         slenkstis=f"vardiklis < {MIN_RENO}", col_n=("reno_baigta", "reno_vykdoma"),
         col_r="reno_baigta_vykdoma_proc", den="reno"),
    dict(id="kultura", pavadinimas="Kultūros vietos", vienetas="vietų 10 000 gyventojų",
         aprasymas="Kiek OpenStreetMap pažymėtų bibliotekų, muziejų, teatrų, kino teatrų ir kultūros centrų tenka 10 000 gyventojų.",
         kryptis="daugiau", saltinis=f"OpenStreetMap; {CENSUS}", data=OSM_DATE, faktai="F-075",
         skaitiklis="amenity=library|theatre|arts_centre|community_centre|cinema, tourism=museum",
         vardiklis="gyventojai, 2021", slenkstis=f"gyventojų < {MIN_GYV}",
         col_n=("bibliotekos", "muziejai", "kulturos_centrai_teatrai_kinai"), col_r="kultura_10000_gyv", den="gyv"),
    dict(id="sportas", pavadinimas="Sporto vietos", vienetas="vietų 10 000 gyventojų",
         aprasymas="Kiek OpenStreetMap pažymėtų viešai prieinamų sporto centrų, salių, stadionų ir lauko aikštynų tenka 10 000 gyventojų.",
         kryptis="daugiau", saltinis=f"OpenStreetMap; {CENSUS}", data=OSM_DATE, faktai="F-076",
         skaitiklis="leisure=sports_centre|sports_hall|stadium|pitch|track|fitness_station (be access=private|customers)",
         vardiklis="gyventojai, 2021", slenkstis=f"gyventojų < {MIN_GYV}",
         col_n=("sporto_centrai", "lauko_aikstynai"), col_r="sportas_10000_gyv", den="gyv"),
    dict(id="zaidimu_aiksteles", pavadinimas="Vaikų žaidimų aikštelės", vienetas="aikštelių 1 000 vaikų (0–14 m.)",
         aprasymas="Kiek OpenStreetMap pažymėtų viešų vaikų žaidimų aikštelių tenka 1 000 vaikų (0–14 m.).",
         kryptis="daugiau", saltinis=f"OpenStreetMap; {CENSUS}", data=OSM_DATE, faktai="F-077",
         skaitiklis="leisure=playground (be access=private|customers)", vardiklis="0–14 m. gyventojai, 2021",
         slenkstis=f"vaikų < {MIN_VAIKU}", col_n="zaidimu_aikst", col_r="zaidimu_aikst_1000_vaiku", den="vaik"),
    dict(id="vaiku_dalis", pavadinimas="Vaikų dalis", vienetas="proc. gyventojų",
         aprasymas="Kokią gyventojų dalį 2021 m. sudarė 0–14 metų vaikai.",
         kryptis="kontekstas", saltinis=CENSUS, data="2021-01-01", faktai="F-067",
         skaitiklis="0–14 m. gyventojai", vardiklis="visi gyventojai", slenkstis=f"gyventojų < {MIN_GYV}",
         col_n="gyv_0_14_2021", col_r="_vaiku_dalis", den="gyv"),
    dict(id="senjoru_dalis", pavadinimas="Vyresnio amžiaus gyventojų dalis", vienetas="proc. gyventojų",
         aprasymas="Kokią gyventojų dalį 2021 m. sudarė 65 metų ir vyresni žmonės.",
         kryptis="kontekstas", saltinis=CENSUS, data="2021-01-01", faktai="F-067",
         skaitiklis="65+ m. gyventojai", vardiklis="visi gyventojai", slenkstis=f"gyventojų < {MIN_GYV}",
         col_n="gyv_65_plius_2021", col_r="_senjoru_dalis", den="gyv"),
]


def num(v):
    if v in ("", None):
        return None
    f = float(v)
    return int(f) if f.is_integer() else f


def value(row, r, is_city):
    cn = r["col_n"]
    kiekis = sum(num(row[c]) or 0 for c in cn) if isinstance(cn, tuple) else num(row[cn])
    if isinstance(kiekis, float):
        kiekis = round(kiekis, 1)
    gyv, vaik = num(row["gyventojai_2021"]), num(row["gyv_0_14_2021"])
    if r["col_r"] is None:
        reiksme = kiekis
    elif r["col_r"] == "_vaiku_dalis":
        reiksme = round(100 * vaik / gyv, 1) if gyv else None
    elif r["col_r"] == "_senjoru_dalis":
        reiksme = round(100 * num(row["gyv_65_plius_2021"]) / gyv, 1) if gyv else None
    else:
        reiksme = num(row[r["col_r"]])
    if not is_city:
        den = r["den"]
        if (den == "gyv" and (gyv or 0) < MIN_GYV) or (den == "vaik" and (vaik or 0) < MIN_VAIKU) \
                or (den == "reno" and (num(row["reno_vardiklis"]) or 0) < MIN_RENO) \
                or (den == "gatv" and (num(row["gatviu_km"]) or 0) < MIN_GATVIU_KM):
            reiksme = None
    return {"reiksme": reiksme, "kiekis": kiekis}


def main():
    out = {"sugeneruota": datetime.date.today().isoformat(),
           "slenksciai": {"min_gyventoju": MIN_GYV, "min_vaiku_0_14": MIN_VAIKU,
                          "min_reno_vardiklis": MIN_RENO, "min_gatviu_km": MIN_GATVIU_KM},
           "rodikliai": [{k: v for k, v in r.items() if k not in ("col_n", "col_r", "den")} for r in RODIKLIAI],
           "reiksmes": {}, "miestas": {}}
    nulls = {}
    for lvl in ("seniunijos", "apylinkes"):
        with open(os.path.join(GEO, f"rodikliai_{lvl}.csv"), encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        out["reiksmes"][lvl] = {}
        for row in rows:
            if row["id"] == "miestas":
                if lvl == "seniunijos":
                    out["miestas"] = {r["id"]: value(row, r, True) for r in RODIKLIAI}
                continue
            out["reiksmes"][lvl][row["id"]] = {r["id"]: value(row, r, False) for r in RODIKLIAI}
        nulls[lvl] = {r["id"]: sum(1 for v in out["reiksmes"][lvl].values() if v[r["id"]]["reiksme"] is None)
                      for r in RODIKLIAI}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"Saved -> {OUT}")
    print("null values per indicator:", json.dumps(nulls, ensure_ascii=False))
    print("city:", json.dumps(out["miestas"], ensure_ascii=False))


if __name__ == "__main__":
    main()
