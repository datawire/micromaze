all: docker-images

VERSION=0.1.0

.ALWAYS:

docker-images: base-service-image

base-service-image: .ALWAYS
	docker build -t datawire/base-service:$(VERSION) .
	if [ -n "datawire/" ]; then \
		docker push datawire/base-service:$(VERSION); \
	fi
