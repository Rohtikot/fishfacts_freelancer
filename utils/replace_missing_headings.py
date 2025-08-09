from pandas import Series


def replace_heading_error(heading_values: Series) -> Series:
    """
    Fix heading error code 511 by adding values that are in between the last and next actual heading values.

    Arguments:
        heading_values (pandas Series):
            Series of integers

    Returns:
        heading_values_fixed (pandas Series):
            Series of integers with fixed headings

    Example:
        Input:  [349, 336, 511, 511, 511, 511, 511, 174, 174]
        Output: [349, 336, 309, 282, 255, 228, 201, 174, 174]
    """
    heading_values_fixed = heading_values.copy()  # Make a copy to avoid modifying the original Series

    # Find indices with error values
    error_indices = heading_values_fixed[heading_values_fixed == 511].index

    # Replace error values using linear interpolation
    for index in error_indices:
        left_index = index - 1
        right_index = index + 1

        # Find the nearest correct values
        while heading_values_fixed.iloc[left_index] == 511:
            left_index -= 1
        while right_index < len(heading_values_fixed) and heading_values_fixed.iloc[right_index] == 511:
            right_index += 1

        # Perform linear interpolation
        left_value = heading_values_fixed.iloc[left_index]

        if right_index != len(heading_values_fixed):
            right_value = heading_values_fixed.iloc[right_index]
        else:
            back_index = left_index
            while back_index == 511:
                back_index -= 1
            right_value = heading_values_fixed.iloc[back_index]

        difference = right_index - left_index

        for i in range(left_index + 1, right_index):
            proportion = (i - left_index) / difference
            interpolated_value = round(left_value + (right_value - left_value) * proportion)
            heading_values_fixed.iloc[i] = interpolated_value

    return heading_values_fixed
