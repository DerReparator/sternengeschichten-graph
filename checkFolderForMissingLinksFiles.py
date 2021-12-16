import argparse
import logging
import os
from typing import List
import re

LOGFILE = 'missingEpisodes.log'

class MissingEpisodesChecker:
    def __init__(self, folderPath: str):
        self.folderPath = folderPath
        self.missingEpisodes = []

    def check_for_missing_episodes(self):
        if not os.path.isdir(self.folderPath):
            logging.error(f'Could not check for missing episodes because {self.folderPath} is not a valid folder.')
            return
        episodes = self._get_episodes_from_folder()
        episodes.sort()
        self.missingEpisodes = self._get_missing_integers_from_sorted_array(episodes)

    def _get_missing_integers_from_sorted_array(self, arr: List[int]) -> List[int]:
        logging.debug(f'Missing ints of {arr}')
        if len(arr) == 0: return []
        currInt: int = arr[0]
        currIdx: int = 0
        missingInts: List[int] = []
        while currInt < arr[-1]:
            if arr[currIdx] == currInt:
                currInt = currInt + 1
                currIdx = currIdx + 1
            else:
                missingInts.append(currInt)
                currInt = currInt + 1
        return missingInts

    def _get_episodes_from_folder(self) -> List[int]:
        EPISODE_IDX_REGEX = re.compile(r".*?(\d+)\.links$", re.IGNORECASE)
        episodes = []
        for _,_,filenames in os.walk(self.folderPath):
            for filename in filenames:
                match = EPISODE_IDX_REGEX.match(filename)
                if match:
                    episodes.append(int(match.group(1)))
        return episodes

    def get_missing_episodes(self):
        return self.missingEpisodes


def setUpLogging():
	logging.basicConfig(level=logging.DEBUG)
	logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
	rootLogger = logging.getLogger()

	fileHandler = logging.FileHandler(LOGFILE)
	fileHandler.setFormatter(logFormatter)
	rootLogger.addHandler(fileHandler)

	consoleHandler = logging.StreamHandler()
	consoleHandler.setFormatter(logFormatter)
	rootLogger.addHandler(consoleHandler)

	logging.debug("Set up logging successfully")

if __name__=='__main__':
    setUpLogging()
    parser = argparse.ArgumentParser(description='Check a folder for existence of every *.links file between its oldest and latest episode.')
    parser.add_argument('folderPath', type=str,
                    help='the folder containing the *.links files')
    args = parser.parse_args()
    folderPath: str = args.folderPath
    logging.info(f'Searching folder "{folderPath}"...')
    checker = MissingEpisodesChecker(folderPath)
    checker.check_for_missing_episodes()

    if len(checker.get_missing_episodes()) == 0:
        logging.info(f'NO MISSING EPISODES DETECTED!')
    else:
        logging.info(f'Missing episodes:')
        for episodeNr in checker.get_missing_episodes():
            logging.info(f'{episodeNr}')
    logging.info('=== Finished ===')
