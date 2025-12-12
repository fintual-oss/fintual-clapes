import os.path as op

# Resolve repo root as one level above this package
BASE_DIR = op.dirname(op.dirname(op.abspath(__file__)))

def output_dir() -> str:
    """
    Folder where result files are stored.
    """
    return op.join(BASE_DIR, "outputs")

def output_file(filename: str) -> str:
    """
    Full path for an output file inside 'outputs'.
    """
    return op.join(output_dir(), filename)
