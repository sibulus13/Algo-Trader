import csv
from pathlib import Path

from .constants import EXEC_CSV_HEADERS


def write_to_csv(fileName: str, data, header=EXEC_CSV_HEADERS):
    '''
    Writes header to csv file if it is a new file
    Writes data to csv file based on the header
    '''
    path = Path(fileName)
    isNewFile = False
    if not path.is_file() and header:
        print('Creating new file: ', fileName)
        isNewFile = True
    with open(fileName, 'a', newline='') as csv_file:
        csv_writer = csv.DictWriter(csv_file,
                                    delimiter=',',
                                    quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL,
                                    fieldnames=header)
        if isNewFile:
            csv_writer.writeheader()
        csv_writer.writerow(data)
    print(f'wrote to {fileName}: {data}')