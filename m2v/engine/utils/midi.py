###############################################################################
#                                MIDI Module                                  #
###############################################################################
"""
MIDI module imported from https://github.com/JacquesLucke/animation_nodes
This part are written by Omar Emara and licensed under the GPLv3 license.
I was the initiator and participated in the implementation of the MIDI module in Animation Nodes
Additions:
    added noteMin & noteMax in track object 
    added notes_used in track object
    added track, only if it contains notes in tracks
    added trackIndexUsed vs trackIndex
Somes Fix:
    decode("latin-1") instead of decode("utf-8")
TODO:
    snake_case
"""

from dataclasses import dataclass, field
from typing import List
import struct
import mmap
from os import SEEK_CUR

def evaluate_envelope(time, time_on, time_off, attack_time, attack_interpolation,
    decay_time, decay_interpolation, sustain_level):
    """
    find either point in time for envelope or where in envelope the time_off happened
    """
    relative_time = min(time, time_off) - time_on

    if relative_time <= 0.0:
        return 0.0

    if relative_time < attack_time:
        return attack_interpolation(relative_time / attack_time)

    relative_time = relative_time - attack_time

    if relative_time < decay_time:
        decay_normalized = decay_interpolation(1 - relative_time / decay_time)
        return decay_normalized * (1 - sustain_level) + sustain_level

    return sustain_level

@dataclass
class MIDINote:
    """
    This class stores essential MIDI note data and provides functionality to evaluate
    the note's envelope value at a given time.
    Attributes:
        channel (int): MIDI channel number (0-15)
        note_number (int): MIDI note number (0-127)
        time_on (float): Time when note was pressed/started in seconds
        time_off (float): Time when note was released/ended in seconds
        velocity (float): Note velocity/loudness (0.0-1.0)
    """
    channel: int = 0
    note_number: int = 0
    time_on: float = 0
    time_off: float = 0
    velocity: float = 0

    def evaluate(self, time, attack_time, attack_interpolation, decay_time, decay_interpolation,
        sustain_level, release_time, release_interpolation, velocity_sensitivity):
        """
        Evaluates the ADSR (Attack, Decay, Sustain, Release) envelope at a given time.
        Parameters:
            time (float): Current time to evaluate the envelope at
            attack_time (float): Duration of the attack phase
            attack_interpolation (callable): Interpolation function for attack phase
            decay_time (float): Duration of the decay phase
            decay_interpolation (callable): Interpolation function for decay phase
            sustain_level (float): Level at which the envelope sustains
            release_time (float): Duration of the release phase
            release_interpolation (callable): Interpolation function for release phase
            velocity_sensitivity (float): Value between 0 and 1 indicating how much
            the velocity affects the envelope (0 = no effect, 1 = full effect)
        Returns:
            float: The calculated envelope value at the given time,
            incorporating velocity sensitivity
        """
        value = evaluate_envelope(time, self.time_on, self.time_off, attack_time,
                attack_interpolation, decay_time, decay_interpolation, sustain_level)

        if time > self.time_off:
            value = value * release_interpolation(1 - ((time - self.time_off) / release_time))

        # if velocity sensitivity is 25%, then take 75% of envelope
        # and 25% of envelope with velocity
        return (1 - velocity_sensitivity) * value + velocity_sensitivity * self.velocity * value

    def copy(self):
        """
        Create a copy of the MIDINote object.
        Returns:
            MIDINote: A new MIDINote object with the same channel, note number, time on, time off
            and velocity values as the original.
        """
        return MIDINote(self.channel, self.note_number, self.time_on, self.time_off, self.velocity)

@dataclass
class MIDITrackUsed:
    """
    This class holds information about a MIDI track including its index number,
    name, total note count, and a list of used note numbers.
    Attributes:
        track_index (int): The index number of the MIDI track. Defaults to 0.
        name (str): The name of the MIDI track. Defaults to empty string.
        note_count (int): The total number of notes in the track. Defaults to 0.
        notes_used (List[int]): A list containing all unique MIDI note numbers used in this track.
    """
    track_index: int = 0
    name: str = ""
    note_count: int = 0
    notes_used: List[int] = field(default_factory=list)

