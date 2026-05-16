import pandas as pd
from src.db.vessels import get_vessels_all_to_dataframe
from src.db.model import VesselType

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

type_names = {
    VesselType.PELAGIC: "Pelagic",
    VesselType.FREEZING_TRAWLER: "Freezing trawler",
    VesselType.TRAWLER: "Trawler",
    VesselType.LONG_LINER: "Long liner",
    VesselType.CRABS_AND_SHELLFISH: "Crabs & shellfish"
}

vessels = get_vessels_all_to_dataframe()
vessels = vessels[
        vessels['vessel_type_id'].isin([
            VesselType.PELAGIC,
            VesselType.FREEZING_TRAWLER,
            VesselType.TRAWLER,
            VesselType.LONG_LINER,
            VesselType.CRABS_AND_SHELLFISH
        ])
    ].copy()


vessels['vessel_type'] = vessels['vessel_type_id'].map(type_names)

vessels['size_group'] = vessels['length_overall'].apply(
    lambda x: '>=25m' if pd.notna(x) and x >= 25 else '<25m'
)

print(vessels.head(5))
grouped = (
    vessels.groupby(['vessel_type', 'size_group'])
    .size()
    .reset_index(name='count')
)
print(grouped)
pivot = grouped.pivot_table(index='vessel_type', columns='size_group', values='count').fillna(0)
pivot.loc['Total'] = pivot.sum()
print(pivot)


done_vessels = pd.read_csv('../../../Projects/elsalvador26/vessel_scan_status.csv')
done_vessels = done_vessels[(done_vessels['checked']) & (done_vessels['in_zone'])]
print(done_vessels)