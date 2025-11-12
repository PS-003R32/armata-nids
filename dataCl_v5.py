import pandas as pd
import numpy as np
import glob
import os
from sklearn.utils import shuffle

# i have reduced the features as the zero w might not process much data becaus of the 1ghz cpu, 
#but if you are using a pi 4,5 or similar models you can add more features and add more sample data to train your model. 
#If you do then you have to change the features count in the arduino file, i have marked the line.
SELECTED_FEATURES = [
    'Destination Port',
    'Flow Duration',
    'Total Fwd Packets',
    'Total Backward Packets',
    'Total Length of Fwd Packets',
    'Total Length of Bwd Packets',
    'Flow IAT Mean',
    'SYN Flag Count',
    'PSH Flag Count',
    'ACK Flag Count',
    'Label'
]

N_BENIGN_SAMPLES = 250000
N_ATTACK_SAMPLES_PER_TYPE = 200000

OUTPUT_FILENAME = 'preprocessed_nids_data.csv'

def clean_data(df):
    df_clean = df.copy()
    df_clean.replace([np.inf, -np.inf], np.nan, inplace=True)
    df_clean.dropna(inplace=True)
    return df_clean

def preprocess():
    csv_files = glob.glob('*.csv') # make sure the script is in the same folder as the CSVs or change the pathg
    if not csv_files:
        print("Error: No CSV files found in this directory.")
        return

    print(f"Found {len(csv_files)} CSV files. Processing...")

    all_dfs = []
    for f in csv_files:
        if f == OUTPUT_FILENAME or f == 'preprocess.py':
            continue
        
        print(f"Reading {f}...")
        try:
            df = pd.read_csv(f)
            df.columns = df.columns.str.strip()
            missing_cols = [col for col in SELECTED_FEATURES if col not in df.columns]
            if missing_cols:
                continue
            df_selected = df[SELECTED_FEATURES]
            df_cleaned = clean_data(df_selected)
            all_dfs.append(df_cleaned)
            print(f"Successfully processed and added {f}")
        except Exception as e:
            print(f"Warning: Could not process {f}. Error: {e}")

    if not all_dfs:
        print("Error: No data was successfully loaded. Please check your CSV files and permissions.")
        return
    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df['Label'] = combined_df['Label'].str.strip()
    benign_df = combined_df[combined_df['Label'] == 'BENIGN']
    attack_df = combined_df[combined_df['Label'] != 'BENIGN']

    benign_sampled = benign_df.sample(n=N_BENIGN_SAMPLES, 
                                      random_state=42, 
                                      replace=(len(benign_df) < N_BENIGN_SAMPLES))

    attack_sampled = attack_df.groupby('Label').apply(
        lambda x: x.sample(n=N_ATTACK_SAMPLES_PER_TYPE, 
                           random_state=42, 
                           replace=(len(x) < N_ATTACK_SAMPLES_PER_TYPE))
    ).reset_index(drop=True)
    
    final_df = pd.concat([benign_sampled, attack_sampled])
    final_df = shuffle(final_df, random_state=42)

    cols = [c for c in SELECTED_FEATURES if c != 'Label'] + ['Label']
    final_df = final_df[cols]
    final_df.to_csv(OUTPUT_FILENAME, index=False)

if __name__ == "__main__":
    preprocess()
