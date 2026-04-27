# Analysis Pipeline Neuropixel Data

Sounds involved:
- 101 - 40 Hz
- 102 - 1 Click
- 400 - 600 - DRCs
- 1300 - White Noise
- 1401, 1402, 1403 - Vocals

### The general order of things:
The flow is as follows:
Preprocessing APs -> Spike Sorting -> Syncing all times -> 
Curation (Manual/Automatic) -> Labeling -> Sync video data -> Plots

#### Files needed for analysis and plots:
- Spikes times
- Spikes info
- TTL times
- TTL labels
- LFPs data (can be read using TTL times)
- LED time vec
- location_COM
- Sleep/Wake labels

#### Data structures:
- LFPs Database - Big Pandas DataFrame with the following fields
  - Date
  - InjectionType
  - SoundType (7 Sounds)
  - Channel
  - LFPs params (by trials (Latency, Amplitude, Average Response))
    - All
    - Wake Trials
    - Sleep Trials
    - First 30 mins
    - Last 30 mins

#### Plots:
- LFP
  - LFP time (specific SoundType, specific trials)
    - All channels - Average response across picked trials
    - Single channel - Response across trials average on top
  - LFPs params - Scatter plots
    - Scatter Latency vs Amplitude - Grouping Trials
    - Scatter Latency vs Amplitude - Grouping Date
    - Scatter Latency vs Amplitude - Grouping SoundType
    - Scatter Latency vs Amplitude - Grouping InjectionType
    - Scatter Latency vs Amplitude - Grouping Channel
- AP
  - AP time (specific SoundType, specific trials)
    - Raster Plot
    - Color by cluster
    - PSTH on top
  - AP Cluster analysis

### Functions:

- Spike Sorting
    - 'APs_Preprocess_SpikeSorting.ipynb'
        - Reads the data from the SPIKEGLX path
        - Shows the probe layout
        - Preprocess the recording (cleans it up and removes bad channels)
        - Saves to 'path/preprocess'
    - 'APs_SpikeSorting.ipynb'
        - Reads 'path/preprocess'
        - Checks for spiking activity and drift
            - Check noise levels
            - Detect and localize peaks
            - Check for Drift
        - Run Spike sorting (returns **spike times** with **clusters** and **info**)
    - 'APs_PostProcessing_QualityMetrics_Curation.ipynb'
      - Post-processing
      - Quality metrics
      - Save to disk with report
      - Manual Curation with SortingView
- Manual Curation and Labeling
    - Either use **Sortingview** (code in 'APs_SpikeSorting' notebook) or **Phy** (code in 'Script for Phy')
      - [ ] I want to try to move to sortingview since it is faster
      - [ ] I want to do the curation in the code using the Quality Metrics before I do labeling and curation
- Syncing spike times and TTL events to LFP clock
    - 'All_SyncDatastreams.ipynb'
      - Read 3 clock signals for syncing
        - NI clock
        - AP clock
        - LFP clock
      - Read TTL times and TTL labels (2 arrays)
      - Save all 5 arrays in text files
    - 'Tprime' - code in 'script for Tprime'
        - Use 3 sync signals and 1 TTL times
        - Use spike times from spike sorting
        - Run Tprime command to sync all 5 signals
- Video extraction and analysis
  - 'VIDs_Analyze_and_Export_Vecs.py'
    - Read video of experiment
    - Rotate and crops the cage area
    - Picks the LED coordinates
    - Filters the mouse head-stage based on the color of the sticker
    - Gets mouse location based on the COM of the sticker
    - Returns LED_info, Location_COM, first frame
  - 'VIDs_SyncVidWithTTL.ipynb'
    - Read LED_info, Location_COM, first frame
    - Read TTL_events and time vecs
    - Sync TTL_events with LED_info using convolution
    - Returns LED_info, Location_COM, first frame, LED_time_vec



