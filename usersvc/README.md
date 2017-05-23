micromaze -- a simple maze app built using microservices
========================================================

This is a simple application using multiple microservices. In the world of micromaze, users and grues wander around in a maze...

...or, at least, that's how things will work later. Right now, there's very little here here.

Contact Flynn <flynn@datawire.io> with questions.

Building
--------

`make DOCKER_REGISTRY=registry-info` should Do The Right Thing.

If `registry-info` is `-`, no `docker push` is done. This is probably correct only if you're using Minikube.

If `registry-info` is something else, it will be used as the registry prefix for `docker push`, e.g.

```
make DOCKER_REGISTRY=dwflynn
```

will use the `dwflynn` organization in DockerHub.

`make clean` will clean everything up.

