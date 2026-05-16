from src.core.segmentation import split_tracks
from src.core.time import resample_segment
from src.core.distance import calculate_distance
from src.core.kinematics import compute_speed
from src.core.zones import assign_zone_labels, add_in_zone_flag

STEP_REGISTRY = {
    'split_tracks': split_tracks,
    'resample_segment': resample_segment,
    'calculate_distance': calculate_distance,
    'compute_speed': compute_speed,
    'assign_zone_labels': assign_zone_labels,
    'add_in_zone_flag': add_in_zone_flag,
}
