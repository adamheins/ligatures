
import itertools
import os
import re

import textract


# NOTE: we want longer ligatures first
COMMON_LIGATURE_BASES = sorted(['fi', 'fl', 'i', 'j', 'l', 'f'], key=len, reverse=True)
COMMON_LIGATURES = ['f' + s for s in COMMON_LIGATURE_BASES]
COMMON_LIGATURE_REGEX = re.compile('|'.join(COMMON_LIGATURES))

OTHER_LIGATURE_BASES = ['a', 'e', 'o', 'r', 's', 't', 'b', 'h', 'u', 'y', '.',
                        ',', '-']
OTHER_LIGATURES = [f + s for f in ['f', 'ff', 'fft']
                         for s in OTHER_LIGATURE_BASES]

SS2LIG_FILE_NAME = 'ss2lig.txt'
LIG_WORDS_FILE_NAME = 'lig_words.txt'


def save_ss2lig_map(ss2lig, fname):
    with open(fname, 'w') as f:
        for k, v in ss2lig.items():
            before = ','.join(v['before'])
            after = ','.join(v['after'])
            f.write('{}:{};{}\n'.format(k, before, after))


def remove_ligs(parts):
    parts_no_ligs = []
    for part in parts:
        parts_no_ligs.extend(COMMON_LIGATURE_REGEX.split(part))
    return parts_no_ligs


def find_words_with_ligatures(words):
    words_with_ligatures = set()
    for word in words:
        if COMMON_LIGATURE_REGEX.search(word):
            words_with_ligatures.add(word)
    return words_with_ligatures


def build_ss2lig_map(words_with_ligatures):
    ss2lig = {}
    num_lig_hist = {}

    for word in words_with_ligatures:
        substrs = COMMON_LIGATURE_REGEX.split(word)
        ligs = COMMON_LIGATURE_REGEX.findall(word)

        # Construct a histogram of number of ligatures in each word with at
        # least one.
        if len(ligs) in num_lig_hist:
            num_lig_hist[len(ligs)].append(word)
        else:
            num_lig_hist[len(ligs)] = [word]

        # Initialize substring mapping.
        for ss in substrs:
            if ss not in ss2lig:
                ss2lig[ss] = { 'before': set(), 'after': set() }

        for ss, lig in zip(substrs, ligs):
            ss2lig[ss]['after'].add(lig)

        for lig, ss in zip(ligs, substrs[1:]):
            ss2lig[ss]['before'].add(lig)

    return ss2lig, num_lig_hist


class LigatureMap(object):
    def __init__(self, lig_words, ss2lig, ligatures):
        self.lig_words = lig_words
        self.ss2lig = ss2lig

        ligatures.sort(key=len, reverse=True)
        self.regex = re.compile('|'.join(ligatures))

    def save(self, datadir):
        # Create the data directory if it does not yet exist.
        if not os.path.isdir(datadir):
            os.mkdir(datadir)

        ss2lig_path = os.path.join(datadir, SS2LIG_FILE_NAME)
        lig_words_path = os.path.join(datadir, LIG_WORDS_FILE_NAME)

        # Save list of words containing ligatures.
        with open(lig_words_path, 'w') as f:
            f.write('\n'.join(self.lig_words))

        # Saving mapping of substrings to neighbouring ligatures.
        save_ss2lig_map(self.ss2lig, ss2lig_path)

    def query_word(self, parts):
        # Split words on any remaining ligatures, since these won't appear in
        # the ss2lig map.
        parts = remove_ligs(parts)

        # Determine ligatures that neighbouring substrings have in common.
        candidate_ligs = []
        for curr_part, next_part in zip(parts[:-1], parts[1:]):
            try:
                next_ligs = self.ss2lig[curr_part]['after']
                prev_ligs = self.ss2lig[next_part]['before']
            except KeyError:
                # TODO handle capitalization
                return []
            ligs = next_ligs.intersection(prev_ligs)
            candidate_ligs.append(ligs)

        # Generate all combinations of potential ligature candidate.
        lig_combos = itertools.product(*candidate_ligs)

        # Build all possible candidate words.
        candidate_words = []
        for lig_combo in lig_combos:
            word = [parts[0]]
            for lig, part in zip(lig_combo, parts[1:]):
                word.append(lig)
                word.append(part)
            candidate_words.append(''.join(word))

        # Filter out candidates that aren't actual words.
        candidate_words = [c for c in candidate_words if c in self.lig_words]

        return candidate_words

    def query_text(self, text, lig_identifier, verbose=False):
        # Regex to find words that contain one or more occurences of the given
        # ligature identifier.
        lig_word_regex = u'\W(([a-zA-Z]*' + lig_identifier + ')+[a-zA-Z]*)\W'

        # Find all words with ligatures.
        for match, _ in re.findall(lig_word_regex, text):
            parts = match.split(lig_identifier)
            candidates = self.query_word(parts)
            if len(candidates) == 0:
                print('Could not find a match for {}.'.format(match))
            elif len(candidates) > 1:
                print('Ambiguous case: found multiple matches for {}: {}'
                      .format(match, ', '.join(candidates)))
            else:
                # TODO we're going to want to pack this into a dictionary or
                # something
                print(candidates)

    def split(self, string):
        return self.regex.split(string)


def build(words, ligatures=COMMON_LIGATURES):
    ''' Build ligature database. '''
    lig_words = find_words_with_ligatures(words)
    ss2lig, _ = build_ss2lig_map(lig_words)
    return LigatureMap(lig_words, ss2lig, ligatures)


def load(datadir):
    ''' Load ligature data. '''

    ss2lig_path = os.path.join(datadir, SS2LIG_FILE_NAME)
    lig_words_path = os.path.join(datadir, LIG_WORDS_FILE_NAME)

    # TODO read ligatures from first line in file
    with open(lig_words_path) as f:
        lig_words = set(f.read().splitlines())

    with open(ss2lig_path) as f:
        lines = f.readlines()

    # TODO should be its own function
    ss2lig = {}
    for line in lines:
        k, v = tuple(line.strip().split(':'))
        before, after = tuple(v.split(';'))
        before = set(before.split(','))
        after = set(after.split(','))
        ss2lig[k] = { 'before': before, 'after': after }

    return LigatureMap(lig_words, ss2lig, COMMON_LIGATURES)


def stats(words, lig_map):
    # Determine how many words with ligatures removed become ambiguous when we
    # try to add the ligatures back.
    num_ambiguous = 0
    for word in lig_map.lig_words:
        substrs = lig_map.split(word)
        candidates = lig_map.query(substrs)
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
    lig_map = build(words)
    lig_map.save('data')
    lig_map = load('data')

    stats(words, lig_map)


def test():
    text = textract.process('curses.pdf').decode('utf-8')
    unknown = u'\ufffd'

    lig_map = load('data')
    lig_map.query_text(text, unknown)


if __name__ == '__main__':
    test()
