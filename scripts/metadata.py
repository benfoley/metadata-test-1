import json
from pathlib import Path
from typing import Dict, List, Optional

AuthorInfo = Dict[str, str]

DEFAULT_AUTHOR = {
    "name": "Unknown",
    "orcid": "https://orcid.org/0000-0000-0000-0000",
}
CREATORS_KEY = "creators"


def extract_default_authors(metadata: Path) -> List[AuthorInfo]:
    """Attempts to extract author information from the metadata.json file within
    the repository. If none are found, returns a dummy value.

    Parameters:
        metadata: The path to the metadata file, commonly metadata.json
    """
    with open(metadata) as file:
        data = json.load(file)

    if CREATORS_KEY not in data:
        return [DEFAULT_AUTHOR]

    return data[CREATORS_KEY]


def extract_notebook_authors(notebook: Path) -> Optional[List[AuthorInfo]]:
    """Attempts to extract author information from within a jupyter notebook.

    Parameters:
        notebook: The path to the jupyter notebook
    """
    with open(notebook) as file:
        data = json.load(file)

    notebook_metadata = data["metadata"]
    if CREATORS_KEY not in notebook_metadata:
        return None

    return notebook_metadata[CREATORS_KEY]
