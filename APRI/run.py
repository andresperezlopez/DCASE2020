"""
run.py

Main SELD loop
Execute the full analysis, from audio files to result csv files, for a given preset configuration.
In dev mode, compute evaluation metrics too.

Options:
- write_file (bool): Actually generate output files and folders
- plot (bool): Plot the annotations for each file (not recommended on the whole dataset)
- quick (bool): Perform analysis only on a manually given subset, useful for fast iterative development
"""

import datetime
from APRI.localization_detection import *
from APRI.compute_metrics import compute_metrics
from APRI.event_class_prediction import *
import time

# %% Parameters

# preset = 'particle'
# preset = '4REPORT'
preset = '4EVALUATION_PARTICLE'
write = True
plot = False
quick = False

params = parameter.get_params(preset)
mode = params['mode']
data_folder_path = os.path.join(params['dataset_dir'], 'foa_'+mode) # path to audios
gt_folder_path = os.path.join(params['dataset_dir'], 'metadata_'+mode) # path to annotations
this_file_path = os.path.dirname(os.path.abspath(__file__))
result_folder_path = os.path.join(this_file_path, params['results_dir'], preset)
if quick:
    result_folder_path += '_Q!' # save quick results in separated folders, so that eval.py can benefit from it
create_folder(result_folder_path)

# numbers
M = 4
N = 600
fs = params['fs']
window = params['window']
window_size = params['window_size']
window_overlap = params['window_overlap']
nfft = params['nfft']
D = params['D'] # decimate factor
frame_length = params['label_hop_len_s']

beamforming_mode = params['beamforming_mode']

# Dataset
all_audio_files = [f for f in os.listdir(data_folder_path) if not f.startswith('.')]
quick_audio_files = ['fold1_room1_mix007_ov1.wav',
                     'fold2_room1_mix007_ov1.wav',
                     'fold3_room1_mix007_ov1.wav',
                     'fold4_room1_mix007_ov1.wav',
                     'fold5_room1_mix007_ov1.wav',
                     'fold6_room1_mix007_ov1.wav',
                     'fold1_room1_mix037_ov2.wav',
                     'fold2_room1_mix037_ov2.wav',
                     'fold3_room1_mix037_ov2.wav',
                     'fold4_room1_mix037_ov2.wav',
                     'fold5_room1_mix037_ov2.wav',
                     ]


# %% Analysis

start_time = time.time()

print('                                              ')
print('-------------- PROCESSING FILES --------------')
print('Folder path: ' + data_folder_path              )
print('Pipeline: ' + params['preset_descriptor']      )
if quick:
    print('Quick!')

if quick:
    audio_files = quick_audio_files
else:
    audio_files = all_audio_files
for audio_file_idx, audio_file_name in enumerate(audio_files):

    st = datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')
    print("{}: {}, {}".format(audio_file_idx, st, audio_file_name))

    ############################################
    # Preprocess: prepare file output in case
    if write:
        csv_file_name = (os.path.splitext(audio_file_name)[0]) + '.csv'
        csv_file_path = os.path.join(result_folder_path, csv_file_name)
        # since we always append to the csv file, make a reset on the file
        if os.path.exists(csv_file_path):
            # os.remove(csv_file_path)
            continue # SKIP EXISTING FILES!

    ############################################
    # Open file
    audio_file_path = os.path.join(data_folder_path, audio_file_name)
    b_format, sr = sf.read(audio_file_path)

    # Get spectrogram
    stft = compute_spectrogram(b_format, sr, window, window_size, window_overlap, nfft, D)

    ############################################
    # Localization and detection analysis: from stft to event_list
    ld_method_string = params['ld_method']
    ld_method = locals()[ld_method_string]
    if ld_method_string == 'ld_oracle':
        ld_method_args = [audio_file_name, gt_folder_path] # need to pass the current name to get the associated metadata file
    else:
        ld_method_args = params['ld_method_args']
    event_list = ld_method(stft, *ld_method_args)

    ############################################
    # Get monophonic estimates of the event, and predict the classes
    num_events = len(event_list)
    for event_idx in range(num_events):
        event = event_list[event_idx]
        mono_event = get_mono_audio_from_event(b_format, event, beamforming_mode, fs, frame_length)

        # Predict
        class_method_string = params['class_method']
        class_method = locals()[class_method_string]
        class_method_args = params['class_method_args']
        class_idx = class_method(mono_event, *class_method_args)
        #class_idx = class_method(temp_file_name, *class_method_args)
        event.set_classID(class_idx)
        ############################################
        # Postprocessing:
        process_event=True
        try:
            event_filter = params['event_filter_activation']
        except:
            event_filter = False  # default True, so it works also when no event_filter
        if event_filter:
            event_filter_method_string = params['event_filter_method']
            event_filter_method = locals()[event_filter_method_string]
            event_filters_method_args = params['event_filter_method_args']
            process_event = event_filter_method(event, *event_filters_method_args)

        ############################################
        # Generate metadata file from event
        if write and process_event:
            event.export_csv(csv_file_path)


    ############################################
    # Plot results
    if plot:
        plot_results(csv_file_path, params)


print('-------------- PROCESSING FINISHED --------------')
print('                                                 ')


# %% OPTIONAL EVAL

if mode == 'dev':
    print('-------------- COMPUTE DOA METRICS --------------')
    compute_metrics(gt_folder_path, result_folder_path, params)


# %%
end_time = time.time()

print('                                               ')
print('-------------- PROCESS COMPLETED --------------')
print('                                               ')
print('Elapsed time: ' + str(end_time-start_time)      )
