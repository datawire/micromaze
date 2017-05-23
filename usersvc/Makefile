all: docker-images usersvc.yaml

VERSION=0.1.0

.ALWAYS:

docker-images: usersvc-image

usersvc-image: .ALWAYS
	docker build -t datawire/micromaze-user:$(VERSION) .
	if [ -n "datawire/" ]; then \
		docker push datawire/micromaze-user:$(VERSION); \
	fi
