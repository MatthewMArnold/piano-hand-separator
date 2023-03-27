# Piano Hand Separator

A tool that separates out a single stream of music from a midi file into two
instruments within a single midi file. This allows piano-specific operations to
be performed on the midi file that require music be separated into streams of
music for the left and right hand.

Some example uses include:
* Generating sheet music from a midi file of someone playing the piano. Sheet
  music must be separated into treble and base clef.
* Classifying difficulty of piano music. It is often necessary to provide left
  and right hand piano fingering to a piano difficulty analyzer. Before using a
  tool such as [PianoPlayer](https://github.com/marcomusy/pianoplayer) you must
  split the midi file with a single instrument into one with two--one for the
  right hand and one for the right.

## Usage

```
usage: separate_hands.py [-h] [-start_time_threshold START_TIME_THRESHOLD] [-chord_max_key_distance CHORD_MAX_KEY_DISTANCE]
                         [-out_file OUT_FILE]
                         file

positional arguments:
  file                  midi (.midi or .mid) file to perform hand separation.This midi file is expected to have a single instrument(i.e. a
                        single sequence of notes that needs to besplit into two note sequences).

options:
  -h, --help            show this help message and exit
  -start_time_threshold START_TIME_THRESHOLD
                        Max time difference between two notes where they are considered to be starting at the same time. Notes that are
                        starting at the same time are identified as chords, which is part of the hand separation algorithm. We cannot say
                        that two notes start at the same time if they start at exactly the same time with no tolerance because midi files can
                        be generated from someone playing music and there may be variation between notes played at the same time.
  -chord_max_key_distance CHORD_MAX_KEY_DISTANCE
                        Max number of keys between the min and max note in the chord. It is expected that it is impossible for someone to
                        reach between a span greater than this amount. For example, if a potential chord has keys C4 and C6, this is clearly
                        impossible for the user to play and thus is not a chord.
  -out_file OUT_FILE    The file to output the results to. The results will be the form of a midi file with two instruments, one for the
                        right hand and one for the right. The convention is that instrument at index 0 in the instrument list will be the
                        right hand and instrument at index 1 will be the left hand. If no output file is provided, the output file will be
                        the provided file appended with '_split'
```
