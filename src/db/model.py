import decimal
import json
from abc import ABC
from datetime import datetime
from enum import IntEnum

import pandas as pd


def _measurement_unit_to_name(unit: str) -> str:
    match unit:
        case None:
            result = None
        case 'CUBIC_METERS':
            result = 'm3'  # u"\u33A5"
        case 'TONNS':
            result = 't'
        case _:
            raise Exception(f'Unknown measurement unit: {unit}')
    return result


class VesselType(IntEnum):
    FISHING_VESSEL = 1
    PELAGIC = 2
    TRAWLER = 3
    FREEZING_TRAWLER = 4
    LONG_LINER = 5
    CRABS_AND_SHELLFISH = 6
    SEALS = 7
    KRILL = 8
    TUNA = 9
    COAST = 10
    CARGO = 11
    PROCESSING_VESSEL = 12
    RESEARCH_VESSEL = 13
    COAST_GUARD = 14
    WORKING_BOAT = 15
    FLOATING_PLATFORM = 16
    SERVICE_VESSEL = 17
    HARVESTING = 18
    WELLBOAT = 19
    FEEDING_CARRIER = 20
    OIL_TANKER = 21
    ICEBRAKER = 22
    NEW_BUILDING_FF = 23
    OTHER = 24
    OFFSHORE = 25
    NEW_BUILDING_AF = 26
    ENSILAGE = 27
    COMBINED_SEINE_TRAWLER = 28
    COAST_20M = 29
    BULK = 30
    REEFER = 31
    FERRY = 32
    CRUISE = 33
    GAS_TANKER = 34
    SUPPLY = 35
    PLATFORM = 36
    WINDMILL = 37
    SSV = 38
    MULTIPURPOSE = 39
    DRILL_VESSEL = 40
    TUGBOAT = 41
    SAR = 42
    CARGO_AND_TRANSPORT = 43
    SUPPORT_SERVICE_AND_OTHER = 44
    AQUACULTURE = 45


HarvestingVesselTypes = [VesselType.HARVESTING, VesselType.WELLBOAT, VesselType.ENSILAGE]
ServiceVesselTypes = [VesselType.FEEDING_CARRIER, VesselType.WORKING_BOAT, VesselType.SERVICE_VESSEL]
AquaCultureVesselTypes = HarvestingVesselTypes + ServiceVesselTypes

wellboat_load_ratio = 0.67
harvester_load_ratio = 0.67


