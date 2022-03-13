# StimMusic - Music + GVS

Experience music and vestibular stimulation in sync. Artists can write music with vestibular stimulation channel using a Digital Audio Workstation (DAW) plugin Virtual Studio Technology (VST). A 4-electrode GVS setup allows for stimulation of yaw, pitch, and roll vestibular experience, at various intensities, in sync with music.

## Safety

Nominal: 0 - 4mA @ 9V
Max: 4mA @ 9V

Proper system should have current limiter! Better, multiple redundant current limiter! Don't connect to mains, use a battery!

## Install + Setup

Ubuntu 20 or Mac

Run ESP32s with GVS firmware and hardware setup, GVS to VST Python backend at VST_to_GVS_server_bridge_python, open VST in new track in DAW. Run the steps below to setup each component.


### Backend
1. Setup and activate virtual environment
2. Setup Youtube-dlc globally:
```
sudo wget https://github.com/blackjack4494/yt-dlc/releases/latest/download/youtube-dlc -O /usr/local/bin/youtube-dlc
sudo chmod a+rx /usr/local/bin/youtube-dlc
```
3. Install requirements:
`pip3 install -r requirements.txt`

### Firmware

1. Install Visual Studio Code. `sudo snap install code --classic`
2. Setup Platform IO in visual studio code.
3. Open ./firmware in PlatformIO
4. Flash onto ESP32s with GVS hardware connected.

### VST

1. Install Reaper of Ableton (DAW)
2. Connect MIDI keyboard to DAW
3. Build VST for your system.
4. (LINUX) - see below
5. Install VST in DAW
6. Run VST on track Midi keyboard input

##### Linux setup:

1. Install linux low latency kernel
2. Install JACK: `sudo apt-get install jackd2 qjackctl`
3. Configure JACK to use low latency - https://jackaudio.org/faq/linux_rt_config.html
4. Install m2jmidid `sudo apt-get install a2jmidid`
5. In `qjackctl`, Go to "Setup" -> Set Midi Driver to "seq" -> "Options (tab)" -> "Startup after execute" line: `pacmd set-default-sink jack_out; a2jmidid -e &`
6. Check qjackctl "Connections" -> Midi and ensure Midi keyboard is there.
7. Start JACK -> qjackctl -> Start
8. Set Reaper to use JACK as Audio Device ("Ctrl-P" -> Audio Device -> Set as JACK)
9. Add midi keyboard in reaper.
10. Run the GVS to VST backend server

## Electrode Placement

2 seperate current pathways, so that current doesn't go across the forehead.
   - "Because SDAS and ODAS are applied using two current stimulators (A+/- and B+/-), a part of current emitted from anode A+ may be received by cathode B- when ground-sharing circuits are used. Then, current might not flow as we intended. Therefore, we used isolated current stimulators that were driven by a different battery." 

Each electrode must be able to be cathod or anode.

1. Left mastoid.
2. Right mastoid
3. Left temple
4. Right temple

Ensure there is no current flow from 3 to 4!

## Electrical

3 isolated bipolar circuits, in order to show ensure current flows as expected.

1. Mastoid-mastoid
2. Left mastoid - left temple
3. Right mastoid - right temple

## Subjective Experience 

Yaw, pitch, roll are the primary colors of the vestibular system.

How can we make it feel like we're flying up? Or dropping into the ground? Or accelerating forward so we are pushed back into our chair?

Left roll - 1 cathode, 2 anode 
Right roll - 1 anode, 2 cathod

Front pitch - 1 anode, 3 cathode, 2 anode, 4 cathode
Back pitch - 1 cathod, 3 anode, 2 cathode, 3 anode

Left yaw - 1 cathode, 2 anode, 3 anode, 4 cathode
Right yaw - 1 anode, 2 cathode, 3 cathode, 4 anode

## References

GVS Electrode placement pathways and associated subjective experience: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4426693/
