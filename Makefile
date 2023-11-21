SOLARA_CONTAINER_NAME := solara-hw
SOLARA_APP_FILE := annotation_tool.py

.PHONY: docker-build
docker-build:
	docker build -t $(SOLARA_CONTAINER_NAME) .

.PHONY: docker-run
docker-run:
	docker run -p 8888:8888 --rm -it $(SOLARA_CONTAINER_NAME)

.PHONY: docker-stop
docker-stop:
	docker stop $(SOLARA_CONTAINER_NAME)

.PHONY: docker-clean
docker-clean: docker-stop
	docker rmi $(SOLARA_CONTAINER_NAME)

.PHONY: solara-run
solara-run:
	solara run --no-dev $(SOLARA_APP_FILE)
