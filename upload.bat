@echo off
rem FOR TEST
rem python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
rem FOR DIST
python -m twine upload dist/*