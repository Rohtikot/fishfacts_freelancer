from shapely.geometry import Point
import os
import pandas as pd
from datetime import datetime, timedelta
import requests
from zipfile import ZipFile
from io import BytesIO
from tqdm import tqdm


def read_fangstdata(year: int, use_specific_cols: list[str] | bool = None) -> pd.DataFrame:
    """
        Read FDIR catch sheet and add time column for landing timestamp.

        :param year: year to select for DCA CSV-file
        :param use_specific_cols: list of columns to use
        :return: Pandas data frame of Norwegian catches containing custom "landing_time" columns as datetime object.
    """

    path = fr"C:\Program Files (x86)\Fishfacts\catch\norway\catch\fangstdata_{year}.csv"

    # Use specific columns that have been specified to minimize memory usage

    always_include_cols = ['Landingsdato', 'Landingsklokkeslett', 'Fartøynavn', 'Radiokallesignal (seddel)',
                           'Registreringsmerke (seddel)', 'Største lengde', 'Art - FDIR', 'Rundvekt',
                           'Fiskernasjonalitet', 'Mottakernasjonalitet', 'Områdegruppering']

    # Handle use_specific_cols
    if use_specific_cols is True:
        # Use only the default columns
        use_specific_cols = always_include_cols
    elif isinstance(use_specific_cols, list):
        # Combine default and specific columns
        use_specific_cols = always_include_cols + use_specific_cols
    elif use_specific_cols is None:
        # Do not use usecols (read all columns)
        use_specific_cols = None
    else:
        raise ValueError("use_specific_cols must be a list of strings, True, or None.")

    dataframe = pd.read_csv(path, usecols=use_specific_cols, delimiter=';', decimal=',')

    # Create landing_time column that contains datetime objects
    dataframe['landing_time'] = dataframe['Landingsdato'] + ' ' + dataframe['Landingsklokkeslett']
    dataframe['landing_time'] = pd.to_datetime(dataframe['landing_time'], format='%d.%m.%Y %H:%M:%S')

    dataframe.drop(columns=['Landingsdato', 'Landingsklokkeslett'], inplace=True)

    return dataframe


def read_dca(year: int, use_specific_cols: list[str] | bool = None) -> pd.DataFrame:
    """
    Read ERS-DCA sheet and add time columns such as start and stop times for fishing activities.

    :param year: year to select for DCA CSV-file
    :param use_specific_cols: list of columns to use
    :return: Pandas data frame that contains Norwegian catch operations with columns "Start tid" and "Stopp tid"
            as datetime objects.
    """

    always_include_cols = ['Startdato', 'Startklokkeslett', 'Stoppdato', 'Stoppklokkeslett', 'Startposisjon bredde',
                           'Startposisjon lengde', 'Stopposisjon bredde', 'Stopposisjon lengde', 'Art - FDIR',
                           'Rundvekt']

    path = fr"C:\Program Files (x86)\Fishfacts\catch\norway\ers\elektronisk-rapportering-ers-{year}-fangstmelding-dca.csv"
    if use_specific_cols:
        use_specific_cols = use_specific_cols + always_include_cols
    # TODO: Implement the same 'use_specific_cols' as in read_fangstdata()
    dataframe = pd.read_csv(path, usecols=use_specific_cols, delimiter=';', decimal=',', low_memory=False)

    # Create necessary time columns from different time columns
    dataframe['start_time'] = dataframe['Startdato'] + ' ' + dataframe['Startklokkeslett']
    dataframe['stop_time'] = dataframe['Stoppdato'] + ' ' + dataframe['Stoppklokkeslett']
    dataframe['start_time'] = pd.to_datetime(dataframe['start_time'], format='%d.%m.%Y %H:%M')
    dataframe['stop_time'] = pd.to_datetime(dataframe['stop_time'], format='%d.%m.%Y %H:%M')

    # TODO: This is not working optimally
    # Create shapely Points for start and stop positions
    dataframe['start_position'] = dataframe.apply(
        lambda row: Point(row['Startposisjon lengde'], row['Startposisjon bredde']), axis=1)
    dataframe['stop_position'] = dataframe.apply(
        lambda row: Point(row['Stopposisjon lengde'], row['Stopposisjon bredde']), axis=1)

    # dataframe.drop(columns=['Startdato', 'Startklokkeslett', 'Stoppdato', 'Stoppklokkeslett', 'Startposisjon lengde',
    #                         'Startposisjon bredde', 'Stopposisjon lengde', 'Stopposisjon bredde'], inplace=True)

    return dataframe


def read_arrivals(year: int) -> pd.DataFrame:
    path = fr"C:\Program Files (x86)\Fishfacts\catch\norway\ers\elektronisk-rapportering-ers-{year}-ankomstmelding-por.csv"
    dataframe = pd.read_csv(path, delimiter=';', decimal=',', low_memory=False)

    # Create necessary time columns from different columns
    dataframe['arrival_time'] = dataframe['Ankomstdato'] + ' ' + dataframe['Ankomstklokkeslett']
    dataframe['arrival_time'] = pd.to_datetime(dataframe['arrival_time'], format='%d.%m.%Y %H:%M')

    return dataframe


