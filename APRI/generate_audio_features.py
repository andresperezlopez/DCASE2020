"""
generate_audio_features.py

For each audio file, the script generates a set of audio features.

The output values are stored in a folder `oracle_mono_signals/audio_features` within `params['dataset_dir']`.
Inside it, a folder is created for each event class, and a single file in created for each event
keeping the name (number) of the original audio file.

"""
from baseline import parameter
import essentia
import essentia.standard as es
import os
import numpy as np
from baseline.cls_feature_class import create_folder

def get_feature_list():
    return [
         'lowlevel.barkbands.dmean',
         'lowlevel.barkbands.mean',
         'lowlevel.barkbands.var',
         'lowlevel.erbbands.dmean',
         'lowlevel.erbbands.mean',
         'lowlevel.erbbands.var',
         'lowlevel.gfcc.mean',
         'lowlevel.melbands.dmean',
         'lowlevel.melbands.mean',
         'lowlevel.melbands.var',
         'lowlevel.mfcc.mean',
         'lowlevel.spectral_contrast_coeffs.dmean',
         'lowlevel.spectral_contrast_coeffs.mean',
         'lowlevel.spectral_contrast_coeffs.var',
         'lowlevel.spectral_contrast_valleys.dmean',
         'lowlevel.spectral_contrast_valleys.mean',
         'lowlevel.spectral_contrast_valleys.var',
         'rhythm.beats_loudness_band_ratio.dmean',
         'rhythm.beats_loudness_band_ratio.mean',
         'rhythm.beats_loudness_band_ratio.var',
         'tonal.hpcp.dmean',
         'tonal.hpcp.mean',
         'tonal.hpcp.var',
         'tonal.chords_histogram',
         'tonal.thpcp',
         'lowlevel.pitch_salience.dmean',
         'lowlevel.pitch_salience.mean',
         'lowlevel.pitch_salience.var',
         'lowlevel.silence_rate_20dB.dmean',
         'lowlevel.silence_rate_20dB.mean',
         'lowlevel.silence_rate_20dB.var',
         'lowlevel.silence_rate_30dB.dmean',
         'lowlevel.silence_rate_30dB.mean',
         'lowlevel.silence_rate_30dB.var',
         'lowlevel.silence_rate_60dB.dmean',
         'lowlevel.silence_rate_60dB.mean',
         'lowlevel.silence_rate_60dB.var'
    ]

def get_class_name_dict():
    return {
        0: 'alarm',
        1: 'crying_baby',
        2: 'crash',
        3: 'barking_dog',
        4: 'running_engine',
        5: 'female_scream',
        6: 'female_speech',
        7: 'burning_fire',
        8: 'footsteps',
        9: 'knocking_on_door',
        10:'male_scream',
        11:'male_speech',
        12:'ringing_phone',
        13:'piano'
    }

params = parameter.get_params()
event_type= get_class_name_dict().values()
data_folder_path = os.path.join(params['dataset_dir'], 'oracle_mono_signals/') # path to audios
audio_features_output_path= os.path.join(data_folder_path,'audio_features/')

# Compute each audio_file generated by "generate_audio_from_annotations.py" and generates audio_features using MusicExtractor
for event in event_type:
    create_folder(os.path.join(audio_features_output_path,event))
    audio_path= os.path.join(data_folder_path,event) #path to file
    for audio in os.scandir(audio_path):
        print("Extracting features from ",event+' ' + audio.name)
        features, features_frames = es.MusicExtractor(lowlevelFrameSize=4096,
                                              lowlevelHopSize=2048,
                                              tonalFrameSize=4096,
                                              tonalHopSize=2048,
                                              rhythmStats = ["mean", "var", "dmean"],
                                              lowlevelStats = ["mean", "var", "dmean"],
                                             )(audio.path)
        feature_list=get_feature_list()
        audio_features=[]
        print("Converting to array...")
        for feature in feature_list:
            x=features[feature]
            if type(x) is float:
                x=np.array(x)
                y=[x]
            else:
                y=x.tolist()
            audio_features=audio_features+y
        audio_features=np.array(audio_features)
        # Save arrays

        file_name = os.path.splitext(audio.name)[0]
        print("Saving file ",event+file_name+'.npy')
        np.save(os.path.join(audio_features_output_path, event, file_name+'.npy'), audio_features)



