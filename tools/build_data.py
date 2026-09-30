"""Bygger assets/data.js til GitHub Pages-siden.

Læser kapitelmarkører fra MP3'en, transskriptionen (SRT) og beregner en
bølgeform. Kør fra repoets rod:  python tools/build_data.py
Kræver: mutagen, miniaudio (pip install mutagen miniaudio)
"""
import json, math, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MP3 = ROOT / "EMMERSKE EFTERSKOLE - med kapitler.mp3"
SRT = ROOT / "EMMERSKE EFTERSKOLE - transskription.srt"
OUT = ROOT / "assets" / "data.js"

# Titler, medvirkende og beskrivelser (fra kapiteloversigten)
CHAPTER_INFO = [
    ("Intro", "Nadim", "Nadim introducerer Efterskolernes Dag og Emmerske Efterskole.", "radio"),
    ("Hvad er Emmerske Efterskole?", "Forstander Jesper", "Om ordblindhed, mistrivsel, mobning, små hold og tæt voksenkontakt.", "school"),
    ("Livet på et elevværelse", "Emily og Olivia", "Emily og Olivia viser deres værelse og fortæller om hverdagen og fællesskabet.", "bed"),
    ("Fra mobning til fællesskab", "Liam", "Liam ved bordfodbolden om sin tidligere skole, mobning, venner og fællesskab.", "ball"),
    ("Ledige pladser og et nyt skoleliv", "Forstander Jesper", "Om rundvisninger, 8.–10. klasse, økonomisk hjælp og andet år.", "door"),
    ("Kærestevæggen", "Emma og Liv", "Emma og Liv forklarer kærestevæggen: ships, skyer, solen, øen og havet.", "heart"),
    ("Hvorfor vælge et år mere?", "Magnus og Sander", "To andetårselever om tryghed, lærere, ordblindhed og hjælpemidler.", "repeat"),
    ("Trivsel og faglige resultater", "Forstander Jesper", "Praksisnær undervisning, prøver, 10. klasse med EUC Tønder og fritidstilbud.", "chart"),
    ("Fra elev til medarbejder", "Martin", "Tidligere elev, nu servicemedarbejder og underviser i selvforsvar.", "shield"),
    ("AKT og trivselsteamet", "Tobias", "Om selvværd, skolevægring, faglig og social støtte – og KRAP.", "hands"),
    ("Træ og praksisfaglighed", "Sander", "Sander i træværkstedet om at arbejde med hænderne.", "saw"),
    ("Metalværkstedet", "William", "William viser et motorprojekt og starter den højlydte maskine.", "gear"),
    ("At være lærer på Emmerske", "Kjeld", "Om små klasser, individuelle hensyn og modigere ordblinde elever.", "book"),
    ("Reporteren ser tilbage", "Oscar", "Reporter Oscar om sit eget uddannelsesforløb og værdien af efterskolefællesskabet.", "mic"),
    ("Når familien ringer til skolen", "Charlotte", "Om administration, forældrekontakt, økonomi og booking af rundvisning.", "phone"),
    ("Afslutning: Hvorfor Emmerske?", "Forstander Jesper", "Jesper samler op: trivsel, ledige pladser, beliggenhed og skolens historie.", "star"),
    ("Outro", "Nadim", "Nadim afslutter besøget.", "radio"),
]

PEOPLE = [
    ("Nadim Adam", "Vært, Radio Globus", "Guider lytterne gennem eftermiddagen på det flyvende tæppe.", [1, 17]),
    ("Oscar", "Reporter", "Journaliststuderende, der aldrig selv gik på efterskole – og møder den for første gang.", [3, 4, 6, 14]),
    ("Jesper", "Forstander", "Fortæller om trivselsefterskolen, faglige resultater og porten til Tønder.", [2, 5, 8, 16]),
    ("Emily & Olivia", "Elever", "Viser deres firemandsværelse med billeder hjemmefra.", [3]),
    ("Liam", "Elev", "Fandt venner og fællesskab efter mobning på sin gamle skole.", [4]),
    ("Emma & Liv", "Elever", "Guider til kærestevæggen – efterskolens romantiske landkort.", [6]),
    ("Magnus & Sander", "Andetårselever", "Blev et år mere – for fællesskabet og de faglige fremskridt.", [7]),
    ("Martin", "Servicemedarbejder & tidl. elev", "Pedel, AMR, selvforsvarslærer – og selv ordblind.", [9]),
    ("Tobias", "AKT-teamet", "Arbejder med adfærd, kontakt og trivsel efter KRAP-metoden.", [10]),
    ("Sander", "Elev, træværkstedet", "Bygger en kasse – og føler sig friere med hænderne.", [11]),
    ("William", "Elev, metalværkstedet", "Genopbygger en 175 cc græsslåmaskinemotor fra genbrugspladsen.", [12]),
    ("Kjeld", "Lærer", "Matematik, håndværk & design – og glad for støjende elever.", [13]),
    ("Charlotte", "Sekretær", "Stemmen i telefonen, når familier ringer til skolen.", [15]),
]

