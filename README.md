# cbtb

Collective behaviour and bio-hybrid results analysis

* A python package that includes:
   * Analysis of experimental results
   * Includes loaders for experimental results generated with 
     assisipy_utils exec tools
   * Also includes loader for the built-in assisipy.casu logfile 
   * code to compute indices including:
      * collective decision index
      * volatility index
   
* v0.6
* author: rob.mills@fc.ul.pt


### How do I get set up? ###

* Install with pip

  $ pip install --user --upgrade cbtb-0.6.tar.gz

* Install editable with pip

  $ git clone <repo.git> <the_path>
  $ cd !$
  $ pip install --editable .


* Dependencies: numpy, scipy, yaml
* For info_theory/libinfo, JIDT must be installed (the infodynamics.jar is
  needed).  See guide [https://github.com/jlizier/jidt/wiki/Installation].
  jpype is also needed (e.g. `sudo apt-get install python-jpype`)

  (pip doesn't well handle the fact that ubuntu's apt has installed python-numpy -- if that is how obtained... so these are not declared in the setup.py)






