# Kartový optimalizátor

Toto je aplikácia na optimalizovanie nákup kariet z internetového portálu magiccardmarket.eu. 


### Požiadavky

Potrebuje nainšalovaný Python3 a tieto knižnice:

* `beautifulsoup4`
* `requests`
* `unidecode`


### Riešitele

Optimizer internaly uses ILP solver to optimize and you need at least one installed and launchable from command line (for example in your windows `PATH`):
Optimalizátor interne používa ÚCP riešiteľ na hľadanie riešenia, a potrebuje aspoň jeden nainštalovaný a spustiteľný z príkazového riadku (napríklad vo windowse sa musí nachádzať v `PATH`)

* [SYMPHONY](https://projects.coin-or.org/SYMPHONY#DownloadandInstall)
* [SCIP](http://scip.zib.de/#download) - je pod [ZIB akademickou licensiou](http://scip.zib.de/academic.txt)
* GLPK - [binárka pre Windows](https://sourceforge.net/projects/winglpk/), [linux balíčky](https://en.wikibooks.org/wiki/GLPK/Linux_packages), alebo [kompilované zo zdrojového kódu](https://www.gnu.org/software/glpk/#TOCdownloading)
* [lp_solve](https://sourceforge.net/projects/lpsolve/files/lpsolve/) - treba stiahnúť súbor /<verzia>/lp_solve_<verzia>_exe_<platform>, kde <verzia> je posledná verzia programu (najnovšia je 5.5.2.5)
* [Gurobi](http://www.gurobi.com/downloads/download-center) - komerčný riešiteľ, zadarmo pre akademické použitie


### Použitie

Spúsťa sa z príkazového riadku ako `python optimize.py` s argumentami:


pozičné argumenty:

  `karty`:                 Karty na nakúpenia a ich počet vo formáte: počet karta


voliteľné argumenty:

* `-h, --help`:            Ukáže nápomoc
* `-s , --solver`:         Riešiteľ na použitie k optimalizácii
* `-t, --timelimit`:       Časový limit na riešenie ÚCP problému
* `-c, --country`:         Krajina do ktorej sa karty posielajú
* `-f, --file`:            Načíta počet a názvy kariet zo súbora
* `-wmps`:                 Vypíše mps problém do súbora