@dataclass
class MIDITrack:
    """
    This class stores and manages MIDI notes within a track, providing functionality to evaluate
    note values at specific time points based on various envelope parameters.
    Attributes:
        name (str): The name of the MIDI track.
        index (int): The index/number of the MIDI track.
        min_note (int): The lowest note number in the track (defaults to 1000).
        max_note (int): The highest note number in the track (defaults to 0).
        notes (List[MIDINote]): List of MIDI notes contained in the track.
        notes_used (List[int]): List of note numbers that are used in the track.
    """
    name: str = ""
    index: int = 0
    min_note: int = 1000
    max_note: int = 0
    min_velo: int = 127
    max_velo: int = 0
    notes: List[MIDINote] = field(default_factory=list)
    notes_used: List[int] = field(default_factory=list)

    def evaluate(self, time, channel, note_number,
        attack_time, attack_interpolation, decay_time, decay_interpolation, sustain_level,
        release_time, release_interpolation, velocity_sensitivity):
        """
        Evaluates the ADSR envelope for a specific note at a given time point.
        Parameters:
            time (float): Current time point for evaluation
            channel (int): MIDI channel number
            note_number (int): MIDI note number
            attack_time (float): Duration of attack phase in seconds
            attack_interpolation (float): Interpolation curve for attack phase
            decay_time (float): Duration of decay phase in seconds 
            decay_interpolation (float): Interpolation curve for decay phase
            sustain_level (float): Amplitude level during sustain phase (0.0 to 1.0)
            release_time (float): Duration of release phase in seconds
            release_interpolation (float): Interpolation curve for release phase
            velocity_sensitivity (float): Sensitivity to MIDI velocity (0.0 to 1.0)
        Returns:
            float: Envelope amplitude value at the given time point (0.0 to 1.0).
                  Returns 0.0 if no matching notes are found.
        Notes:
            The function filters notes by channel and note number, then evaluates the ADSR 
            envelope for all matching notes that are active at the given time point. 
            Returns the maximum envelope value among all matching notes.
        """
        note_filter = lambda note: note.channel == channel and note.note_number == note_number
        time_filter = lambda note: note.time_off + release_time >= time >= note.time_on
        filtered_notes = filter(lambda note: note_filter(note) and time_filter(note), self.notes)
        arguments = (time, attack_time, attack_interpolation, decay_time, decay_interpolation,
            sustain_level, release_time, release_interpolation, velocity_sensitivity)
        return max((note.evaluate(*arguments) for note in filtered_notes), default=0.0)

    def evaluate_all(self, time, channel,
        attack_time, attack_interpolation, decay_time, decay_interpolation, sustain_level,
        release_time, release_interpolation, velocity_sensitivity):
        """
        Evaluates the ADSR envelope for all MIDI notes at a given time point.

        This method calculates the envelope value for each MIDI note (0-127)
        on the specified channel
        at the given time, using the provided ADSR (Attack, Decay, Sustain, Release) parameters.

        Args:
            time (float): The current time point to evaluate
            channel (int): MIDI channel to evaluate notes from
            attack_time (float): Duration of the attack phase in seconds
            attack_interpolation (float): Shape of the attack curve (0-1)
            decay_time (float): Duration of the decay phase in seconds
            decay_interpolation (float): Shape of the decay curve (0-1)
            sustain_level (float): Level during sustain phase (0-1)
            release_time (float): Duration of the release phase in seconds
            release_interpolation (float): Shape of the release curve (0-1)
            velocity_sensitivity (float): How much the note velocity affects the envelope (0-1)

        Returns:
            list[float]: A list of 128 envelope values (0-1), one for each MIDI note number,
                         where each value represents the current amplitude of that note
        """
        channel_filter = lambda note: note.channel == channel
        time_filter = lambda note: note.time_off + release_time >= time >= note.time_on
        filtered_notes = list(filter(lambda note: channel_filter(note)
                         and time_filter(note), self.notes))
        arguments = (time, attack_time, attack_interpolation, decay_time, decay_interpolation,
            sustain_level, release_time, release_interpolation, velocity_sensitivity)
        note_values = []
        for i in range(128):
            filtered_by_number_notes = filter(lambda note: note.note_number == i, filtered_notes)
            value = max((note.evaluate(*arguments) for note in filtered_by_number_notes),
                    default=0.0)
            note_values.append(value)
        return note_values

    def copy(self):
        """
        Creates a deep copy of the MIDITrack instance.
        Returns
        -------
        MIDITrack
            A new MIDITrack instance with the same attributes as the original,
            including a deep copy of all its notes.
        """
        return MIDITrack(self.name, self.index, self.min_note, self.max_note, self.min_velo, self.max_velo,
                [n.copy() for n in self.notes])

