import urllib.request
import requests
import logging
import os
import lxml.html
import shutil
from pathlib import Path
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
import multiprocessing
import concurrent.futures
import re

MAX_NUM_THREADS: int = multiprocessing.cpu_count()
THREAD_TIMEOUT_SECONDS: int = 300
PODCAST_DIRECTORY_URL: str = 'https://scienceblogs.de/astrodicticum-simplex/sternengeschichten/'
CACHE_DIR = 'cache'
CHUNK_DIR_NAME = 'chunks'
LOGFILE = 'applicationLog.log'

REGEX_MATCH_FOR_EPISODE_NR = re.compile(r"folge (\d+)", re.IGNORECASE)

class PodcastEpisode:
    def __init__(self, episodeNumber: int, downloadUrl: str, pathToWav: str=None, pathToChunks: str=None, pathToTranscript: str = None, name: str=None, pathToLinkedEpisodes: str=None):
        self.downloadUrl = downloadUrl
        self.pathToWav = pathToWav
        self.pathToChunks = pathToChunks
        self.pathToTranscript = pathToTranscript
        self.name = name
        self.episodeNumber = episodeNumber
        self.pathToLinkedEpisodes = pathToLinkedEpisodes

    def getDownloadUrl(self):
        return self.downloadUrl

    def getPathToWav(self):
        return self.pathToWav

    def getPathToChunks(self):
        return self.pathToChunks

    def getPathToTranscript(self):
        return self.pathToTranscript

    def getName(self):
        return self.name

    def getPathToLinkedEpisodes(self):
        return self.pathToLinkedEpisodes

    def setDownloadUrl(self, downloadUrl):
        self.downloadUrl = downloadUrl

    def setPathToWav(self, pathToWav):
        self.pathToWav = pathToWav

    def setPathToChunks(self, pathToChunks):
        self.pathToChunks = pathToChunks

    def setPathToTransscript(self, pathToTranscript):
        self.pathToTranscript = pathToTranscript

    def setName(self, name):
        self.name = name

    def setEpisodeNumber(self, episodeNr):
        self.episodeNumber = episodeNr

    def setPathToLinkedEpisodes(self, pathToLinkedEpisodes):
        self.pathToLinkedEpisodes = pathToLinkedEpisodes

    def getEpisodeNumber(self):
        return self.episodeNumber

    def getExpectedPathToWav(self):
        return os.path.join(CACHE_DIR,f"Sternengeschichten{self.episodeNumber}.wav")

    def getExpectedPathToChunks(self):
        return os.path.join(CACHE_DIR, f"{CHUNK_DIR_NAME}{self.episodeNumber}")

    def getExpectedPathToTranscript(self):
        return os.path.join(CACHE_DIR, f"Episode{self.episodeNumber}_transcript.txt")

    def getExpectedPathToLinkedEpisodes(self):
        return os.path.join(CACHE_DIR, f"Episode{self.episodeNumber}.links")

def getListOfPodcastEpisodes() -> []:
    episodeDownloadLinks = getListOfPodcastEpisodeDownloadLinks()

    podcastEpisodes = []
    for episodeNumber, downloadLink in enumerate(episodeDownloadLinks, start=1):
        podcastEpisodes.append(PodcastEpisode(episodeNumber, downloadLink))

    logging.debug(f"Retrieved {len(podcastEpisodes)} Podcast Episodes")
    return podcastEpisodes

def getListOfPodcastEpisodeDownloadLinks() -> []:
    logging.debug(f"Retrieving list of Podcast episodes from {PODCAST_DIRECTORY_URL}")
    downloadLinks = []
    directoryWebsite = downloadPodcastDirectoryWebsite()
    parsed_html = lxml.html.document_fromstring(directoryWebsite)

    for link in parsed_html.xpath('//li/a[2]/@href'):
        downloadLinks.append(link)

    logging.debug(f"Retrieved {len(downloadLinks)} Episode download links")
    return downloadLinks

