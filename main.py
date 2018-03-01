#!/usr/bin/env python3

import textract

import ligatures


def stats(words, lig_map):
    # Determine how many words with ligatures removed become ambiguous when we
    # try to add the ligatures back.
    num_ambiguous = 0
    for word in lig_map.lig_words:
        substrs = lig_map.split(word)
        candidates = lig_map.query_word(substrs)
        if len(candidates) > 1:
            num_ambiguous += 1

    # Statistics.
    num_words = len(words)
    num_lig_words = len(lig_map.lig_words)
    lig_percent = num_lig_words / num_words * 100
    ambiguous_percent = num_ambiguous / num_lig_words * 100
    total_ambiguous_percent = num_ambiguous / num_words

    print('{} of {} words contain ligatures ({:.2f}%).'.format(num_lig_words,
                                                               num_words,
                                                               lig_percent))
    print(('{} of {} words with ligatures are ambiguous ({:.2f}%; {:.4f}% of '
           'all words).').format(num_ambiguous, num_lig_words,
                                 ambiguous_percent, total_ambiguous_percent))


def main():
    with open('words.txt') as f:
        words = set(f.read().splitlines())

    # Test out build/save/load
    lig_map = ligatures.build(words)
    lig_map.save('data')
    lig_map = ligatures.load('data')

    stats(words, lig_map)


def test():
    text = textract.process('curses.pdf').decode('utf-8')
    unknown = u'\ufffd'

    lig_map = ligatures.load('data')
    _, new_text = lig_map.query_text(text, unknown, verbose=True)


if __name__ == '__main__':
    main()