# Channel events
@dataclass
class NoteOnEvent:
    """
    This class encapsulates MIDI Note On events, which occur when a note starts playing.
    Attributes:
        delta_time (int): The time delay before this event in MIDI ticks
        channel (int): The MIDI channel number (0-15)
        note (int): The MIDI note number (0-127)
        velocity (int): The velocity/loudness of the note (0-127)
    """
    delta_time: int
    channel: int
    note: int
    velocity: int

    @classmethod
    def from_memory_map(cls, delta_time, channel, memory_map):
        """
        Creates a MIDI note event from a memory map.
        Args:
            delta_time (int): The delta time of the MIDI event.
            channel (int): The MIDI channel number (0-15).
            memory_map (mmap.mmap): Memory map object containing MIDI data.
        Returns:
            MIDINote: A new MIDI note event instance.
        Note:
            This method expects the memory map's current position to be at the start of
            note and velocity bytes. It will advance the memory map position by 2 bytes.
        """
        note = struct.unpack("B", memory_map.read(1))[0]
        velocity = struct.unpack("B", memory_map.read(1))[0]
        return cls(delta_time, channel, note, velocity)

@dataclass
class NoteOffEvent:
    """
    This class encapsulates the properties and parsing logic for MIDI Note Off messages,
    which signal the end of a note being played.
    Attributes:
        delta_time (int): The time delay before this event occurs.
        channel (int): The MIDI channel number (0-15).
        note (int): The MIDI note number (0-127).
        velocity (int): The release velocity of the note (0-127).
    """
    delta_time: int
    channel: int
    note: int
    velocity: int

    @classmethod
    def from_memory_map(cls, delta_time, channel, memory_map):
        """
        Creates a MIDI note event from a memory map.
        Args:
            delta_time (int): The delta time for this MIDI message
            channel (int): The MIDI channel number (0-15)
            memory_map (mmap.mmap): Memory mapped file object to read from
        Returns:
            MidiMessage: A new MIDI message instance constructed from the memory map data
        Reads 2 bytes from the memory map:
        - First byte: note number (0-127)
        - Second byte: velocity (0-127)
        """
        note = struct.unpack("B", memory_map.read(1))[0]
        velocity = struct.unpack("B", memory_map.read(1))[0]
        return cls(delta_time, channel, note, velocity)

@dataclass
class NotePressureEvent:
    delta_time: int
    channel: int
    note: int
    pressure: int

    @classmethod
    def from_memory_map(cls, delta_time, channel, memory_map):
        note = struct.unpack("B", memory_map.read(1))[0]
        pressure = struct.unpack("B", memory_map.read(1))[0]
        return cls(delta_time, channel, note, pressure)

@dataclass
class ControllerEvent:
    delta_time: int
    channel: int
    controller: int
    value: int

    @classmethod
    def from_memory_map(cls, delta_time, channel, memory_map):
        controller = struct.unpack("B", memory_map.read(1))[0]
        value = struct.unpack("B", memory_map.read(1))[0]
        return cls(delta_time, channel, controller, value)

@dataclass
class ProgramEvent:
    delta_time: int
    channel: int
    program: int

    @classmethod
    def from_memory_map(cls, delta_time, channel, memory_map):
        program = struct.unpack("B", memory_map.read(1))[0]
        return cls(delta_time, channel, program)

@dataclass
class ChannelPressureEvent:
    delta_time: int
    channel: int
    pressure: int

    @classmethod
    def from_memory_map(cls, delta_time, channel, memory_map):
        pressure = struct.unpack("B", memory_map.read(1))[0]
        return cls(delta_time, channel, pressure)

