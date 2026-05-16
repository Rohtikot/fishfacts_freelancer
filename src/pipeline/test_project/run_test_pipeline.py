from src.data.zones import load_polygons
from src.pipeline.runner import Pipeline
import pandas as pd
import yaml

from pathlib import Path

pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)

ROOT = Path(__file__).parents[3]
CONFIG_PATH = ROOT / 'src' / 'pipeline' / 'test_project' / 'pipeline_config.yaml'
POLYGONS_PATH = ROOT / 'data' / 'zones' / 'eez' / 'World_EEZ_v12_20231025'
DATA_PATH = ROOT / 'data' / 'ais'

# load config
config = yaml.safe_load(open(CONFIG_PATH))

for i in config['steps']:
    print(i)
print('\n\n')
# load zones
eez = load_polygons(POLYGONS_PATH, layer='eez_v12')

pipeline = Pipeline(
    steps=config['steps'],
    context={'polygons': eez}
)

df = pd.read_parquet(DATA_PATH / 'vessel_20.parquet')
print(df.head(3))
res_df = pipeline.run(df)
import matplotlib.pyplot as plt
fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
ax1.plot(res_df['timestamp'], res_df['speed_calc'], label='Speed calc')
ax2.plot(df['timestamp'], df['speed'], label='Speed')
ax2.plot(res_df['timestamp'], res_df['speed_calc'], label='Speed calc', linestyle='--', alpha=0.8, color='red')
plt.legend()
plt.show()
print(res_df)
