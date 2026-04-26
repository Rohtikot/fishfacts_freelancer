import pandas as pd
import matplotlib.pyplot as plt
import folium
from plotting.utils import get_speed_color
from plotting.plot import plot_vessel_track
from shapely.ops import unary_union, polygonize
from resample.resample_fix_time_gaps import resample_with_interpolation
import geopandas as gpd




def main():
    pd.set_option('display.width', None)
    pd.set_option('display.max_columns', None)

    df = pd.read_parquet('ais_data/ais_data_for_all_vessels_resampled.parquet')
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, format='%Y-%m-%d %H:%M%:%S')

    df = df[
        (df['flag'] == 'Faroe Islands')
        & (df['timestamp'].dt.year == 2024)
    ]

    df['year'] = df['timestamp'].dt.year

    for vessel, group in df.groupby(['year', 'vessel_name']):

        print(group)
        m = folium.Map(location=(48.32, -45.46), tiles='cartodb dark_matter', zoom_start=5)
        m = plot_area_3m(m)
        m = plot_vessel_track(group, m, vessel[0])
        fishing_speed = group[group['speed'] <= 6]

        for _, row in fishing_speed.iterrows():
            folium.CircleMarker(
                location=(row['latitude'], row['longitude']),
                color=get_speed_color(row['speed']),
                weight=0,
                fill=True,
                opacity=0.5,
                fill_color=get_speed_color(row['speed']),
                popup=f'{vessel}\nSpeed: {row['speed']:.01f} knots'
            ).add_to(m)
        m.save(f'specific_plot/{vessel[0]}-{vessel[1]}.html')
    print(df.head())
    print(df.dtypes)


if __name__ == '__main__':
    main()
