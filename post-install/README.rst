===========================================
gvSIG batovi Activity Post-intall process
===========================================


This folder contains all supported *post-intall* actions implemented in gvSIG activity.


user-gvsig-home
================

Files of this folder will be **merged** (copy only files than no exists on target folder) with *~/gvSIG* folder of user intallation in first gvSIG activity execution.


After that this folder will be renamed to *user-gvsig-home.done*.


user-home
===========

Files of this folder will be **merged** (copy only files than no exists on target folder)  to *user home* folder.

After that this folder will be removed.

scripts
========

Excecutes contained scripts in first gvSIG activity execution. Only *Pyhon* (files ``.py``) and *Shell* (files ``.sh``) are allowed (other files will be ignored).

Before all execution this environ variables will be set:

* ``GVSIG_ACTIVITY``: root folder of gvSIG activity (usually ``~/Activities/org.gvsig.batovi.activity``)

* ``GVSIG_HOME``: root folder of gvSIG installation (usually ``$GVSIG_ACTIVITY/gvSIG``)

After the script excution will be renamed (adds ``.done``) to prevent future executions.

When all script were executed, this folder will be renamed (adds ``.done``).

See log file for problems in script executions.