@dataclass
class PitchBendEvent:
    delta_time: int
    channel: int
    lsb: int
    msb: int

    @classmethod
    def from_memory_map(cls, delta_time, channel, memory_map):
        lsb = struct.unpack("B", memory_map.read(1))[0]
        msb = struct.unpack("B", memory_map.read(1))[0]
        return cls(delta_time, channel, lsb, msb)

# Only track events
@dataclass
class SequenceNumberEvent:
    delta_time: int
    sequence_number: int

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        sequence_number = struct.unpack(">H", memory_map.read(2))[0]
        return cls(delta_time, sequence_number)

@dataclass
class TextEvent:
    delta_time: int
    text: str

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        text = struct.unpack(f"{length}s", memory_map.read(length))[0].decode("latin-1")
        return cls(delta_time, text)

@dataclass
class CopyrightEvent:
    delta_time: int
    copyright: str

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        copyright = struct.unpack(f"{length}s", memory_map.read(length))[0].decode("latin-1")
        return cls(delta_time, copyright)

@dataclass
class TrackNameEvent:
    delta_time: int
    name: str

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        name = struct.unpack(f"{length}s", memory_map.read(length))[0].decode("latin-1")
        return cls(delta_time, name)

@dataclass
class InstrumentNameEvent:
    delta_time: int
    name: str

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        name = struct.unpack(f"{length}s", memory_map.read(length))[0].decode("latin-1")
        return cls(delta_time, name)

@dataclass
class LyricEvent:
    delta_time: int
    lyric: str

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        lyric = struct.unpack(f"{length}s", memory_map.read(length))[0].decode("latin-1")
        return cls(delta_time, lyric)

@dataclass
class MarkerEvent:
    delta_time: int
    marker: str

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        marker = struct.unpack(f"{length}s", memory_map.read(length))[0].decode("latin-1")
        return cls(delta_time, marker)

@dataclass
class CuePointEvent:
    delta_time: int
    cue_point: str

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        cue_point = struct.unpack(f"{length}s", memory_map.read(length))[0].decode("latin-1")
        return cls(delta_time, cue_point)

@dataclass
class ProgramNameEvent:
    delta_time: int
    name: str

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        name = struct.unpack(f"{length}s", memory_map.read(length))[0].decode("latin-1")
        return cls(delta_time, name)

@dataclass
class DeviceNameEvent:
    delta_time: int
    name: str

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        name = struct.unpack(f"{length}s", memory_map.read(length))[0].decode("latin-1")
        return cls(delta_time, name)

@dataclass
class MidiChannelPrefixEvent:
    delta_time: int
    prefix: int

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        prefix = struct.unpack("B", memory_map.read(1))[0]
        return cls(delta_time, prefix)

@dataclass
class MidiPortEvent:
    delta_time: int
    port: int

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        port = struct.unpack("B", memory_map.read(1))[0]
        return cls(delta_time, port)

@dataclass
class EndOfTrackEvent:
    delta_time: int

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        return cls(delta_time)

@dataclass
class TempoEvent:
    delta_time: int
    tempo: int

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        tempo = struct.unpack(">I", b"\x00" + memory_map.read(3))[0]
        return cls(delta_time, tempo)

@dataclass
class SmpteOffsetEvent:
    delta_time: int
    hours: int
    minutes: int
    seconds: int
    fps: int
    fractional_frames: int

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        hours = struct.unpack("B", memory_map.read(1))[0]
        minutes = struct.unpack("B", memory_map.read(1))[0]
        seconds = struct.unpack("B", memory_map.read(1))[0]
        fps = struct.unpack("B", memory_map.read(1))[0]
        fractional_frames = struct.unpack("B", memory_map.read(1))[0]
        return cls(delta_time, hours, minutes, seconds, fps, fractional_frames)

@dataclass
class TimeSignatureEvent:
    delta_time: int
    numerator: int
    denominator: int
    clocks_per_click: int
    thirty_second_per_24_clocks: int

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        numerator = struct.unpack("B", memory_map.read(1))[0]
        denominator = struct.unpack("B", memory_map.read(1))[0]
        clocks_per_click = struct.unpack("B", memory_map.read(1))[0]
        thirty_second_per_24_clocks = struct.unpack("B", memory_map.read(1))[0]
        return cls(delta_time, numerator, denominator, clocks_per_click,
                   thirty_second_per_24_clocks)

