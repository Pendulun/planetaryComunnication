PYTHON:= python

exhibitor: 
	${PYTHON} exhibitor.py ${ARGS}

emitter:
	${PYTHON} emitter.py ${ARGS}

server:
	${PYTHON} server.py ${ARGS}