all:
	mkdir -p build
	python src/genapidoc.py ../pyzui > build/apidoc.tex
	cp src/manual.tex build/
	cd build && pdflatex manual && pdflatex manual
	cp build/manual.pdf .

clean:
	rm -rf build/
