# Card optimizer

This is application for optimalizing shopping list for cards from magiccardmarket.eu. 


### Requirments

Requires Python3 to launch with these packages installed:

* `beautifulsoup4`
* `requests`
* `unidecode`


### Solvers

Optimizer internaly uses ILP solver to optimize and you need at least one installed and launchable from command line (for example in your windows `PATH`):

* [SYMPHONY](https://projects.coin-or.org/SYMPHONY#DownloadandInstall)
* [SCIP](http://scip.zib.de/#download) - is under [ZIB academic license](http://scip.zib.de/academic.txt)
* GLPK - [binary for Windows](https://sourceforge.net/projects/winglpk/), [linux packages](https://en.wikibooks.org/wiki/GLPK/Linux_packages), or [compile from source](https://www.gnu.org/software/glpk/#TOCdownloading)
* [lp_solve](https://sourceforge.net/projects/lpsolve/files/lpsolve/) - download a /<version>/lp_solve_<version>_exe_<platform> file, where <version> is the lastest version (5.5.2.5 as of writing this)
* [Gurobi](http://www.gurobi.com/downloads/download-center) - commercial program, free for academic use


### Usage

Simply call `python optimize.py` from command line / bash

positional arguments:

  `cards`:                 Cards to buy and their quantities in format: amount card

optional arguments:

* `-h, --help`:            Show help message and exit
* `-s , --solver`:         Solver to use for optimizing
* `-t, --timelimit`:       Timelimit for solving ILP problem
* `-c, --country`:         Country to which ship cards
* `-f, --file`:            Read amount and card names from file
* `-wmps`:                 Write the mps problem to file


