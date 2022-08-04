from pathlib import Path
from typing import List, Dict
import os
import argparse
from rocrate.rocrate import ROCrate
from rocrate.model.person import Person
from notebook_embedder import embed_notebook_metadata
from metadata import extract_default_authors, extract_notebook_authors
import shutil


NOTEBOOK_EXTENSION = ".ipynb"
DESCRIPTION = """
Embeds rocrate data within every jupyter notebook in the directory, and then
creates a parent rocrate in the same directory.
"""
DEFAULT_CRATE_PROPERTIES = {}
DEFAULT_CRATE_NAME = "ro-crate-metadata.json"
METADATA_KEY = "ro-crate"
TEMP_DIR = "/tmp/crate_hole"


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("dir", type=Path, help="The directory to act on")
    parser.add_argument(
        "metadata",
        type=Path,
        help="An metadata.json file containing some defaults for author information",
    )
    args = parser.parse_args()

    notebooks = get_notebooks(args.dir)
    for notebook in notebooks:
        update_notebook_metadata(notebook, args.metadata)

    create_root_crate(args.dir, notebooks, args.metadata)


def get_notebooks(dir: Path) -> List[Path]:
    files = [Path(file) for file in os.listdir(dir)]
    is_notebook = lambda file: file.suffix == NOTEBOOK_EXTENSION
    return list(filter(is_notebook, files))


def update_notebook_metadata(notebook: Path, metadata: Path) -> None:
    """Creates and embeds an rocrate in the metadata of a jupyter notebooks

    Parameters:
        notebook: The path of a jupyter notebook
        metadata: A metadata file containing author information

    """
    crate = generate_rocrate(notebook, metadata)
    crate_file = create_temporary_crate_file(crate)
    with open(crate_file) as in_file:
        data = in_file.read()
    embed_notebook_metadata(notebook, METADATA_KEY, data)
    clean_up()


def generate_rocrate(notebook: Path, metadata: Path) -> ROCrate:
    crate = ROCrate()
    add_notebook(crate, notebook, metadata)
    return crate


def add_notebook(crate: ROCrate, notebook: Path, metadata: Path) -> None:
    file = crate.add_file(notebook, properties=extract_properties(notebook, metadata))
    # Add the authors
    authors = extract_authors(crate, notebook, metadata)
    crate.add(*authors)
    file["author"] = authors


def extract_properties(notebook: Path, metadata: Path) -> Dict[str, str]:
    return {"name": notebook.name, "encodingFormat": "application/x-ipynb+json"}


def extract_authors(crate: ROCrate, notebook: Path, metadata: Path) -> List[Person]:
    notebook_authors = extract_notebook_authors(notebook)
    default_authors = extract_default_authors(metadata)

    authors = notebook_authors if notebook_authors is not None else default_authors
    return [
        Person(crate, author["orcid"], {"name": author["name"]}) for author in authors
    ]


def create_root_crate(output_dir: Path, notebooks: List[Path], metadata: Path) -> None:
    """Creates a parent crate in the supplied directory, linking together the
    info from its children crates.

    Parameters:
        notebooks: The notebooks to include in the crate
        output_dir: The path to the directory in which to create the
                ro-crate-metadata.json file.
        metadata: A path to a metadata.json file
    """
    result = ROCrate()
    for notebook in notebooks:
        add_notebook(result, notebook, metadata)

    # Create and copy across ro-crate-metadata.json file
    crate_file = create_temporary_crate_file(result)
    shutil.copyfile(crate_file, output_dir.joinpath(crate_file.name))
    clean_up()


def create_temporary_crate_file(crate: ROCrate) -> Path:
    temp_dir = Path(TEMP_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)

    crate.write(temp_dir)
    return temp_dir.joinpath(DEFAULT_CRATE_NAME)


def clean_up() -> None:
    """Deletes the temporary directory"""
    shutil.rmtree(TEMP_DIR)


if __name__ == "__main__":
    main()