def read_departures(year: int) -> pd.DataFrame:
    path = fr"C:\Program Files (x86)\Fishfacts\catch\norway\ers\elektronisk-rapportering-ers-{year}-avgangsmelding-dep.csv"
    dataframe = pd.read_csv(path, delimiter=';', decimal=',', low_memory=False)

    # Create necessary time columns from different columns
    dataframe['departure_time'] = dataframe['Avgangsdato'] + ' ' + dataframe['Avgangsklokkeslett']
    dataframe['departure_time'] = pd.to_datetime(dataframe['departure_time'], format='%d.%m.%Y %H:%M')

    return dataframe


def download_fangstdata(year: int = datetime.now().year) -> None:
    # Specify the URL of the ZIP file
    url = f"https://register.fiskeridir.no/uttrekk/fangstdata_{year}.csv.zip"

    # Send a GET request to the URL with stream=True to download in chunks
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Ensure we notice bad responses

    # Get the total size of the file in bytes
    total_size = int(response.headers.get('content-length', 0))

    # Create a BytesIO object to store the downloaded content
    zip_file = BytesIO()

    # Download the file in chunks and update the progress bar
    with tqdm(total=total_size, unit='B', unit_scale=True, desc='Downloading catch data file') as progress_bar:
        for chunk in response.iter_content(chunk_size=8192):
            zip_file.write(chunk)
            progress_bar.update(len(chunk))

    # Go back to the beginning of the BytesIO object
    zip_file.seek(0)

    save_dir = r"C:\Program Files (x86)\Fishfacts\catch\norway\catch"

    # Open the ZIP file
    with ZipFile(zip_file) as z:
        # Extract and save the CSV file
        for filename in z.namelist():
            if filename.endswith('.csv'):
                # Extract and save the CSV file with its original name
                file_path = os.path.join(save_dir, filename)
                with z.open(filename) as source, open(file_path, 'wb') as target:
                    target.write(source.read())
                print(f"{filename} has been extracted and saved to {save_dir}.")


def download_ers(year: int = datetime.now().year) -> None:
    url = f"https://register.fiskeridir.no/vms-ers/ERS/elektronisk-rapportering-ers-{year}.zip"
    # Send a HEAD request to get the total file size
    response = requests.get(url, stream=True)
    response.raise_for_status()

    # Get the total size of the file in bytes
    total_size = int(response.headers.get('content-length', 0))

    # Create a BytesIO object to store the downloaded content
    zip_file = BytesIO()

    # Download the file in chunks and update the progress bar
    with tqdm(total=total_size, unit='B', unit_scale=True, desc='Downloading ERS sheets') as progress_bar:
        for chunk in response.iter_content(chunk_size=8192):
            zip_file.write(chunk)
            progress_bar.update(len(chunk))

    # Go back to the beginning of the BytesIO object
    zip_file.seek(0)

    save_dir = r"C:\Program Files (x86)\Fishfacts\catch\norway\ers"

    # Open the ZIP file
    with ZipFile(zip_file) as z:
        # Extract and save the CSV files
        for filename in z.namelist():
            if filename.endswith('.csv'):
                # Extract and save the CSV file with its original name
                file_path = os.path.join(save_dir, filename)
                with z.open(filename) as source, open(file_path, 'wb') as target:
                    target.write(source.read())
                print(f"{filename} has been extracted and saved to {save_dir}.")


def file_age(file_name: str, hrs: int = 12) -> bool or None:
    """
    Find out if file is older than threshold (12 hours)

    :param: file_name (str): which file fangstdata (arg: fangst/catch) or ers (arg: ers)

    :return: None
    """

    # check if file_name
    allowed_values = ['fangst', 'catch', 'ers']

    if file_name.lower() not in allowed_values:
        raise ValueError(f"Invalid argument: '{file_name}'. Must be one of {allowed_values}.")

    # get current year
    current_year = datetime.now().year

    # check which file it is
    if file_name.lower() in ['fangst', 'catch']:
        file_path = fr"C:\Program Files (x86)\Fishfacts\catch\norway\catch\fangstdata_{current_year}.csv"
    elif file_name.lower() in ['ers']:
        file_path = fr"C:\Program Files (x86)\Fishfacts\catch\norway\ers\elektronisk-rapportering-ers-{current_year}-fangstmelding-dca.csv"
    else:
        return None

    # TODO: There's a month delay on the DCA sheet, which means an error will occur, when looking for age of this file.
    # Get last modified date
    time = os.path.getmtime(file_path)

    # Convert from Unix timestamp to datetime
    time = datetime.fromtimestamp(time)

    # If file is older than threshold return True
    return datetime.now() - time > timedelta(hours=hrs)

file_age('fangst', hrs=12)