# Citater (let renset for transskriptionsfejl) med tidspunkt i sekunder
QUOTES = [
    ("Det er et sted, hvor de unge mennesker ikke skal opleve nederlag. Det er et sted, hvor man ikke skal føle sig forkert.", "Forstander Jesper", 111),
    ("På mange måder er det måske skuldrene ned og selvværdet op.", "Forstander Jesper", 173),
    ("De tager mobning meget seriøst her. Og det er meget sjovt at være sammen med folk hele tiden.", "Liam", 687),
    ("Man får mange flere venner her, fordi man bor jo sammen, så man er hele tiden sammen med folk.", "Liam", 720),
    ("Nogle af vores elever skal faktisk i første omgang få lyst til at lære igen.", "Forstander Jesper", 926),
    ("Her kender man og vender med alle.", "Magnus og Sander", 1264),
    ("Der er næsten 100 % af eleverne, der går til alle deres afgangsprøver.", "Forstander Jesper", 1406),
    ("At vi er en stor familie, og at de kan komme til mig lige så vel, som de kan komme til lærerne.", "Martin", 1727),
    ("Vi har meget fokus på at være sammen med eleverne og skabe en bedre fremtid for dem – sammen med dem.", "Tobias", 1954),
    ("Man føler sig lidt mere fri i det. Lidt mere afslappet, i stedet for stressende.", "Sander", 2093),
    ("En hel begejstring over, at deres barn er støjende. Fordi det har de aldrig oplevet før.", "Kjeld", 2331),
    ("Vi har åbent næsten døgnet rundt i forhold til rundvisninger.", "Charlotte", 2559),
    ("Jeg synes jo, jeg har verdens bedste job.", "Forstander Jesper", 2665),
]

SLIDES = [
    "Skuldrene ned, selvværd op",
    "Fra overlevelsestilstand til væksttilstand",
    "Først trivsel, derefter læring",
    "Du er aldrig alene: Vores voksen-økosystem",
    "Støttecentret: Struktureret hjælp til trivsel",
    "Klasseværelset: Hvor nederlag aflyses",
    "Værkstedet: Når hænderne lærer, hvad hovedet frygter",
    "To veje til samme mål",
    "Værelset og fællesarealet: Et trygt hjem",
    "Kulturen: Plads til alle (også på kærestevæggen)",
    "Emmerske-ligningen",
    "Træd ind ad porten til Tønder",
]


def chapters_from_mp3():
    from mutagen.mp3 import MP3
    audio = MP3(MP3_PATH)
    chaps = sorted(
        (f for k, f in audio.tags.items() if k.startswith("CHAP")),
        key=lambda f: f.start_time,
    )
    out = []
    for i, c in enumerate(chaps):
        title, who, desc, icon = CHAPTER_INFO[i]
        file = next(s.text[0] for s in c.sub_frames.values() if hasattr(s, "text"))
        out.append({
            "n": i + 1, "title": title, "who": who, "desc": desc, "icon": icon,
            "start": round(c.start_time / 1000, 2), "end": round(c.end_time / 1000, 2),
            "file": f"Kapitler/{file}.mp3",
        })
    return out, round(audio.info.length, 2)


def parse_srt():
    ts = lambda h, m, s, ms: int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    cues = []
    blocks = re.split(r"\n\s*\n", SRT.read_text(encoding="utf-8").strip())
    for b in blocks:
        lines = b.strip().splitlines()
        m = re.match(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)", lines[1])
        if not m:
            continue
        g = m.groups()
        cues.append([round(ts(*g[:4]), 2), round(ts(*g[4:]), 2), " ".join(lines[2:]).strip()])
    return cues


def waveform(n=1400):
    try:
        import miniaudio
    except ImportError:
        print("miniaudio mangler – springer bølgeform over")
        return []
    d = miniaudio.decode_file(str(MP3_PATH), output_format=miniaudio.SampleFormat.SIGNED16,
                              nchannels=1, sample_rate=8000)
    s = d.samples
    step = len(s) // n
    peaks = []
    for i in range(n):
        seg = s[i * step:(i + 1) * step:4]
        peaks.append(math.sqrt(sum(x * x for x in seg) / len(seg)))
    top = sorted(peaks)[int(n * 0.995)]
    return [round(min(1, p / top), 3) for p in peaks]


MP3_PATH = str(MP3)

if __name__ == "__main__":
    chapters, duration = chapters_from_mp3()
    data = {
        "duration": duration,
        "audio": MP3.name,
        "chapters": chapters,
        "cues": parse_srt(),
        "peaks": waveform(),
        "people": [dict(name=a, role=b, bio=c, chapters=d) for a, b, c, d in PEOPLE],
        "quotes": [dict(text=a, who=b, t=c) for a, b, c in QUOTES],
        "slides": SLIDES,
    }
    OUT.write_text("window.EE = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n",
                   encoding="utf-8")
    print(f"Skrev {OUT} – {len(chapters)} kapitler, {len(data['cues'])} replikker, {len(data['peaks'])} peaks")
