# Sternengeschichten Graph

The software in this Repo is made for the fantastic (German) podcast [Sternengeschichten](https://florian-freistetter.de/sternengeschichten/) by Florian Freistetter.

It aims to provide a visual (graph) representation of the backward references used during the Podcast's episodes. Example:

[Example Graph](pics/example_graph.png)

As you can see, episode 139 references the episode 131 and 4. Episode 101 is referenced by 2 episodes: 138 and 131.

## How to use

1. Activate a virtual environment under Python 3 (tested with 3.7.1)
```
cd /this/directory/in/your/cloned/repo
python -m venv .env &&\
source .env/bin/activate &&\
pip install -r requirements.txt
```
This will install all dependencies into the virtual environment located in `.env`.
After the initial setup it is enough to activate the environment using the following command:
```
source .env/bin/activate
```

2. Make sure you have `ffmpeg` [Website](https://ffmpeg.org/) installed on your system. Under MacOS, you can use [Homebrew](https://brew.sh) to install it:
```
brew install ffmpeg
```

3. If you want to visualize the result, you also need to install `graphviz` on your
machine from their [Website](https://graphviz.org/download/). Under MacOS, you can use
[Homebrew](https://brew.sh) to install it:
```
brew install graphviz
```

4. Run the `sternengeschichten_graph.py` script which can take a very long time!

5. For actual visualization, you need to execute `visualization.py`to draw a graph from a folder containing `*.links`files.

## For developers

When you add/update dependencies, please make sure to update the `requirements.txt`
file accordingly like so:

```
(venv) /foo/bar> pip freeze > requirements.txt
```
