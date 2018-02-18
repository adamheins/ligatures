import re


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

    for curr_part, next_part in zip(parts[:-1], parts[1:]):
        ligs = ss2lig[curr_part]
        candidates = []
        for lig in ligs:
            if next_part in lig2ss[lig]:
                candidates.append(lig)
        print(candidates)


def main():
    substring_to_lig_map = {}
    lig_to_substring_map = {}

    with open('words.txt') as f:
        words = set(f.read().splitlines())

    words_with_ligatures = []

    # Find all words containing ligatures.
    for word in words:
        if COMMON_LIGATURE_REGEX.search(word):
            words_with_ligatures.append(word)

    for word in words_with_ligatures:
        substrs = COMMON_LIGATURE_REGEX.split(word)
        ligs = COMMON_LIGATURE_REGEX.findall(word)

        for ss, lig in zip(substrs, ligs):
            if ss in substring_to_lig_map:
                substring_to_lig_map[ss].add(lig)
            else:
                substring_to_lig_map[ss] = set([lig])

        for lig, ss in zip(ligs, substrs[1:]):
            if lig in lig_to_substring_map:
                lig_to_substring_map[lig].add(ss)
            else:
                lig_to_substring_map[lig] = set([ss])

    save_map(substring_to_lig_map, 'ss2lig.txt')
    save_map(lig_to_substring_map, 'lig2ss.txt')

    query(substring_to_lig_map, lig_to_substring_map, ['di', 'cult'])

    print(len(words_with_ligatures) / len(words) * 100)


if __name__ == '__main__':
    main()
