#!/usr/bin/env python3

import textract

import ligatures


def main():
    # Extract the text from the PDF file.
    text = textract.process('sample.pdf').decode('utf-8').strip()

    # Symbol representing a missing ligature (unicode "unknown" glyph)
    unknown_lig = u'\ufffd'

    # Load the ligature map from the data directory.
    lig_map = ligatures.load('data')

    # Restore the missing ligatures.
    _, new_text = lig_map.query_text(text, unknown_lig, verbose=True)

    print(text)
    print(new_text)


if __name__ == '__main__':
    main()
