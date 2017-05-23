all: prep base gruesvc usersvc mazesvc

.ALWAYS:

prep: .ALWAYS
	bash prep.sh "$(DOCKER_REGISTRY)"

base: .ALWAYS
	cd base && $(MAKE)

gruesvc: .ALWAYS
	cd gruesvc && $(MAKE)

usersvc: .ALWAYS
	cd usersvc && $(MAKE)

mazesvc: .ALWAYS
	cd mazesvc && $(MAKE)

clean: .ALWAYS
	sh clean.sh