@dataclass
class KeySignatureEvent:
    delta_time: int
    flats_sharps: int
    major_minor: int

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        flats_sharps = struct.unpack("B", memory_map.read(1))[0]
        major_minor = struct.unpack("B", memory_map.read(1))[0]
        return cls(delta_time, flats_sharps, major_minor)

@dataclass
class SequencerEvent:
    delta_time: int
    data: bytes

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        data = struct.unpack(f"{length}s", memory_map.read(length))[0]
        return cls(delta_time, data)

@dataclass
class SysExEvent:
    delta_time: int
    data: bytes

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        data = struct.unpack(f"{length}s", memory_map.read(length))[0]
        return cls(delta_time, data)

@dataclass
class EscapeSequenceEvent:
    delta_time: int
    data: bytes

    @classmethod
    def from_memory_map(cls, delta_time, length, memory_map):
        data = struct.unpack(f"{length}s", memory_map.read(length))[0]
        return cls(delta_time, data)

# A brief description of the MIDI specification:
# - http://www.somascape.org/midi/tech/spec.html
# A brief description of the MIDI File specification:
# - http://www.somascape.org/midi/tech/mfile.html
# A MIDI Binary Template:
# - https://www.sweetscape.com/010editor/repository/files/MIDI.bt
# A description of Running Status:
# - http://midi.teragonaudio.com/tech/midispec/run.htm

meta_event_by_type = {
    0x00 : SequenceNumberEvent,
    0x01 : TextEvent,
    0x02 : CopyrightEvent,
    0x03 : TrackNameEvent,
    0x04 : InstrumentNameEvent,
    0x05 : LyricEvent,
    0x06 : MarkerEvent,
    0x07 : CuePointEvent,
    0x08 : ProgramNameEvent,
    0x09 : DeviceNameEvent,
    0x20 : MidiChannelPrefixEvent,
    0x21 : MidiPortEvent,
    0x2F : EndOfTrackEvent,
    0x51 : TempoEvent,
    0x54 : SmpteOffsetEvent,
    0x58 : TimeSignatureEvent,
    0x59 : KeySignatureEvent,
    0x7F : SequencerEvent,
}

channel_event_by_status = {
    0x80 : NoteOffEvent,
    0x90 : NoteOnEvent,
    0xA0 : NotePressureEvent,
    0xB0 : ControllerEvent,
    0xC0 : ProgramEvent,
    0xD0 : ChannelPressureEvent,
    0xE0 : PitchBendEvent,
}

def unpack_vlq(memory_map):
    total = 0
    while True:
        char = struct.unpack("B", memory_map.read(1))[0]
        total = (total << 7) + (char & 0x7F)
        if not char & 0x80: break
    return total

def parse_channel_event(delta_time, status, memory_map):
    channel = status & 0xF
    event_class = channel_event_by_status[status & 0xF0]
    event = event_class.from_memory_map(delta_time, channel, memory_map)
    if isinstance(event, NoteOnEvent) and event.velocity == 0:
        return NoteOffEvent(delta_time, channel, event.note, 0)
    return event

def parse_meta_event(delta_time, memory_map):
    event_type = struct.unpack("B", memory_map.read(1))[0]
    length = unpack_vlq(memory_map)
    event_class = meta_event_by_type[event_type]
    event = event_class.from_memory_map(delta_time, length, memory_map)
    return event

def parse_sys_ex_event(delta_time, status, memory_map):
    length = unpack_vlq(memory_map)
    if status == 0xF0:
        return SysExEvent.from_memory_map(delta_time, length, memory_map)
    elif status == 0xF7:
        return EscapeSequenceEvent.from_memory_map(delta_time, length, memory_map)

