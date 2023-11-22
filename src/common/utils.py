import os
import json
from typing import Dict


def load_file(filepath: str) -> Dict:
    '''
    Load data from file and return data in key-value dict
    '''
    if filepath is None or not (os.path.exists(filepath)):
        raise Exception(f"Failed to load file; invalid file (={filepath})")

    with open(filepath) as fh:
        data = json.load(fh)
    return data
