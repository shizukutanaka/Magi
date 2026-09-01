"""Pythagorean numerology mappings."""

LETTER_VALUES = {
    letter: ((ord(letter) - ord("a")) % 9) + 1
    for letter in "abcdefghijklmnopqrstuvwxyz"
}
MASTER_NUMBERS = (11, 22, 33)
