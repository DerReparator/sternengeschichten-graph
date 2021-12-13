import graphviz
import os
from typing import List

LINK_FILE_DIRECTORY = 'cache'

def exportGraph():
    g = graphviz.Digraph('G', filename='sternengeschichten.gv')
    for linksFile in findAllLinksFiles(LINK_FILE_DIRECTORY):
        filename, file_extension = os.path.splitext(os.path.basename(linksFile))
        filename = filename.replace("Episode", "").replace(".links", "")
        fromID = int(filename)
        for toID in getDestinationEpisodesFromLinksFile(linksFile):
            g.edge(str(fromID), str(toID))

    g.view()

def getDestinationEpisodesFromLinksFile(pathToLinksFile: str) -> List[int]:
    with open(pathToLinksFile, 'r') as f:
        return [int(line) for line in f]


def findAllLinksFiles(directory: str) -> List[str]:
    allLinksFiles = []
    for path, _, files in os.walk(directory):
        for file in [f for f in files if f.endswith(".links")]:
            allLinksFiles.append(str(os.path.abspath(os.path.join(path,file))))
    return allLinksFiles

if __name__=='__main__':
    if not os.path.isdir(LINK_FILE_DIRECTORY):
        print(f"Visualization failed because directory was not found ({LINK_FILE_DIRECTORY})")
    else:
        exportGraph()
