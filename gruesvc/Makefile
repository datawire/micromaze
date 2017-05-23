all: docker-images gruesvc.yaml

VERSION=0.1.0

.ALWAYS:

docker-images: gruesvc-image

gruesvc-image: .ALWAYS
	docker build -t datawire/micromaze-grue:$(VERSION) .
	if [ -n "datawire/" ]; then \
		docker push datawire/micromaze-grue:$(VERSION); \
	fi
