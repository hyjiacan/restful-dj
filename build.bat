@echo off
rmdir /S /Q dist
rmdir /S /Q build
rmdir /S /Q restful_dj.egg-info
python setup.py sdist bdist_wheel