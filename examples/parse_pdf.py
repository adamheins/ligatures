#!/usr/bin/env python3
import os
import textract
import ligatures


def main():
    # Extract the text from the PDF file.
    text = textract.process('sample.pdf').decode('utf-8').strip()

    # Symbol representing a missing ligature (unicode "unknown" glyph)
    unknown_lig = u'\ufffd'

    # Build the ligature map if it doesn't already exist.
    if not os.path.isdir('data'):
        with open('words.txt') as f:
            words = set(f.read().splitlines())
        lig_map = ligatures.build(words)
        lig_map.save('data')

    # Load the ligature map from the data directory.
    lig_map = ligatures.load('data')

    # Restore the missing ligatures.
    _, new_text = lig_map.query_text(text, unknown_lig)

    print('Original: {}'.format(text))
    print('Restored: {}'.format(new_text))


if __name__ == '__main__':
    main()
