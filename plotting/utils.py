# Get track color depending on speed and according to Fishfacts live map
def get_speed_color(speed: float) -> str:
    if 0 <= speed <= 0.3:
        return '#0118c8'  # dark blue
    elif 0.3 < speed <= 1:
        return '#4e74fb'  # medium light blue
    elif 1 < speed <= 3:
        return '#4db2ff'  # light blue
    elif 3 < speed <= 4:
        return '#01e6b7'  # turquoise
    elif 4 < speed <= 5.5:
        return '#b3f95b'  # lime
    elif 5.5 < speed <= 7:
        return '#ffff00'  # yellow
    elif 7 < speed <= 10:
        return '#ffd325'  # orange
    elif 10 < speed <= 13:
        return '#ff8717'  # dark orange
    elif speed > 13:
        return '#ff0000'  # red
