# M2B - MIDI To Blender

A blender extension that generates animated 3D visualizations from MIDI files in Blender.

## Overview

M2B converts MIDI music data into various 3D animated visualizations in Blender. It can create several visualization types including bar graphs, note strips, waterfalls, fireworks, and fountains.

## Features

- Multiple visualization types:
  - BarGraph - Creates one cube per note, animated in sync with the music
  - Notes Strip - Creates a piano roll style visualization
  - Waterfall - Animated waterfall effect over note strips
  - Fireworks - Particle-based firework effects
  - Fountain - Fountain particle simulation
  - Lightshow - Animated Lights
  
- Supports multiple MIDI file formats:
  - Format 0 (single track)
  - Format 1 (multiple tracks)
  - Format 2 (multiple tracks)

- Real-time animation synchronized with:
  - Note on/off events
  - Note velocity 
  - Track colors
  - MIDI timing

- Integration with Blender:
  - Custom node materials
  - Particle systems
  - Geometry nodes
  - Audio sync with MP3
  - Compositing effects

## Requirements

- Blender 4.0 or higher
- Python 3.x
- MIDI files (.mid)
- Optional: Corresponding MP3 audio files

## License

GNU GPL v3
See LICENSE file for details.

## Author

Patrick M (Patochun)
- Email: ptkmgr@gmail.com
- YouTube: https://www.youtube.com/channel/UCCNXecgdUbUChEyvW3gFWvw

## Version

Current version: 1.0 (2025)
