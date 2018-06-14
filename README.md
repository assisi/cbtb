# cbtb
Collective behaviour and bio-hybrid results analysis

* A python package that is for: 
   * Analysis of experimental results
   * Includes loaders for experimental results generated with assisipy_utils
     exec tools

Includes:
* code to compute indices including:
   * collective decision index
   * volatility index

   
* v0.4

* author: rob.mills@fc.ul.pt



### How do I get set up? ###

* Install with pip
  $ pip install --user --upgrade cbtb-0.4.tar.gz

* Install editable with pip
  $ git clone <repo.git> <the_path>
  $ cd !$
  $ pip install --editable .


* Dependencies: numpy, scipy, yaml

  (pip doesn't well handle the fact that ubuntu's apt has installed python-numpy -- if that is how obtained... so these are not declared in the setup.py)






