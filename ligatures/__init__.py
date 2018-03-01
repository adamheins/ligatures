import itertools
import os
import re


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


def save_lig_words(lig_words, ligatures, fname):
    with open(fname, 'w') as f:
        f.write(' '.join(ligatures) + '\n')
        f.write('\n'.join(lig_words))


def remove_ligs(parts, lig_regex):
    ''' Remove and split all parts on any ligatures they may still contain. '''
    parts_no_ligs = []
    for part in parts:
        parts_no_ligs.extend(lig_regex.split(part))
    return parts_no_ligs


def find_words_with_ligatures(words):
    words_with_ligatures = set()
    for word in words:
        if COMMON_LIGATURE_REGEX.search(word):
            words_with_ligatures.add(word)
    return words_with_ligatures


def build_ss2lig_map(words_with_ligatures):
    ss2lig = {}

    for word in words_with_ligatures:
        substrs = COMMON_LIGATURE_REGEX.split(word)
        ligs = COMMON_LIGATURE_REGEX.findall(word)

        # Initialize substring mapping.
        for ss in substrs:
            if ss not in ss2lig:
                ss2lig[ss] = { 'before': set(), 'after': set() }

        for ss, lig in zip(substrs, ligs):
            ss2lig[ss]['after'].add(lig)

        for lig, ss in zip(ligs, substrs[1:]):
            ss2lig[ss]['before'].add(lig)

    return ss2lig


def replace_successful_matches(text, matches):
    successful_matches = list(filter(lambda m: m.success, matches))
    new_text = []
    last_end = 0

    for m in successful_matches:
        new_text.append(text[last_end:m.start])
        new_text.append(m.replacement)
        last_end = m.end
    new_text.append(text[successful_matches[-1].end:])

    return ''.join(new_text)


class LigatureMatch(object):
    def __init__(self, original, candidates, start, end):
        self.original = original
        self.candidates = candidates
        self.start = start
        self.end = end

        if len(candidates) == 1:
            self.success = True
            self.replacement = candidates[0]
        else:
            self.success = False
            self.replacement = None


class LigatureMap(object):
    def __init__(self, lig_words, ss2lig, ligatures):
        self.lig_words = lig_words
        self.ss2lig = ss2lig

        ligatures.sort(key=len, reverse=True)

        self.ligatures = ligatures
        self.regex = re.compile('|'.join(ligatures))

    def save(self, datadir):
        # Create the data directory if it does not yet exist.
        if not os.path.isdir(datadir):
            os.mkdir(datadir)

        ss2lig_path = os.path.join(datadir, SS2LIG_FILE_NAME)
        lig_words_path = os.path.join(datadir, LIG_WORDS_FILE_NAME)

        save_lig_words(self.lig_words, self.ligatures, lig_words_path)
        save_ss2lig_map(self.ss2lig, ss2lig_path)

    def query_word(self, parts):
        # Split words on any remaining ligatures, since these won't appear in
        # the ss2lig map.
        parts = remove_ligs(parts, self.regex)

        # Determine ligatures that neighbouring substrings have in common.
        candidate_ligs = []
        for curr_part, next_part in zip(parts[:-1], parts[1:]):

            if curr_part in self.ss2lig:
                next_ligs = self.ss2lig[curr_part]['after']
            elif curr_part.lower() in self.ss2lig:
                next_ligs = self.ss2lig[curr_part.lower()]['after']
            else:
                return []

            if next_part in self.ss2lig:
                prev_ligs = self.ss2lig[next_part]['before']
            elif curr_part.lower() in self.ss2lig:
                prev_ligs = self.ss2lig[next_part.lower()]['before']
            else:
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

        num_failed = 0
        num_ambiguous = 0
        num_success = 0

        matches = []

        # Find all words with ligatures.
        for match in re.finditer(lig_word_regex, text):
            word = match.group(1)

            parts = word.split(lig_identifier)
            candidates = self.query_word(parts)

            if len(candidates) == 0:
                num_failed += 1
                if verbose:
                    print('Could not find a match for {}.'.format(word))
            elif len(candidates) > 1:
                num_ambiguous += 1
                if verbose:
                    print('Ambiguous case: found multiple matches for {}: {}'
                          .format(match, ', '.join(candidates)))
            else:
                num_success += 1

            lig_match = LigatureMatch(word, candidates, match.start(1),
                                      match.end(1))
            matches.append(lig_match)

        if verbose:
            print('Total: {}'.format(num_success + num_failed + num_ambiguous))
            print('Successful: {}'.format(num_success))
            print('Failed: {}'.format(num_failed))
            print('Ambiguous: {}'.format(num_ambiguous))

        new_text = replace_successful_matches(text, matches)

        return matches, new_text

    def split(self, string):
        return self.regex.split(string)


def build(words, ligatures=COMMON_LIGATURES):
    ''' Build ligature database. '''
    lig_words = find_words_with_ligatures(words)
    ss2lig = build_ss2lig_map(lig_words)
    return LigatureMap(lig_words, ss2lig, ligatures)


def load_lig_words(fname):
    with open(fname) as f:
        lines = f.read().splitlines()
    ligatures = lines[0].split(' ')
    lig_words = set(lines[1:])
    return lig_words, ligatures


def load_ss2lig_map(fname):
    with open(fname) as f:
        lines = f.readlines()

    ss2lig = {}
    for line in lines:
        k, v = tuple(line.strip().split(':'))
        before, after = tuple(v.split(';'))
        before = set(before.split(','))
        after = set(after.split(','))
        ss2lig[k] = { 'before': before, 'after': after }

    return ss2lig


def load(datadir):
    ''' Load ligature data. '''
    ss2lig_path = os.path.join(datadir, SS2LIG_FILE_NAME)
    lig_words_path = os.path.join(datadir, LIG_WORDS_FILE_NAME)

    lig_words, ligatures = load_lig_words(lig_words_path)
    ss2lig = load_ss2lig_map(ss2lig_path)

    return LigatureMap(lig_words, ss2lig, ligatures)
