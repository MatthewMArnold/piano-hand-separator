import pretty_midi
import os
import math
import argparse

from typing import List, Dict, Tuple, Set, TypeVar, Callable
from pretty_midi.containers import Note
from operator import attrgetter

# Possible chord lengtINotehs.
POSSIBLE_CHORD_LENGTHS = [2, 3, 4]

# In general, we should be splitting notes along middle C, pitch 60.
C4_MIDI_NOTE = 60

# MIDI note associated with the A4 note.
A4_MIDI_NOTE = 69
# Frequency associated with the A4 note.
A4_FREQUENCY = 440

def frequency_to_semitone(frequency: float) -> float:
    '''
    Convert given frequency to a piano semitone relative to A4.
    '''
    return round(12 * math.log2(frequency / A4_FREQUENCY), 1)

def note_to_frequency(note: int) -> float:
    '''
    Convert given midi note to a note frequency.
    '''
    return A4_FREQUENCY * pow(2.0, (note - A4_MIDI_NOTE) / 12.0)

def note_to_semitone(note: int) -> float:
    '''
    Convert given midi note to a piano semitone relative to A4.
    '''
    return frequency_to_semitone(note_to_frequency(note))

T = TypeVar('T')

def get_avg(list: List[T], key: Callable[[T], float]) -> float:
    '''
    Returns the average of the list, using the key to extract elements from the list.
    '''
    return sum([key(x) for x in list]) / len(list)

