import re
import itertools

import textract


# NOTE: we want longer ligatures first
COMMON_LIGATURE_BASES = ['fi', 'fl', 'i', 'j', 'l', 'f']
COMMON_LIGATURES = ['f' + s for s in COMMON_LIGATURE_BASES]
COMMON_LIGATURE_REGEX = re.compile('|'.join(COMMON_LIGATURES))

OTHER_LIGATURE_BASES = ['a', 'e', 'o', 'r', 's', 't', 'b', 'h', 'u', 'y', '.',
                        ',', '-']
OTHER_LIGATURES = [f + s for f in ['f', 'ff', 'fft'] for s in OTHER_LIGATURE_BASES]


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


def query(ss2lig, parts):
    parts = remove_ligs(parts)

    candidates = []
    for curr_part, next_part in zip(parts[:-1], parts[1:]):
        try:
            next_ligs = ss2lig[curr_part]['after']
            prev_ligs = ss2lig[next_part]['before']
        except KeyError:
            return None
        ligs = next_ligs.intersection(prev_ligs)
        candidates.append(ligs)

    lig_combos = itertools.product(*candidates)
    candidate_words = []
    for lig_combo in lig_combos:
        word = [parts[0]]
        for lig, part in zip(lig_combo, parts[1:]):
            word.append(lig)
            word.append(part)
        candidate_words.append(''.join(word))

    return candidate_words


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


def build():
    ''' Build ligature database. '''
    with open('words.txt') as f:
        words = set(f.read().splitlines())

    words_with_ligatures = find_words_with_ligatures(words)
    with open('words_with_ligatures.txt', 'w') as f:
        f.write('\n'.join(words_with_ligatures))

    ss2lig, _ = build_ss2lig_map(words_with_ligatures)
    save_ss2lig_map(ss2lig, 'ss2lig.txt')

    return words, words_with_ligatures, ss2lig


def load():
    ''' Load ligature data. '''
    with open('words_with_ligatures.txt') as f:
        words_with_ligatures = set(f.read().splitlines())

    with open('ss2lig.txt') as f:
        lines = f.readlines()

    ss2lig = {}
    for line in lines:
        k, v = tuple(line.strip().split(':'))
        before, after = tuple(v.split(';'))
        before = set(before.split(','))
        after = set(after.split(','))
        ss2lig[k] = { 'before': before, 'after': after }

    return words_with_ligatures, ss2lig


def main():
    words, _, _ = build()
    words_with_ligatures, ss2lig = load()

    # Determine how many words with ligatures removed become ambiguous when we
    # try to add the ligatures back.
    num_ambiguous = 0
    for word in words_with_ligatures:
        substrs = COMMON_LIGATURE_REGEX.split(word)
        candidates = query(ss2lig, substrs)
        candidates = [c for c in candidates if c in words_with_ligatures]
        if len(candidates) > 1:
            num_ambiguous += 1

    # Statistics.
    num_words = len(words)
    num_lig_words = len(words_with_ligatures)
    lig_percent = num_lig_words / num_words * 100
    ambiguous_percent = num_ambiguous / num_lig_words * 100
    total_ambiguous_percent = num_ambiguous / num_words

    print('{} of {} words contain ligatures ({:.2f}%).'.format(num_lig_words, num_words, lig_percent))
    print('{} of {} words with ligatures are ambiguous ({:.2f}%; {:.4f}% of all words).'.format(num_ambiguous, num_lig_words, ambiguous_percent, total_ambiguous_percent))


def test():
    text = textract.process('curses.pdf').decode('utf-8')
    unknown = u'\ufffd'
    regex = u'\W(([a-zA-Z]*\ufffd)+[a-zA-Z]*)\W'

    words_with_ligatures, ss2lig = load()

    for match, _ in re.findall(regex, text):
        parts = match.split(unknown)
        candidates = query(ss2lig, parts)
        if candidates is None:
            print('Could not find a match for {}.'.format(match))
            continue
        candidates = [c for c in candidates if c in words_with_ligatures]
        print(candidates)


if __name__ == '__main__':
    test()
