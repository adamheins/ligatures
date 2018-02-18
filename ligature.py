import re
import itertools


# NOTE: we want longer ligatures first
COMMON_LIGATURE_BASES = ['fi', 'fl', 'i', 'j', 'l', 'f']
COMMON_LIGATURES = ['f' + s for s in COMMON_LIGATURE_BASES]
COMMON_LIGATURE_REGEX = re.compile('|'.join(COMMON_LIGATURES))

OTHER_LIGATURE_BASES = ['a', 'e', 'o', 'r', 's', 't', 'b', 'h', 'u', 'y', '.',
                        ',', '-']
OTHER_LIGATURES = [f + s for f in ['f', 'ff', 'fft'] for s in OTHER_LIGATURE_BASES]


def save_map(m, fname):
    with open(fname, 'w') as f:
        for k, v in m.items():
            f.write('{}:{}\n'.format(k, ','.join(v)))


def remove_ligs(parts):
    parts_no_ligs = []
    for part in parts:
        parts_no_ligs.extend(COMMON_LIGATURE_REGEX.split(part))
    return parts_no_ligs


def query(ss2lig, lig2ss, parts):
    parts = remove_ligs(parts)

    candidates = []
    for curr_part, next_part in zip(parts[:-1], parts[1:]):
        ligs = ss2lig[curr_part]
        candidates.append([])
        for lig in ligs:
            if next_part in lig2ss[lig]:
                candidates[-1].append(lig)

    lig_combos = itertools.product(*candidates)
    candidate_words = []
    for lig_combo in lig_combos:
        word = [parts[0]]
        for lig, part in zip(lig_combo, parts[1:]):
            word.append(lig)
            word.append(part)
        candidate_words.append(''.join(word))

    return candidate_words


def main():
    ss2lig = {}
    lig2ss = {}

    with open('words.txt') as f:
        words = set(f.read().splitlines())

    words_with_ligatures = []
    num_lig_hist = {}

    # Find all words containing ligatures.
    for word in words:
        if COMMON_LIGATURE_REGEX.search(word):
            words_with_ligatures.append(word)

    for word in words_with_ligatures:
        substrs = COMMON_LIGATURE_REGEX.split(word)
        ligs = COMMON_LIGATURE_REGEX.findall(word)

        # Construct a histogram of number of ligatures in each word with at
        # least one.
        if len(ligs) in num_lig_hist:
            num_lig_hist[len(ligs)].append(word)
        else:
            num_lig_hist[len(ligs)] = [word]

        for ss, lig in zip(substrs, ligs):
            if ss in ss2lig:
                ss2lig[ss].add(lig)
            else:
                ss2lig[ss] = set([lig])

        for lig, ss in zip(ligs, substrs[1:]):
            if lig in lig2ss:
                lig2ss[lig].add(ss)
            else:
                lig2ss[lig] = set([ss])

    save_map(ss2lig, 'ss2lig.txt')
    save_map(lig2ss, 'lig2ss.txt')

    num_ambiguous = 0
    for word in words_with_ligatures:
        substrs = COMMON_LIGATURE_REGEX.split(word)
        candidates = query(ss2lig, lig2ss, substrs)
        candidates = [c for c in candidates if c in words]
        if len(candidates) > 1:
            num_ambiguous += 1

    num_words = len(words)
    num_lig_words = len(words_with_ligatures)
    lig_percent = num_lig_words / num_words * 100
    ambiguous_percent = num_ambiguous / num_lig_words * 100
    total_ambiguous_percent = num_ambiguous / num_words

    print('{} of {} words contain ligatures ({:.2f}%).'.format(num_lig_words, num_words, lig_percent))
    print('{} of {} words with ligatures are ambiguous ({:.2f}%; {:.4f}% of all words).'.format(num_ambiguous, num_lig_words, ambiguous_percent, total_ambiguous_percent))


if __name__ == '__main__':
    main()