def parse_event(memory_map, parse_state):
    delta_time = unpack_vlq(memory_map)
    status = struct.unpack("B", memory_map.read(1))[0]

    if status & 0x80: parse_state.runningStatus = status
    else: memory_map.seek(-1, SEEK_CUR)

    running_status = parse_state.runningStatus
    if running_status == 0xFF:
        return parse_meta_event(delta_time, memory_map)
    elif running_status == 0xF0 or running_status == 0xF7:
        return parse_sys_ex_event(delta_time, running_status, memory_map)
    elif running_status >= 0x80:
        return parse_channel_event(delta_time, running_status, memory_map)

@dataclass
class MidiParseState:
    running_status: int = 0

def parse_events(memory_map):
    events = []
    parse_state = MidiParseState()
    while True:
        event = parse_event(memory_map, parse_state)
        events.append(event)
        if isinstance(event, EndOfTrackEvent): break
    return events

def parse_track_header(memory_map):
    identifier = memory_map.read(4).decode('latin-1')
    chunk_length = struct.unpack(">I", memory_map.read(4))[0]
    return chunk_length

@dataclass
class MidiTrack:
    events: List

    @classmethod
    def from_memory_map(cls, memory_map):
        chunk_length = parse_track_header(memory_map)
        events = parse_events(memory_map)
        return cls(events)

def parse_header(memory_map):
    identifier = memory_map.read(4).decode('latin-1')
    chunk_length = struct.unpack(">I", memory_map.read(4))[0]
    midi_format = struct.unpack(">H", memory_map.read(2))[0]
    tracks_count = struct.unpack(">H", memory_map.read(2))[0]
    ppqn = struct.unpack(">H", memory_map.read(2))[0]
    return midi_format, tracks_count, ppqn

def parse_tracks(memory_map, tracks_count):
    return [MidiTrack.from_memory_map(memory_map) for i in range(tracks_count)]

@dataclass
class MIDIFile:
    midi_format: int
    ppqn: int
    tempo: int
    tracks: List[MidiTrack]

    @classmethod
    def from_file(cls, file_path):
        with open(file_path, "rb") as f:
            memory_map = mmap.mmap(f.fileno(), 0, access = mmap.ACCESS_READ)
            midi_format, tracks_count, ppqn = parse_header(memory_map)
            tracks = parse_tracks(memory_map, tracks_count)
            memory_map.close()
            tempo = -1 # initialisation
            return cls(midi_format, ppqn, tempo, tracks)

@dataclass
class TempoEventRecord:
    time_in_ticks: int
    time_in_seconds: int
    tempo: int

class TempoMap:
    def __init__(self, midi_file):
        self.ppqn = midi_file.ppqn
        self.midi_format = midi_file.midi_format
        self.compute_tempo_tracks(midi_file)

    def compute_tempo_tracks(self, midi_file):
        tracks = midi_file.tracks
        if midi_file.midi_format == 1: tracks = tracks[0:1]
        self.tempo_tracks = [[] * len(tracks)]
        for track_index, track in enumerate(tracks):
            time_in_ticks = 0
            time_in_seconds = 0
            tempo_events = self.tempo_tracks[track_index]
            for event in track.events:
                time_in_ticks += event.delta_time
                time_in_seconds = self.time_in_ticks_to_seconds(track_index, time_in_ticks)
                if not isinstance(event, TempoEvent): continue
                tempo_events.append(TempoEventRecord(time_in_ticks, time_in_seconds, event.tempo))

    def time_in_ticks_to_seconds(self, track_index, time_in_ticks):
        track_index = track_index if self.midi_format != 1 else 0
        tempo_events = self.tempo_tracks[track_index]
        match_function = lambda event: event.time_in_ticks <= time_in_ticks
        matched_events = filter(match_function, reversed(tempo_events))
        tempo_event = next(matched_events, TempoEventRecord(0, 0, 500_000))
        microseconds_per_tick = tempo_event.tempo / self.ppqn
        seconds_per_tick = microseconds_per_tick / 1_000_000
        elapsed_seconds = (time_in_ticks - tempo_event.time_in_ticks) * seconds_per_tick
        return tempo_event.time_in_seconds + elapsed_seconds

# Notes:
# - It is possible for multiple consecutive Note On Events to happen on the same
#   channel and note number. The `numberOfNotes` member in NoteOnRecord represents
#   the number of such consecutive events. Note Off Events decrement that number
#   and are only considered when that number becomes 1.
# - The MIDI parser takes care of running-status Note On Events with zero velocity
#   so the code needn't check for that.

