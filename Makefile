.PHONY: build offline serve test
build:
	python3 -m pipelines.build
offline:
	python3 -m pipelines.build --offline
serve:
	python3 -m http.server 8000 -d docs
test:
	python3 -m pipelines.test