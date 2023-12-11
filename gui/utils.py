import winsound


def notify(duration=2000, freq=440):
    '''
    Duration [ms]
    Freq[Hz]
    '''
    winsound.Beep(freq, duration)