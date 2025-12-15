from datasets import load_dataset
import pandas as pd
import numpy as np

# Load dataset
print("Loading dataset...")
raw_datasets = load_dataset("8Opt/vietnamese-summarization-dataset-0001")

print(f"\n=== DATASET INFO ===")
print(f"Available splits: {list(raw_datasets.keys())}")

for split in raw_datasets.keys():
    print(f"\n{split.upper()} SET:")
    print(f"  Number of samples: {len(raw_datasets[split])}")
    print(f"  Columns: {raw_datasets[split].column_names}")

# Normalize column names
def normalize_columns(dataset):
    mapping = {
        "document": "input_text", 
        "summary": "target_text", 
        "content": "input_text", 
        "abstract": "target_text"
    }
    for old, new in mapping.items():
        if old in dataset.column_names:
            dataset = dataset.rename_column(old, new)
    return dataset

for split in raw_datasets.keys():
    raw_datasets[split] = normalize_columns(raw_datasets[split])

# Filter null
raw_datasets = raw_datasets.filter(
    lambda x: x['input_text'] is not None and x['target_text'] is not None
)

print(f"\n=== AFTER FILTERING NULL ===")
for split in raw_datasets.keys():
    print(f"{split}: {len(raw_datasets[split])} samples")

# Convert to pandas for analysis
def count_words(text):
    return len(str(text).split())

all_data = []
for split in raw_datasets.keys():
    df_split = raw_datasets[split].to_pandas()
    df_split['split'] = split
    all_data.append(df_split)

df = pd.concat(all_data, ignore_index=True)

# Calculate lengths
df['input_len'] = df['input_text'].apply(count_words)
df['target_len'] = df['target_text'].apply(count_words)
df['compression_ratio'] = df['target_len'] / df['input_len']

print(f"\n=== LENGTH STATISTICS ===")
print(f"\nTotal samples: {len(df)}")
print(f"\nInput length (words):")
print(df['input_len'].describe(percentiles=[0.5, 0.9, 0.95, 0.99]))

print(f"\nTarget length (words):")
print(df['target_len'].describe(percentiles=[0.5, 0.9, 0.95, 0.99]))

print(f"\nCompression ratio:")
print(df['compression_ratio'].describe(percentiles=[0.5, 0.9, 0.95, 0.99]))

# By split
print(f"\n=== BY SPLIT ===")
for split in df['split'].unique():
    split_df = df[df['split'] == split]
    print(f"\n{split.upper()}:")
    print(f"  Samples: {len(split_df)}")
    print(f"  Avg input: {split_df['input_len'].mean():.1f} words")
    print(f"  Avg target: {split_df['target_len'].mean():.1f} words")
    print(f"  Avg compression: {split_df['compression_ratio'].mean():.3f}")

# Sample some examples
print(f"\n=== SAMPLE EXAMPLES ===")
for i in range(min(3, len(df))):
    print(f"\nExample {i+1}:")
    print(f"Input ({df['input_len'].iloc[i]} words): {df['input_text'].iloc[i][:200]}...")
    print(f"Target ({df['target_len'].iloc[i]} words): {df['target_text'].iloc[i][:150]}...")