@dataclass
class NoteOnRecord:
    ticks: int
    time: float
    velocity: float
    number_of_notes: int = 1

class TrackState:
    def __init__(self):
        self.time_in_ticks = 0
        self.time_in_seconds = 0
        self.note_on_table = dict()

    def update_time(self, track_index, tempo_map, delta_time):
        self.time_in_ticks += delta_time
        self.time_in_seconds = tempo_map.time_in_ticks_to_seconds(track_index, self.time_in_ticks)

    def record_note_on(self, event):
        key = (event.channel, event.note)
        if key in self.note_on_table:
            self.note_on_table[key].number_of_notes += 1
        else:
            self.note_on_table[key] = NoteOnRecord(self.time_in_ticks, self.time_in_seconds,
                                                   event.velocity / 127)

    def get_corresponding_note_on_record(self, event):
        key = (event.channel, event.note)
        note_on_record = self.note_on_table[key]
        if note_on_record.number_of_notes == 1:
            del self.note_on_table[key]
            return note_on_record
        else:
            note_on_record.number_of_notes -= 1
            return None

def read_midi_file(path):
    midi_file = MIDIFile.from_file(path)
    tempo_map = TempoMap(midi_file)
    # set tempo to tempo value if fixe for all midi_file
    if len(tempo_map.tempo_tracks) == 1:
        tempo = tempo_map.tempo_tracks[0][0].tempo
    else:
        tempo = 0
    midi_file.tempo = tempo
    working_tracks = []
    file_tracks = midi_file.tracks if midi_file.midi_format != 1 else midi_file.tracks[1:]
    track_index_used = 0
    for track_index, track in enumerate(file_tracks):
        notes = []
        notes_used = []
        track_name = ""
        track_state = TrackState()
        min_note = 1000
        max_note = 0
        min_velo = 127
        max_velo = 0
        min_duration_in_ticks = 1000000
        for event in track.events:
            track_state.update_time(track_index, tempo_map, event.delta_time)
            if isinstance(event, TrackNameEvent):
                track_name = event.name
            elif isinstance(event, NoteOnEvent):
                track_state.record_note_on(event)
                min_note = min(min_note, event.note)
                max_note = max(max_note, event.note)
                min_velo = min(min_velo, event.velocity)
                max_velo = max(max_velo, event.velocity)
                if event.note not in notes_used:
                    notes_used.append(event.note)
            elif isinstance(event, NoteOffEvent):
                note_on_record = track_state.get_corresponding_note_on_record(event)
                if note_on_record is None: continue
                start_time = note_on_record.time
                velocity = note_on_record.velocity
                end_time = track_state.time_in_seconds
                notes.append(MIDINote(event.channel, event.note, start_time, end_time, velocity))
                min_duration_in_ticks = min(min_duration_in_ticks,
                                            track_state.time_in_ticks - note_on_record.ticks)
        if bool(notes_used):
            working_tracks.append(MIDITrack(track_name, track_index_used, min_note,
                                  max_note, min_velo, max_velo, notes, notes_used))
            track_index_used += 1
    if midi_file.midi_format == 0:
        track_index_used = 0
        tracks = []
        for channel in range(16):
            notes = []
            notes_used = []
            min_note = 1000
            max_note = 0
            min_velo = 127
            max_velo = 0
            for note in working_tracks[0].notes:
                if note.channel == channel:
                    notes.append(note)
                    min_note = min(min_note, note.note_number)
                    max_note = max(max_note, note.note_number)
                    min_velo = min(min_velo, note.velocity)
                    max_velo = max(max_velo, note.velocity)
                    if note.note_number not in notes_used:
                        notes_used.append(note.note_number)
            if bool(notes_used):
                tracks.append(MIDITrack(f"{working_tracks[0].name}-ch{channel}", track_index_used,
                                        min_note, max_note, min_velo, max_velo, notes, notes_used))
                track_index_used += 1
    else:
        tracks = working_tracks

    return midi_file, tempo_map, tracks
