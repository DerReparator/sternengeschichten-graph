import graphviz
import os
from typing import List

LINK_FILE_DIRECTORY = 'cache'
GRAPH_NAME = 'sternengeschichten'

def exportGraph():
    g = graphviz.Digraph('G',
    filename=GRAPH_NAME+'.gv',
    engine='fdp',
    strict=True,
    graph_attr={'overlap': 'prism', 'overlap_scaling': '-3.5'}
    )

    # Episodes without a reference to another episode
    standaloneEpisodes = set()
    overallMentionedEpisodes = set()
    for linksFile in findAllLinksFiles(LINK_FILE_DIRECTORY):
        fromID = parseLinksFilenameForEpisodeID(linksFile)
        mentionedEpisodes = getDestinationEpisodesFromLinksFile(linksFile)
        if len(mentionedEpisodes) == 0:
            standaloneEpisodes.add(fromID)
        for toID in mentionedEpisodes:
            g.edge(str(fromID), str(toID))
            overallMentionedEpisodes.add(fromID)
            overallMentionedEpisodes.add(toID)

    # Remove any episodes that are connected to at least 1 other episode in any way
    standaloneEpisodes.difference_update(overallMentionedEpisodes)
    handleStandaloneEpisodes(standaloneEpisodes, g)
    g.view()

def parseLinksFilenameForEpisodeID(linksFilename: str) -> int:
    filename, file_extension = os.path.splitext(os.path.basename(linksFilename))
    filename = filename.replace("Episode", "").replace(".links", "")
    return int(filename)

def handleStandaloneEpisodes(standaloneEpisodes, graph: graphviz.Digraph):
    with graph.subgraph(name=f'cluster_{GRAPH_NAME}_0') as c:
        c.attr(style='filled', color='lightgrey')
        for epId in [str(ep) for ep in standaloneEpisodes]:
            c.node(epId)
        c.attr(label='Standalone Episodes')

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
