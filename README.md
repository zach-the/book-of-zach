# Book of Zach
This is the collection of my favorite general conference talks, formatted to be bound and placed in a physical book that slowly expands by itself over time

## Dependencies

- Python 3: `beautifulsoup4`, `lxml` — `sudo pacman -S python-beautifulsoup4 python-lxml`
- LaTeX: `sudo pacman -S texlive-binextra texlive-luatex texlive-latexrecommended texlive-fontsrecommended texlive-pictures`

## Usage

### Build from specific URLs

Pass any number of talk URLs from `churchofjesuschrist.org` or `speeches.byu.edu`:

```bash
./build.sh -o my_talks \
  https://www.churchofjesuschrist.org/study/general-conference/2026/04/11oaks?lang=eng \
  https://www.churchofjesuschrist.org/study/general-conference/2026/04/19eyring?lang=eng
```

Produces `my_talks.pdf` (normal) and `my_talks_booklet.pdf` (signatures for bookbinding).

### Build an entire conference session

```bash
python3 list_talks.py https://www.churchofjesuschrist.org/study/general-conference/2026/04?lang=eng > tmpfile
./build.sh -o april_2026 $(cat tmpfile)
```

### Output files

| File | Description |
|------|-------------|
| `NAME.pdf` | Normal reading PDF (6.875×10.625 in) |
| `NAME_booklet.pdf` | Signature-imposed booklet for duplex printing and binding |

## Already Formatted:
- finding joy in the journey

## To Be Formatted:
- As Many as I Love, I Rebuke and Chasten
- Hope through the atonement of jesus christ
- be 100 percent responsible
- becoming a consecrated missionary
- excerpts from believing christ
- beware of pride
- content with the things allotted unto us
- faith in the lord jesus christ
- hope through the atonement of jesus christ
- lectures on faith, formatted
- let god prevail
- missionary work and the atonement
- one percent better
- the answer is the doctrine
- the father and the son
- the purifying power of gethsemane
- wrestling with comparisons
