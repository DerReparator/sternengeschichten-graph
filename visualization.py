'''This module converts cached episode info into a GrphViz visualization.'''

import logging
import os
from typing import List
from pprint import pformat

import graphviz

LOGFILE = 'visualizationLog.log'
LINK_FILE_DIRECTORY = 'cache'
GRAPH_NAME = 'sternengeschichten'

def export_graph():
    '''Export the GraphViz visualization for every *.links file in the given
    LINK_FILE_DIRECTORY.'''
    graph = graphviz.Digraph('G',
    filename=GRAPH_NAME+'.gv',
    engine='fdp',
    strict=True,
    graph_attr={'overlap': 'prism', 'overlap_scaling': '-3.5'}
    )

    # Episodes without a reference to another episode
    standalone_episodes = set()
    overall_mentioned_episodes = set() # Episodes that mention or are mentioned by other episodes
    for links_file in __find_all_links_files(LINK_FILE_DIRECTORY):
        from_id = __parse_links_filename_for_episode_id(links_file)
        mentioned_episodes = __get_destination_episodes_from_links_file(links_file)
        if len(mentioned_episodes) == 0:
            standalone_episodes.add(from_id)
        for to_id in mentioned_episodes:
            graph.edge(str(from_id), str(to_id))
            overall_mentioned_episodes.add(from_id)
            overall_mentioned_episodes.add(to_id)

    # Remove any episodes that are connected to at least 1 other episode in any way
    standalone_episodes.difference_update(overall_mentioned_episodes)
    __handle_standalone_episodes(standalone_episodes, graph)
    graph.view()

def __parse_links_filename_for_episode_id(links_filename: str) -> int:
    filename, file_extension = os.path.splitext(os.path.basename(links_filename))
    filename = filename.replace("Episode", "").replace(".links", "")
    return int(filename)

def __handle_standalone_episodes(standalone_episodes, graph: graphviz.Digraph):
    with graph.subgraph(name=f'cluster_{GRAPH_NAME}_0') as c:
        c.attr(style='filled', color='lightgrey')
        for ep_id in [str(ep) for ep in standalone_episodes]:
            c.node(ep_id)
        c.attr(label='Standalone Episodes')

def __get_destination_episodes_from_links_file(path_to_links_file: str) -> List[int]:
    with open(path_to_links_file, 'r', encoding='UTF-8') as links_file:
        ret: List[int] = []
        for line in links_file:
            if str.strip(line) == ""\
            or line[0] == "#":
                continue
            ret.append(int(line))
        logging.debug("Found %d linked Episodes in *.links file %s.", len(ret),
                      path_to_links_file)
        return ret


def __find_all_links_files(directory: str) -> List[str]:
    all_links_files = []
    for path, _, files in os.walk(directory):
        for file in [f for f in files if f.endswith(".links")]:
            all_links_files.append(str(os.path.abspath(os.path.join(path,file))))
    logging.info("Found %s *.links files", len(all_links_files))
    logging.debug("Found *.links files for Episodes: %s", pformat(all_links_files))
    return all_links_files

def __setup_logging():
    logging.basicConfig(level=logging.DEBUG)
    log_formatter = logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    root_logger = logging.getLogger()

    file_handler = logging.FileHandler(LOGFILE)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    logging.info("Set up logging successfully")


__setup_logging()
if __name__=='__main__':
    logging.info("=== This is the Sternengeschichten GraphViz visualization ===")
    if not os.path.isdir(LINK_FILE_DIRECTORY):
        logging.error("Visualization failed because directory was not found (%s)",
                      LINK_FILE_DIRECTORY)
    else:
        export_graph()