def downloadPodcastDirectoryWebsite() -> str:
    logging.debug("Downloading Podcast Episode List Website...")
    response = requests.get(PODCAST_DIRECTORY_URL)
    if response.status_code != 200:
        raise ValueError("Podcast Directory URL not ok.")
    logging.debug("Done.")
    return response.content

def handleSinglePodcastEpisode(episode: PodcastEpisode):
    logging.debug(f"Starting to handle Episode {episode.getEpisodeNumber()}")
    if os.path.isfile(episode.getExpectedPathToLinkedEpisodes()):
        logging.debug(f"Found link file for Episode {episode.getEpisodeNumber()}. Skipping every generation step.")
    elif os.path.isfile(episode.getExpectedPathToTranscript()):
        logging.debug(f"Found transcript for Episode {episode.getEpisodeNumber()}")
        episode.setPathToTransscript(episode.getExpectedPathToTranscript())
        analyseTranscriptOfEpisode(episode)
    elif os.path.isdir(episode.getExpectedPathToChunks()):
        logging.debug(f"Found chunk folder for Episode {episode.getEpisodeNumber()}")
        episode.setPathToChunks(episode.getExpectedPathToChunks())
        transcribeAndStoreSingleEpisode(episode)
        analyseTranscriptOfEpisode(episode)
    elif os.path.isfile(episode.getExpectedPathToWav()):
        logging.debug(f"Found WAV file for Episode {episode.getEpisodeNumber()}")
        episode.setPathToWav(episode.getExpectedPathToWav())
        chunkenizeSinglePodcastEpisode(episode)
        transcribeAndStoreSingleEpisode(episode)
        analyseTranscriptOfEpisode(episode)
    else:
        logging.debug(f"No cached information found for Episode {episode.getEpisodeNumber()}")
        downloadSinglePodcastEpisode(episode)
        chunkenizeSinglePodcastEpisode(episode)
        transcribeAndStoreSingleEpisode(episode)
        analyseTranscriptOfEpisode(episode)

    logging.info(f"Handled Episode {episode.getEpisodeNumber()}")

def transcribeAndStoreSingleEpisode(episode: PodcastEpisode):
    transcription = transcribeSinglePodcastEpisode(episode)
    with open(str(episode.getExpectedPathToTranscript()), 'w') as transcript_file:
        transcript_file.write(transcription)
        episode.setPathToTransscript(episode.getExpectedPathToTranscript())
    logging.debug(f"Removing Chunk cache of Episode {episode.getEpisodeNumber()} at {episode.getPathToChunks()}")
    shutil.rmtree(episode.getPathToChunks())

def analyseTranscriptOfEpisode(episode: PodcastEpisode):
    logging.debug(f"Analysing the transcript of Episode {episode.getEpisodeNumber()}")
    with open(str(episode.getPathToTranscript()), 'r') as transcript_file:
        transcript = transcript_file.read().replace('\n',' ')
    quoted_episodes = set([int(epNr) for epNr in REGEX_MATCH_FOR_EPISODE_NR.findall(transcript)])
    quoted_episodes.discard(episode.getEpisodeNumber()) # remove this episode's own episode number
    with open(str(episode.getExpectedPathToLinkedEpisodes()), 'w') as output_file:
        for quoted_episode in quoted_episodes:
            output_file.write(str(quoted_episode))
            output_file.write(os.linesep)
    episode.setPathToLinkedEpisodes(episode.getExpectedPathToLinkedEpisodes())

