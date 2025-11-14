#!/bin/bash

# This script removes all '<' and '>' characters from .tsv files
# in the current directory only, ignoring subdirectories.

echo "Looking for .tsv files in the current folder..."

# Loop over all files ending in .tsv in the current directory.
# The shell glob '*.tsv' only matches files in this folder,
# automatically ignoring any subfolders.
for file in *.tsv; do

  # Check if the glob found a matching file (and it's a regular file)
  # This prevents errors if no .tsv files exist.
  if [ -f "$file" ]; then
    echo "Processing: $file"

    # Use sed to perform in-place editing.
    # -i '' is the required syntax for macOS (BSD sed)
    #         to edit a file in-place without creating a backup.
    # 's/[<>]//g' means:
    #   s = substitute
    #   [<>] = any character in this set (either < or >)
    #   // = replace it with nothing
    #   g = global (do it for every match, not just the first one on a line)

    sed -i '' 's/[<>]//g' "$file"
  fi
done

echo "Done."