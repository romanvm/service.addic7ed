lint:
	. .venv/bin/activate && \
	pylint service.subtitles.rvm.addic7ed/addic7ed service.subtitles.rvm.addic7ed/main.py

PHONY: lint