def separate_hands(start_time_threshold: float,
                   chord_max_key_distance: int,
                   note_list: List[Note]) -> Tuple[List[Note], List[Note]]:
    '''
    Perform note separation. Separates notes from the given note_list into
    two note lists, one for each hand.

    @param start_time_threshold Time threshold to consider two notes to be
    played at the same time. If note "A" is played at some time within
    [-start_time_threshold, start_time_threshold] of note "B", the two notes
    are considered to be played at the same time.
    @param chord_max_key_distance Max semitone distance between two keys such
    that they will be considered part of the same chord. If they are further
    apart than this and played at the same time, it is likely that a different
    hand is playing the note.
    @param note_list List of INotes to be split
    @return (right note list, left note list) tuple, two lists of notes
    separated by hand.
    '''
    # For each note in the sequence generate a list of notes that are played
    # at the same time. For each note, this data structure contains a list of
    # indices that are played at the same time (same starting time) to attempt
    # to identify chords.
    note_idx_to_notes_played_same_time: Dict[int, Set[int]] = dict()

    # Current list of notes that have been played at the same time (within
    # start_time_threshold tolerance). Midi files will likely not have notes
    # in chords played at exactly the same time, so we have to build in some
    # tolerance to our system.
    started_note_indices: List[int] = list()

    for i, note in enumerate(note_list):
        # Update list of started notes
        started_note_indices = list(filter(
            lambda x: abs(note_list[x].start - note.start) <= start_time_threshold,
            started_note_indices)) + [i]

        # Update note_idx_to_notes_played_same_time
        for j in started_note_indices:
            for k in started_note_indices:
                if j != k:
                    if j not in note_idx_to_notes_played_same_time:
                        note_idx_to_notes_played_same_time[j] = set()
                    note_idx_to_notes_played_same_time[j].add(k)

    # Attempt to identify chords played by the same hand
    chords: List[Tuple[float, List[int]]] = list()

    # Note indices that are associated with chords
    idx_in_chords: Set[int] = set()

    def add_chord(cur_chord: List[int]):
        '''
        Add a chord to the chords list.

        @param cur_chord List of notes that make up a chord. A list of indices
        into the note_list.
        '''
        avg_start_time = get_avg(cur_chord, lambda x: note_list[x].start)
        chords.append((avg_start_time, cur_chord))
        for i in cur_chord:
            idx_in_chords.add(i)

    for i, note_played_same_time_idxs in note_idx_to_notes_played_same_time.items():
        potential_chord = [i] + list(note_played_same_time_idxs)

        # Remove any notes that are already in already created chords
        potential_chord = [x for x in potential_chord if x not in idx_in_chords]

        # Not enough notes to make a chord
        if len(potential_chord) < POSSIBLE_CHORD_LENGTHS[0]:
            continue

        # Sort pitches being played at the same time
        potential_chord = sorted(potential_chord, key=lambda x: note_list[x].pitch)

        # Semitones associated with the potential chord
        potential_chord_semitones = [note_to_semitone(note_list[x].pitch) for x in potential_chord]

        def add_potential_chord(cur_min_idx):
            cur_chord = potential_chord[cur_min_idx:j]
            cur_chord_semitone = potential_chord_semitones[cur_min_idx:j]

            semitones = set()
            idxs_to_filter = set()
            for k, semitone in enumerate(cur_chord_semitone):
                if semitone not in semitones:
                    semitones.add(semitone)
                else:
                    idxs_to_filter.add(k)

            cur_chord = list(
                map(lambda x: x[1],
                    filter(lambda x: x[0] not in idxs_to_filter, enumerate(cur_chord))))

            cur_chord_semitone = list(
                map(lambda x: x[1],
                    filter(lambda x: x[0] not in idxs_to_filter, enumerate(cur_chord_semitone))))

            if len(cur_chord) in POSSIBLE_CHORD_LENGTHS:
                add_chord(cur_chord)
            elif len(cur_chord) > POSSIBLE_CHORD_LENGTHS[-1]:
                if len(cur_chord) > 2 * POSSIBLE_CHORD_LENGTHS[-1]:
                    print('WARNING: found > 8 notes played at a time, you '
                            'should decrease start_time_threshold since its '
                            'unlikely that this many notes should be played '
                            'at the same time.')

                # Find index to split the chord at.
                chord_split_idx = 0
                # The largest semitone difference between two adjacent
                # semitones.
                largest_semitone_diff = 0
                for k in range(len(cur_chord) - 1):
                    semitone_diff = cur_chord_semitone[k + 1] - cur_chord_semitone[k]
                    if semitone_diff > largest_semitone_diff:
                        largest_semitone_diff = semitone_diff
                        chord_split_idx = k + 1
                    elif semitone_diff == largest_semitone_diff:
                        pass

                while chord_split_idx > POSSIBLE_CHORD_LENGTHS[-1] and \
                        len(cur_chord) - chord_split_idx <= POSSIBLE_CHORD_LENGTHS[-1]:
                    chord_split_idx -= 1

                while chord_split_idx <= POSSIBLE_CHORD_LENGTHS[-1] and \
                        len(cur_chord) - chord_split_idx > POSSIBLE_CHORD_LENGTHS[-1]:
                    chord_split_idx += 1

                chord_1 = cur_chord[:chord_split_idx]
                chord_2 = cur_chord[chord_split_idx:]

                add_chord(chord_1)
                add_chord(chord_2)

        cur_min_idx = 0
        for j in range(1, len(potential_chord_semitones)):
            if potential_chord_semitones[j] - potential_chord_semitones[cur_min_idx] > chord_max_key_distance:
                add_potential_chord(cur_min_idx)
                cur_min_idx = j

        j += 1
        if cur_min_idx != j:
            add_potential_chord(cur_min_idx)

    chords = list(sorted(chords, key=lambda x: x[0]))

    left_notes: List[Note] = list()
    right_notes: List[Note] = list()

    # Add chords to the notes.
    for i, (start_avg, chord) in enumerate(chords):
        # Find chords that are played at the same time

        chords_starting_same_time: List[int] = list()

        j = i - 1
        while j >= 0 and abs(chords[j][0] - start_avg) <= start_time_threshold:
            chords_starting_same_time.append(j)
            j -= 1

        j = i + 1
        while j < len(chords) and abs(chords[j][0] - start_avg) <= start_time_threshold:
            chords_starting_same_time.append(j)
            j += 1

        def get_pitch_avg(c: List[int]):
            return get_avg(c, lambda x: note_list[x].pitch)

        if chords_starting_same_time != []:
            # Should only be one other chord playing at the same time. Need to
            # select if the chord should be appended to the left or right hand.
            pitch_avgs = [get_pitch_avg(chords[x][1]) for x in chords_starting_same_time]
            center_threshold_avg = sum(pitch_avgs) / len(pitch_avgs)
        else:
            center_threshold_avg = C4_MIDI_NOTE

        def append_notes(notes: List[Note]):
            for idx in chord:
                notes.append(note_list[idx])

        if get_pitch_avg(chord) > center_threshold_avg:
            append_notes(right_notes)
        else:
            append_notes(left_notes)

    # Add notes other than chords to the notes.
    for i, note in enumerate(note_list):
        if i in idx_in_chords:
            continue

        if note.pitch > C4_MIDI_NOTE:
            right_notes.append(note)
        else:
            left_notes.append(note)

    left_notes = sorted(left_notes, key=lambda x: x.start)
    right_notes = sorted(right_notes, key=lambda x: x.start)

    return (right_notes, left_notes)

