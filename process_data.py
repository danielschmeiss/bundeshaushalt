#!/usr/bin/env python3
"""Bundeshaushalt CSV -> JSON. Einmalig ausführen: python3 process_data.py"""
import csv, json, os

FILES = {
    2020: "hh_2020_utf8.csv",
    2021: "hh_2021_n2_utf8.csv",
    2022: "hh_2022_utf8.csv",
    2023: "HH_2023.csv",
    2024: "HH_2024_ALL.csv",
    2025: "HH_2025_ALL.csv",
    2026: "HH_2026_ALL.csv",
}

def col_map(header):
    m = {}
    for i, h in enumerate(header):
        k = h.strip().strip('"').strip().lower().replace('﻿', '')
        if k == 'einzelplan':           m['ep']  = i
        elif k == 'einzelplan-text':    m['ept'] = i
        elif k in ('einnahmen-ausgaben', 'einahmen-ausgaben'): m['ea'] = i
        elif k in ('einnahmen-ausgaben-art', 'einnahmen-ausgaben-text',
                   'einahmen-ausgaben-text'):                  m['art'] = i
        elif k == 'kapitel':            m['kap']  = i
        elif k == 'kapitel-text':       m['kapt'] = i
        elif k == 'titel':              m['tit'] = i
        elif k == 'titel-text':         m['txt'] = i
        elif k.startswith('soll'):      m['soll'] = i
    return m

def get(row, m, k):
    try:    return row[m[k]].strip().strip('"') if k in m else ''
    except: return ''

def parse_soll(s):
    s = s.strip().strip('"')
    try:    return int(float(s)) if s else 0
    except: return 0

os.makedirs('data', exist_ok=True)

# ── Einnahmen category mapping ────────────────────────────────────────────────
# Named top-line Titel tracked consistently across all years (text-keyword based)
TOP_TITEL = [
    ('Lohnsteuer',              'lohnsteuer'),
    ('Umsatzsteuer',            'umsatzsteuer'),
    ('Einfuhrumsatzsteuer',     'einfuhrumsatzsteuer'),
    ('Einkommensteuer',         'veranlagte einkommensteuer'),
    ('Körperschaftsteuer',      'körperschaftsteuer'),
    ('Kapitalertragsteuer',     'nicht veranlagte steuern vom ertrag'),
    ('Energiesteuer',           'energiesteuer'),
    ('Tabaksteuer',             'tabaksteuer'),
    ('Versicherungsteuer',      'versicherungsteuer'),
    ('Kfz-Steuer',              'kfz-steuer'),
    ('Solidaritätszuschlag',    'solidaritätszuschlag'),
    ('CO₂-Bepreisung',          'co2-bepreisung'),
    ('Kreditaufnahme Markt',    'einnahmen aus krediten vom kreditmarkt'),
    ('EU-Beitrag (BNE)',        'bne-eigenmittel'),
    ('Gewerbesteuerumlage',     'gewerbesteuerumlage'),
]

def einnahmen_kat(art, txt):
    t = txt.lower(); a = art.lower()
    if 'kreditmarkt' in t or ('kredit' in t and 'aufnahme' in t) or 'anleihe' in t: return 'Kreditaufnahme'
    if 'besondere finanzierungseinnahmen' in a:                return 'Kreditaufnahme'
    if 'bne-eigenmittel' in t:                                 return 'EU-Beitrag'
    if 'steuern und steuerähnliche' in a:                      return 'EU-Beitrag'
    if 'rrf' in t or 'recovery and resilience' in t:           return 'EU-Transfers'
    if 'sondervermögen' in t and 'zuweisungen' in t:           return 'Sondervermögen-Transfers'
    if 'gemeinschaftsteuern' in a:                             return 'Gemeinschaftsteuern'
    if 'bundessteuer' in a:                                    return 'Bundessteuern'
    if 'verwaltungseinnahmen' in a:                            return 'Verwaltungseinnahmen'
    if any(k in t for k in ['lohnsteuer','umsatzsteuer','einkommensteuer','körperschaftsteuer',
                             'einfuhrumsatz','solidaritäts','gewerbesteuer','kapitalertrag']):
        return 'Gemeinschaftsteuern'
    if any(k in t for k in ['energiesteuer','tabaksteuer','versicherungsteuer','kfz-steuer',
                             'alkohol','biersteuer','stromsteuer','co2']):
        return 'Bundessteuern'
    return 'Sonstige Einnahmen'

all_ep  = {}
summary = {}
titles  = []
detail  = {}   # ep → year → {byKap: {kap: {a,e,n}}, byArt: {art: {a,e}}}
# Einnahmen aggregation
ein_kat  = {}                 # kat  → year → total
ein_top  = {n: {} for n,_ in TOP_TITEL}  # name → year → total

