import pandas as pd

def resample_segment(df_segment, freq='15min'):
    df = df_segment.sort_values('timestamp').set_index('timestamp')

    # Create target grid
    grid = pd.date_range(
        start=df.index.min(),
        end=df.index.max(),
        freq=freq
    )

    # Combine original timestamps + grid
    combined_index = df.index.union(grid)

    # Reindex to combined index
    df = df.reindex(combined_index)

    # Interpolate on full timeline (this is the critical step)
    df['latitude'] = df['latitude'].interpolate(method='time')
    df['longitude'] = df['longitude'].interpolate(method='time')

    # Now sample ONLY the grid
    df = df.loc[grid]

    # Fill vessel_id (safe within segment)
    df['vessel_id'] = df['vessel_id'].ffill()

    return df.reset_index().rename(columns={'index': 'timestamp'})
