all: docker-images mazesvc.yaml

VERSION=0.1.0

.ALWAYS:

docker-images: mazesvc-image

mazesvc-image: .ALWAYS
	docker build -t datawire/micromaze-maze:$(VERSION) .
	if [ -n "datawire/" ]; then \
		docker push datawire/micromaze-maze:$(VERSION); \
	fi