for year, fname in sorted(FILES.items()):
    if not os.path.exists(fname):
        print(f"FEHLT: {fname}"); continue
    with open(fname, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.reader(f, delimiter=';', quotechar='"'))
    cm = col_map(rows[0]) if rows else {}
    yr = {'a': 0, 'e': 0, 'ep': {}}

    for row in rows[1:]:
        ep   = get(row, cm, 'ep')
        ept  = get(row, cm, 'ept')
        ea   = get(row, cm, 'ea').upper()
        kap  = get(row, cm, 'kap')
        if kap and len(kap) < 4:   # 2023 CSV omits EP prefix on Kapitel
            kap = ep + kap.zfill(2)
        kapt = get(row, cm, 'kapt')
        ti   = get(row, cm, 'tit')
        txt  = get(row, cm, 'txt')
        art  = get(row, cm, 'art')
        soll = parse_soll(get(row, cm, 'soll'))

        if not ep or ea not in ('A', 'E'): continue
        if ept: all_ep[ep] = ept
        if ep not in yr['ep']: yr['ep'][ep] = {'a': 0, 'e': 0}

        if ea == 'A':
            yr['a'] += soll; yr['ep'][ep]['a'] += soll
        else:
            yr['e'] += soll; yr['ep'][ep]['e'] += soll

        titles.append([year, ep, kap, ti, txt, ea, art, soll])

        # Einnahmen aggregation (include negatives so totals match summary)
        if ea == 'E' and soll != 0:
            kat = einnahmen_kat(art, txt)
            yr_str = str(year)
            if kat not in ein_kat: ein_kat[kat] = {}
            ein_kat[kat][yr_str] = ein_kat[kat].get(yr_str, 0) + soll
            # Top-Titel matching (positive only: gross receipt keywords)
            if soll > 0:
                tl = txt.lower()
                for name, keyword in TOP_TITEL:
                    if keyword in tl:
                        if yr_str not in ein_top[name]: ein_top[name][yr_str] = 0
                        ein_top[name][yr_str] += soll
                        break

        # Detail aggregation: by Kapitel and by Ausgabenart
        yr_str = str(year)
        if ep not in detail: detail[ep] = {}
        if yr_str not in detail[ep]: detail[ep][yr_str] = {'byKap': {}, 'byArt': {}}
        d = detail[ep][yr_str]
        if kap not in d['byKap']: d['byKap'][kap] = {'a': 0, 'e': 0, 'n': kapt}
        elif kapt and not d['byKap'][kap]['n']: d['byKap'][kap]['n'] = kapt
        if art not in d['byArt']: d['byArt'][art] = {'a': 0, 'e': 0}
        if ea == 'A':
            d['byKap'][kap]['a'] += soll; d['byArt'][art]['a'] += soll
        else:
            d['byKap'][kap]['e'] += soll; d['byArt'][art]['e'] += soll

    summary[year] = yr
    print(f"{year}: Ausgaben {yr['a']/1e6:8.1f} Mrd. | Einnahmen {yr['e']/1e6:8.1f} Mrd. EUR")

ministerien = [{'c': k, 'n': v} for k, v in sorted(all_ep.items())]

with open('data/summary.json', 'w', encoding='utf-8') as f:
    json.dump({'years': sorted(FILES.keys()), 'ministerien': ministerien,
               'summary': {str(k): v for k, v in summary.items()}},
              f, ensure_ascii=False, separators=(',', ':'))

with open('data/titles.json', 'w', encoding='utf-8') as f:
    json.dump(titles, f, ensure_ascii=False, separators=(',', ':'))

with open('data/detail.json', 'w', encoding='utf-8') as f:
    json.dump(detail, f, ensure_ascii=False, separators=(',', ':'))

ein_top_list = [{'name': name, **vals} for name, vals in ein_top.items()]
with open('data/einnahmen.json', 'w', encoding='utf-8') as f:
    json.dump({'years': sorted(FILES.keys()), 'byKat': ein_kat, 'topTitel': ein_top_list},
              f, ensure_ascii=False, separators=(',', ':'))

print(f"\ndata/summary.json:  {os.path.getsize('data/summary.json')/1024:.0f} KB")
print(f"data/einnahmen.json: {os.path.getsize('data/einnahmen.json')/1024:.0f} KB")
print(f"data/detail.json:   {os.path.getsize('data/detail.json')/1024:.0f} KB")
print(f"data/titles.json:  {os.path.getsize('data/titles.json')/1024/1024:.1f} MB")
print(f"Titel gesamt: {len(titles):,}")
print("\nJetzt starten: python3 -m http.server 8000  →  http://localhost:8000")
