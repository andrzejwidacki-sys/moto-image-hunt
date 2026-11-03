"""Source registry. Native sources run first so they win de-duplication against the aggregator."""
from . import commons, flickr, github, openverse, pexels, pixabay, unsplash

ALL = [commons, flickr, pexels, pixabay, unsplash, github, openverse]
BY_NAME = {m.NAME: m for m in ALL}