def gen_separated_midi(start_time_threshold: float,
                       chord_max_key_distance: int,
                       out_file: str,
                       file: str) -> None:
    '''
    Generate a separated midi file that contains two instruments.
    One for the right hand, one for the left hand.

    @param start_time_threshold @see separate_hands.
    @param chord_max_key_distance @see separate_hands.
    @param out_file Midi file to output separated notes to.
    @param file Midi file to separate notes from.
    '''
    # Get PrettyMIDI object instance.
    pm = pretty_midi.PrettyMIDI(file)

    if len(pm.instruments) == 2:
        # left and right hand already separated.
        pm.write(out_file)

    note_list: List[Note] = sorted(pm.instruments[0].notes, key=attrgetter('start'))

    right_notes, left_notes = separate_hands(start_time_threshold,
                                             chord_max_key_distance,
                                             note_list)

    right_hand = pretty_midi.Instrument(
        program=pretty_midi.instrument_name_to_program('Acoustic Grand Piano'))
    left_hand = pretty_midi.Instrument(
        program=pretty_midi.instrument_name_to_program('Acoustic Grand Piano'))

    right_hand.notes = right_notes
    left_hand.notes = left_notes

    # Modify PrettyMidi object to have split left and right hands.
    pm.instruments.clear()
    pm.instruments.append(right_hand)
    pm.instruments.append(left_hand)
    pm.write(out_file)

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-start_time_threshold', type=float, required=False, default=0.11,
                        help='Max time difference between two notes where they '
                             'are considered to be starting at the same time. '
                             'Notes that are starting at the same time are '
                             'identified as chords, which is part of the hand '
                             'separation algorithm. We cannot say that two notes '
                             'start at the same time if they start at exactly the '
                             'same time with no tolerance because midi files can '
                             'be generated from someone playing music and there may '
                             'be variation between notes played at the same time.')
    parser.add_argument('-chord_max_key_distance', type=int, default=12, required=False,
                        help='Max number of keys between the min and max note in '
                             'the chord. It is expected that it is impossible for '
                             'someone to reach between a span greater than this '
                             'amount. For example, if a potential chord has keys C4 '
                             'and C6, this is clearly impossible for the user to '
                             'play and thus is not a chord.')
    parser.add_argument('-out_file', type=str, default=None, required=False,
                        help='The file to output the results to. The results will '
                             'be the form of a midi file with two instruments, one '
                             'for the right hand and one for the right. The '
                             'convention is that instrument at index 0 in the '
                             'instrument list will be the right hand and instrument '
                             'at index 1 will be the left hand. If no output file '
                             'is provided, the output file will be the provided '
                             'file appended with \'_split\'')
    parser.add_argument('file', type=str,
                        help='midi (.midi or .mid) file to perform hand separation.'
                             'This midi file is expected to have a single instrument'
                             '(i.e. a single sequence of notes that needs to be'
                             'split into two note sequences).')

    return parser.parse_args()

def main():
    args = get_args()

    start_time_threshold = args.start_time_threshold
    chord_max_key_distance = args.chord_max_key_distance
    out_file = args.out_file
    file = args.file

    if out_file == None:
        out_file = os.path.splitext(file)[0] + '_split.mid'

    gen_separated_midi(start_time_threshold, chord_max_key_distance, out_file, file)

if __name__ == '__main__':
    main()
