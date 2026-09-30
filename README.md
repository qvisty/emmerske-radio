# Emmerske Efterskole i radioen

Præsentationsside for radioprogrammet **Nadim og det flyvende tæppe** (Radio Globus), der blev sendt direkte fra Emmerske Efterskole ved Tønder op til Efterskolernes Dag.

**Siden:** https://qvisty.github.io/emmerske-radio/

## Indhold
- Afspiller med bølgeform, kapitelmarkører, hastighed, delbare tidspunkter (`#t=sekunder`) og "læs med"-tekst
- 17 kapitler – afspil direkte
- Stemmerne, citater med afspilning, fuld søgbar transskription der følger lyden
- Slides ("Trivslens arkitektur") og infografikker med zoom
- Læsevenlig visning (større tekst og mere luft) samt lyst/mørkt tema

## Opdatering af data
`assets/data.js` genereres fra kapitelmærkerne i MP3'en og SRT-filen:

```
pip install mutagen miniaudio
python tools/build_data.py
```

Titler, beskrivelser, medvirkende og citater redigeres øverst i `tools/build_data.py`.

`EMMERSKE EFTERSKOLE.mp3` (den uredigerede optagelse, 161 MB) er udeladt via `.gitignore`, da GitHub ikke tillader filer over 100 MB.
