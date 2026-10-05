# Emmerske Efterskole i radioen

Præsentationsside for radioprogrammet **Nadim og det flyvende tæppe** (Radio Globus), der blev sendt direkte fra Emmerske Efterskole ved Tønder op til Efterskolernes Dag.

**Siden:** https://qvisty.github.io/emmerske-radio/

## Indhold
- Afspiller med bølgeform, kapitelmarkører, hastighed, delbare tidspunkter (`#t=sekunder`) og "læs med"-tekst
- 17 kapitler – afspil direkte
- Stemmerne og citater med afspilning
- Slides ("Trivslens arkitektur") og infografikker med zoom
- Læsevenlig visning (større tekst og mere luft) samt lyst/mørkt tema

## Opdatering af data
`assets/data.js` genereres fra kapitelmærkerne i MP3'en:

```
pip install mutagen miniaudio
python tools/build_data.py
```

Titler, beskrivelser, medvirkende og citater redigeres øverst i `tools/build_data.py`.

`EMMERSKE EFTERSKOLE.mp3` (den uredigerede optagelse, 161 MB) er udeladt via `.gitignore`, da GitHub ikke tillader filer over 100 MB.

## Redigerbar præsentation
`Filer/Trivslens Arkitektur Emmerske Efterskole.pptx` (og den tilhørende PDF samt billederne i `assets/slides`) er bygget med `tools/make_editable_pptx.py` ud fra de oprindelige dias i `tools/kilde/`: teksten i de oprindelige (flade) dias er fundet med Windows' OCR, fjernet fra billedet og lagt ind som tekstbokse. Håndskrevne noter i tegningerne er en del af billedet. Kræver Windows med PowerPoint og `pip install pymupdf python-pptx opencv-python-headless pillow`. Hvilke tekster der bliver tekstbokse, styres af `SLIDES` øverst i scriptet.

## Logo
`assets/img/logo.svg` (og faviconet) er lavet med `tools/make_logo.py` ud fra `Filer/Emmerske Efterskole logo.png`. Logoet er sporet som vektorgrafik, så det er skarpt i alle størrelser. Ordet EMMERSKE følger tekstfarven, og det grønne skifter til en lysere nuance i mørkt tema. Kræver `pip install pillow numpy potracer`.
