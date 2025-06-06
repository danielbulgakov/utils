import os
import json
import fnmatch
import argparse, textwrap

#++++++++++++++++++++++++++++++++++++++++++++++++
# Utils
#++++++++++++++++++++++++++++++++++++++++++++++++

def dir_arg(path):
    if not os.path.exists(path):
        raise argparse.ArgumentError(f"Path does not exist: {path}")
    if not os.path.isdir(path):
        raise argparse.ArgumentError(f"Path exists but is not a directory: {path}")
    return path

def match_masks(filename, masks):
    if not masks:
        return True
    for mask in masks:
        if fnmatch.fnmatch(filename, mask):
            return True
    return False

def is_excluded_dir(dirname, excluded_dirs):
    if not excluded_dirs:
        return False
    return dirname in excluded_dirs

def is_excluded_file(filename, excluded_masks):
    if not excluded_masks:
        return False
    return any(fnmatch.fnmatch(filename, mask) for mask in excluded_masks)

#++++++++++++++++++++++++++++++++++++++++++++++++
# Config classes
#++++++++++++++++++++++++++++++++++++++++++++++++

def collect_files(base_dir
                , masks=None
                , save_type="path"
                , exclude_dirs=None
                , exclude_files=None):
    result = {}
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if not is_excluded_dir(d, exclude_dirs)]
        for file in files:
            if is_excluded_file(file, exclude_files):
                continue
            if not match_masks(file, masks):
                continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, base_dir)
            if save_type == "path":
                result[rel_path] = full_path
            elif save_type == "content":
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    result[rel_path] = f.read()
    return result

#++++++++++++++++++++++++++++++++++++++++++++++++
# Parse arguments
#++++++++++++++++++++++++++++++++++++++++++++++++

def get_args():
    parser = argparse.ArgumentParser(
        description=textwrap.dedent('''\
        Simple python script to create JSON file from directory.

        The generated JSON file will contain a dictionary where:
        - Key: filename
        - Value: Either the filepath or file content

        Primarily used to convert code projects into LaTeX documents.
        '''),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-d',
        '--directory',
        type=dir_arg,
        required=True,
        help="path to the directory from which we will make the dictionary"
    )
    parser.add_argument(
        '-o',
        '--output-file',
        required=True,
        help="path to the result file"
    )
    parser.add_argument(
        '-m',
        '--mask',
        help="match files with the specified mask, use | to pass more than one\n"
            +"ex: *.py|*.cpp"
    )
    parser.add_argument(
        '-t',
        '--save-type',
        choices=["path", "content"],
        help="save file info as filepath or file content (path=default|content)"
    )
    parser.add_argument(
        '-xdir',
        '--exclude-dirs',
        help="exclude directories by exact name, use | to separate multiple"
             "ex: venv|.git|build"
    )
    parser.add_argument(
        '-xfile',
        '--exclude-files',
        help="exclude files by mask, use | to separate multiple"
             "ex: *.log|*.tmp"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()

    masks = args.mask.split("|") if args.mask else None
    exclude_dirs = args.exclude_dirs.split("|") if args.exclude_dirs else None
    exclude_files = args.exclude_files.split("|") if args.exclude_files else None

    file_data = collect_files(
        base_dir=args.directory,
        masks=masks,
        save_type=args.save_type,
        exclude_dirs=exclude_dirs,
        exclude_files=exclude_files
    )

    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(file_data, f, indent=2, ensure_ascii=False)
