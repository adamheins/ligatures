#!/usr/bin/env python3

import textract

import ligatures


def main():
    text = textract.process('curses.pdf').decode('utf-8')
    unknown_lig = u'\ufffd'

    lig_map = ligatures.load('data')
    _, new_text = lig_map.query_text(text, unknown_lig, verbose=True)


if __name__ == '__main__':
    main()
