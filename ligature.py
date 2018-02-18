import re


# NOTE: we want longer ligatures first
COMMON_LIGATURE_BASES = ['fi', 'fl', 'i', 'j', 'l', 'f']
COMMON_LIGATURES = ['f' + s for s in COMMON_LIGATURE_BASES]

OTHER_LIGATURE_BASES = ['a', 'e', 'o', 'r', 's', 't', 'b', 'h', 'u', 'y', '.',
                        ',', '-']
OTHER_LIGATURES = [f + s for f in ['f', 'ff', 'fft'] for s in OTHER_LIGATURE_BASES]


def main():
    with open('words.txt') as f:
        words = set(f.read().splitlines())

    ligature_regex = re.compile('|'.join(COMMON_LIGATURES))

    words_with_ligatures = []

    # Find all words containing ligatures.
    for word in words:
        if ligature_regex.match(word):
            words_with_ligatures.append(word)

    deligatured_dupes = []

    count = 0
    for word in words_with_ligatures:
        deligatured_word_parts = ligature_regex.split(word)
        if len(deligatured_word_parts) > 2:
            count += 1
        deligatured_word = ''.join(deligatured_word_parts)
        if deligatured_word in words:
            print('{} -> {}'.format(word, deligatured_word_parts))
            deligatured_dupes.append(word)

    print(len(words_with_ligatures) / len(words) * 100)
    print(len(deligatured_dupes) / len(words) * 100)
    print(len(deligatured_dupes))
    print(count)


if __name__ == '__main__':
    main()
