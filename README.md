# Ligatures

[Ligatures](https://en.wikipedia.org/wiki/Typographic_ligature) are special
glyphs that represent two or more letters. For example, the letter pair `ff` is
often converted to a ligature to connect the two `f`'s together.

This project aims to enable some analysis on ligatures in English words. My
motivation was the discovery of some PDF files that have seemingly not encoded
ligatures properly and thus render them incorrectly. I was curious if one could
replace a missing ligature based on the remaining non-ligature parts of the
word. It turn out that, in most cases, one can!

## Install
1. Clone the repository: `git clone git@github.com:adamheins/ligatures.git`.
2. Run `./setup.py install`. This will install the `ligatures` Python package.

**Note:** The project was written for Python 3 and was not tested with Python
2.

## Usage
The `ligatures` package provides two functions:
* `build(words)` takes a list of words and returns a newly-constructed
  `LigatureMap`. Also optionally takes a list of ligatures; defaults to
  `COMMON_LIGATURES`.
* `load(datadir)` loads a previously-saved `LigatureMap` from the directory
  `datadir`.
Lists of ligatures are also provided as the constants `COMMON_LIGATURES` and
`OTHER_LIGATURES`.

The `LigatureMap` object has four methods:
* `save(datadir)` saves the `LigatureMap` to the directory `datadir` for later
  loading.
* `split(string)` splits the provided string on the map's ligatures.
* `query_word(parts)` attempts to reconstruct a word with missing ligatures
  based on the provided non-ligature parts. For example, the parts `[di,
  erent]` would be reconstructed as the word `different`. Returns a list of all
  candidate matches.
* `query_text(text, lig_identifier)` attempts to reconstruct a whole string of
  text, with missing ligatures denoted by `lig_identifier`. Returns the matches
  and the new text.

## Examples
There are two scripts provided in the repository in the `examples/` directory.

The first is `stats.py`, which prints out some statistics about the occurrence
of ligatures in a large English word corpus stored in `words.txt`. The corpus
is a combination of the words from
[here](https://github.com/dwyl/english-words) and those found in
`/usr/share/dict/words`. You can, of course, modify the examples to use a
corpus of your choice.

The second script is `parse_pdf.py`. This loads the provided `sample.pdf`,
which contains a bunch of unknown ligatures, and extracts its text. It then
reconstructs the correct string of words based on knowledge of ligature
occurrences in the corpus.
