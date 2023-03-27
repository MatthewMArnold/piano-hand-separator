import separate_hands

from pretty_midi.containers import Note
from separate_hands import A4_MIDI_NOTE, C4_MIDI_NOTE

A3_MIDI_NOTE = 57

def test_simple_right():
    n = Note(1, A4_MIDI_NOTE, 0, 1)

    right_notes, left_notes = separate_hands.separate_hands(0.1, 5, [n])

    assert len(right_notes) == 1
    assert len(left_notes) == 0

def test_simple_left():
    n = Note(1, A3_MIDI_NOTE, 0, 1)

    right_notes, left_notes = separate_hands.separate_hands(0.1, 5, [n])

    assert len(right_notes) == 0
    assert len(left_notes) == 1

def test_simple_split_lr():
    nl = Note(1, A3_MIDI_NOTE, 0, 1)
    nr = Note(1, A4_MIDI_NOTE, 0, 1)

    right_notes, left_notes = separate_hands.separate_hands(0.1, 5, [nl, nr])

    assert len(right_notes) == 1
    assert len(left_notes) == 1

def test_simple_chord():
    n1 = Note(1, A3_MIDI_NOTE, 0, 1)
    n2 = Note(1, A3_MIDI_NOTE + 1, 0, 1)
    n3 = Note(1, A3_MIDI_NOTE + 2, 0, 1)

    right_notes, left_notes = separate_hands.separate_hands(0.1, 5, [n1, n2, n3])

    assert len(right_notes) == 0
    assert len(left_notes) == 3

def test_chord_crossing_c4():
    n1 = Note(1, C4_MIDI_NOTE - 1, 0, 1)
    n2 = Note(1, C4_MIDI_NOTE + 1, 0, 1)
    n3 = Note(1, C4_MIDI_NOTE + 2, 0, 1)

    right_notes, left_notes = separate_hands.separate_hands(0.1, 5, [n1, n2, n3])

    assert len(right_notes) == 3
    assert len(left_notes) == 0

def test_lr_chords():
    nl1 = Note(1, C4_MIDI_NOTE - 3, 0, 1)
    nl2 = Note(1, C4_MIDI_NOTE - 2, 0, 1)
    nl3 = Note(1, C4_MIDI_NOTE - 1, 0, 1)

    nr0 = Note(1, C4_MIDI_NOTE + 1, 0, 1)  # on right side but closer to left notes
    nr1 = Note(1, C4_MIDI_NOTE + 12, 0, 1)
    nr2 = Note(1, C4_MIDI_NOTE + 13, 0, 1)
    nr3 = Note(1, C4_MIDI_NOTE + 14, 0, 1)

    right_notes, left_notes = separate_hands.separate_hands(0.1, 5, [nl1, nl2, nl3, nr0, nr1, nr2, nr3])

    assert len(right_notes) == 3
    assert len(left_notes) == 4

def test_start_time_thresholding():
    n1 = Note(1, C4_MIDI_NOTE - 1, 0, 1)
    n2 = Note(1, C4_MIDI_NOTE + 1, 0.1, 1)
    n3 = Note(1, C4_MIDI_NOTE + 2, 0.2, 1)

    right_notes, left_notes = separate_hands.separate_hands(1, 5, [n1, n2, n3])

    # Identified as chord
    assert len(right_notes) == 3
    assert len(left_notes) == 0

    right_notes, left_notes = separate_hands.separate_hands(0.05, 5, [n1, n2, n3])

    # Identified as individual notes
    assert len(right_notes) == 2
    assert len(left_notes) == 1

def main():
    test_simple_right()
    test_simple_left()
    test_simple_split_lr()
    test_simple_chord()
    test_chord_crossing_c4()
    test_lr_chords()
    test_start_time_thresholding()

if __name__ == '__main__':
    main()
