# SPDX-FileCopyrightText: Thomas Breitner
#
# SPDX-License-Identifier: CC0-1.0

.PHONY: requirements

help:
	@echo "requirements - Update or created the pip requirements files"

requirements:
	python3 -m pip install --upgrade pip-tools pip wheel setuptools
	python3 -m piptools compile --generate-hashes --allow-unsafe --upgrade requirements.in
	python3 -m piptools compile --generate-hashes --allow-unsafe --upgrade requirements-dev.in
