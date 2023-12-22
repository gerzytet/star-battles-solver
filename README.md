# Star battles solver!

Run the main.py file to solve a puzzle.  When asked for a puzzle file name, enter a name in the puzzles directory.

# Puzzle file format

There are 2 formats currently supported, distinguished by the first line of the file.

"online" is a puzzle from star-battles.com.  The second line of the file is the number of stars per row and column, and the third line is the contents of the "task" variable on the webpage, which can be seen using a javascript console.

"classic" is meant for manual entry of puzzles.  The second line is the number of stars, and the lines after that describe the puzzle grid.  The letters define where the regions are in the puzzle: 2 tiles that have the same letter are in the same connected region.

# TODO

- Improve the algorithm to be able to solve most star battles puzzle without resorting to bifurcation.
- Add documentation describing all of the steps
- Improve file formats to support partially solved puzzles
- Add file format for star battles infinity app's "export puzzle" feature