class Vessel:
    def __init__(self,
                 id: int,
                 name: str,
                 imo: str,
                 flag: str,
                 flag_name: str,
                 build_year: int,
                 vessel_type_id: int,
                 vessel_type: str,
                 length_overall: int,
                 gross_tonnage: int,
                 beam: decimal,
                 engine_model: str,
                 engine_power: int,
                 designer_name: str,
                 yard_name: str,
                 vessel_status_id: int,
                 nettotons: float,
                 bruttotons: float,
                 history: pd.DataFrame,
                 extended_fields: str = None,
                 owner_name: str = None,
                 owner_country: str = None):
        self.id = id
        self.name = name
        self.imo = imo
        self.flag = flag
        self.flag_name = flag_name
        self.build_year = build_year
        self.vessel_type_id = vessel_type_id
        self.vessel_type = vessel_type
        self.vessel_type_label_en = vessel_type
        self.length_overall = length_overall
        self.gross_tonnage = gross_tonnage
        self.beam = beam
        self.engine_model = engine_model
        self.engine_power = engine_power
        self.designer_name = designer_name
        self.yard_name = yard_name
        self.vessel_status_id = vessel_status_id
        self.owner_company_name = owner_name
        self.owner_country = owner_country
        self.capacity = None
        self.units = None
        self.propulsion_method = None
        self.fisheries_fish_hold_capacity = None
        self.fisheries_fish_hold_capacity_measurement_unit = None
        self.aquaculture_fish_hold_capacity = None
        self.aquaculture_fish_hold_capacity_measurement_unit = None
        self.history = history
        self.bruttotons = bruttotons
        self.nettotons = nettotons
        if extended_fields is not None:
            fields = json.loads(extended_fields)

            if "propulsionAndManeuvering" in fields and "mainPowerDriveMethod" in fields["propulsionAndManeuvering"]:
                self.propulsion_method = fields["propulsionAndManeuvering"]["mainPowerDriveMethod"]

            if "other" in fields and "fishCapacity" in fields["other"]:
                if fields["other"]["fishCapacity"]["units"] is not None and fields["other"]["fishCapacity"]["value"] is not None and \
                        fields["other"]["fishCapacity"]["units"] in ['CUBIC_METERS', 'TONNS']:
                    self.fisheries_fish_hold_capacity_measurement_unit = _measurement_unit_to_name(fields["other"]["fishCapacity"]["units"])
                    self.fisheries_fish_hold_capacity = int(fields["other"]["fishCapacity"]["value"])
                self.capacity = self.fisheries_fish_hold_capacity
                self.units = self.fisheries_fish_hold_capacity_measurement_unit
            else:
                if "aquaculture" in fields:
                    if "capacity" in fields["aquaculture"]:
                        if fields["aquaculture"]["capacity"]["units"] is not None and fields["aquaculture"]["capacity"]["value"] is not None and \
                                fields["aquaculture"]["capacity"]["units"] in ['CUBIC_METERS', 'TONNS']:
                            self.aquaculture_fish_hold_capacity_measurement_unit = _measurement_unit_to_name(fields["aquaculture"]["capacity"]["units"])
                            self.aquaculture_fish_hold_capacity = int(fields["aquaculture"]["capacity"]["value"])
                            self.capacity = self.aquaculture_fish_hold_capacity
                            self.units = self.aquaculture_fish_hold_capacity_measurement_unit

                        self.estimated_fish_weight = None
        if self.capacity is not None:
            if vessel_type_id == VesselType.WELLBOAT:
                # Generally wellboats are loaded to up to 18% LW
                # Real load max seems to be at 15%
                self.estimated_fish_weight = self.capacity * 0.15 * wellboat_load_ratio
            if vessel_type_id == VesselType.HARVESTING:
                self.estimated_fish_weight = self.capacity * harvester_load_ratio
        else:
            if self.fisheries_fish_hold_capacity_measurement_unit == 't':
                self.estimated_fish_weight = self.fisheries_fish_hold_capacity * 0.95
            else:
                if vessel_type_id in [VesselType.HARVESTING, VesselType.WELLBOAT]:
                    # No explicit estimated fish weight is provided
                    self.estimated_fish_weight = 0

    def get_historical_update(self, date: datetime):
        latest_update = self.history.loc[self.history['updated_at'] > date]
        if latest_update.empty:
            return None
        else:
            return json.loads(self.history.loc[latest_update.updated_at.idxmin()]['before_update'])

    def get_historical_name(self, date: datetime):
        before_update = self.get_historical_update(date)
        if before_update is None:
            return self.name
        else:
            return before_update['name']

    def get_historical_flag_name(self, date: datetime):
        before_update = self.get_historical_update(date)
        if before_update is None:
            return self.flag_name
        else:
            return get_country_by_id(before_update['flag'])

    def get_historical_flag(self, date: datetime):
        before_update = self.get_historical_update(date)
        if before_update is None:
            return self.flag
        else:
            return before_update['flag']

    def get_historical_owner_company_name(self, date: datetime):
        before_update = self.get_historical_update(date)
        if before_update is None:
            return self.owner_company_name
        else:
            return get_company_name_by_id(before_update['owner'])

    def __str__(self):
        return f"{self.id}, {self.name}, {self.flag}, {self.vessel_type_id}, {self.vessel_status_id}"


class Status(IntEnum):
    IN_TRANSIT = 1
    AT_FISH_FARM = 2
    AT_FACTORY = 3
    AT_UNKNOWN_PORT = 4
    AT_SMOLT = 5
    AT_BROOD_FISH = 6


class State:
    def __init__(self, time: int, farm_id: int, status: Status, duration: int):
        self.time = time
        self.farm_id = farm_id
        self.status = status
        self.duration = round(duration) if duration is not None else -1

    def __str__(self):
        return f"{self.time}, {self.status.name}, {self.farm_id}"


class Location:
    def __init__(self, time: int, latitude: float, longitude: float, speed: float, heading: int, status: Status):
        self.time = time
        if isinstance(time, datetime):
            self.time = time.timestamp()
        self.latitude = latitude
        self.longitude = longitude
        self.speed = speed
        self.heading = heading
        self.status = status
        self.farm_id = 0

    def __str__(self):
        time = datetime.fromtimestamp(self.time)
        # time = datetime.strftime('%Y-%m-%d %H:%M:%S'.format(time))
        return f"{time}, {self.latitude}, {self.longitude}, {self.speed}, {self.heading}, {self.status.name if self.status is not None else ''}, {self.farm_id}"


class LicenseType(IntEnum):
    FISH_FARM = 1
    SMOLT = 2
    BROOD_FISH = 3
    FACTORY = 4