def downloadSinglePodcastEpisode(episode: PodcastEpisode):
    downloadUrl = episode.getDownloadUrl()
    logging.debug(f"Downloading Episode {episode.getEpisodeNumber()} from {downloadUrl}...")
    Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
    outputFileName: str = os.path.join(CACHE_DIR, f"Episode {episode.episodeNumber}.mp3")
    r = requests.get(downloadUrl, stream=True)
    if r.status_code == 200:
        with open(str(outputFileName), 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    else:
        raise ValueError(f"Episode download from {downloadUrl} failed.")
    episode.setPathToWav(convertToWAV(outputFileName))
    shutil.move(episode.getPathToWav(), episode.getExpectedPathToWav())
    episode.setPathToWav(episode.getExpectedPathToWav())
    os.remove(outputFileName)

def convertToWAV(fileName: str) -> str:
    sound = AudioSegment.from_mp3(fileName)
    outputFileName = str(Path(fileName).with_suffix('.wav'))
    sound.export(outputFileName, format="wav")
    return outputFileName

def chunkenizeSinglePodcastEpisode(episode: PodcastEpisode):
    path = episode.getPathToWav()
    logging.debug(f"Parsing from {path} for splitting...")
    sound = AudioSegment.from_wav(path)
    # split audio sound where silence is 700 miliseconds or more and get chunks
    logging.debug("Splitting on silence...")
    chunks = split_on_silence(sound,
        # experiment with this value for your target audio file
        min_silence_len = 500,
        # adjust this per requirement
        silence_thresh = sound.dBFS-14,
        # keep the silence for 1 second, adjustable as well
        keep_silence=500,
    )
    logging.debug("Splitting complete.")
    folder_name = episode.getExpectedPathToChunks()
    # create a directory to store the audio chunks
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)
    # export each chunk
    for i, audio_chunk in enumerate(chunks, start=1):
        chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
        logging.debug(f"Export chunk {i} of episode {episode.getEpisodeNumber()} to {chunk_filename}")
        audio_chunk.export(chunk_filename, format="wav")
    episode.setPathToChunks(folder_name)
    os.remove(path)

def transcribeSinglePodcastEpisode(episode: PodcastEpisode) -> str:
    logging.info(f"Transcribing Episode {episode.getEpisodeNumber()} with chunk folder {episode.getPathToChunks()}")
    whole_text = ""
    r = sr.Recognizer()
    try:
        for _, _, f in os.walk(episode.getPathToChunks()):
            for chunk_filename in f:
                chunk_filename_abs = os.path.join(episode.getPathToChunks(), chunk_filename)
                with sr.AudioFile(chunk_filename_abs) as source:
                    audio_listened = r.record(source)
                    # try converting it to text
                    try:
                        logging.debug(f"Recognizing from {chunk_filename_abs} via Google")
                        text = r.recognize_google(audio_listened, language='de-DE')
                    except sr.UnknownValueError as e:
                        print("Error:", str(e))
                    else:
                        text = f"{text.capitalize()}. "
                        whole_text += text
        return whole_text
    except sr.UnknownValueError:
        logging.error("Sphinx could not understand audio")
        return "Sphinx could not understand audio"
    except sr.RequestError as e:
        logging.error(f"Sphinx error; {e}")
        return f"Sphinx error; {e}"

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

    logging.info("Set up logging successfully")

if __name__=='__main__':
    setUpLogging()
    logging.info("=== Start of Sternengeschichten Graph")
    logging.debug(f"Using {MAX_NUM_THREADS} threads...")

    logging.info("Querying list of podcast episodes")
    podcastEpisodes = getListOfPodcastEpisodes()
    logging.info(f"Got {len(podcastEpisodes)} podcast episodes")

    # Only process a subset of the episodes because of time constrains
    # Only episodes startAtEpisode -> endAtEpisode-1 will be handled
    startAtEpisode: int = 25
    endAtEpisode: int = startAtEpisode+(MAX_NUM_THREADS*3)

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_NUM_THREADS) as executor:
        # executor.map(handleSinglePodcastEpisode, podcastEpisodes[startAtEpisode:endAtEpisode], timeout=THREAD_TIMEOUT_SECONDS)
        future_to_episode = {executor.submit(handleSinglePodcastEpisode, episode): episode for episode in podcastEpisodes[startAtEpisode:endAtEpisode]}
        for future in concurrent.futures.as_completed(future_to_episode):
            episode = future_to_episode[future]
            try:
                data = future.result()
            except Exception as exc:
                logging.error(str(exc))
    logging.info("=== Finished")
