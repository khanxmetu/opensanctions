TS=$(shell date +%Y%m%d)

tmp:
	mkdir -p tmp

tmp/tabula.jar: tmp
	wget -O tmp/tabula.jar https://github.com/tabulapdf/tabula-java/releases/download/v1.0.5/tabula-1.0.5-jar-with-dependencies.jar
	touch tmp/tabula.jar

tmp/iso9362_bic.pdf: tmp
	wget -O tmp/iso9362_bic.pdf https://www.iso9362.org/bicservice/public/v1/bicdata/_pdf 
	touch tmp/iso9362_bic.pdf

tmp/iso.csv: tmp/tabula.jar tmp/iso9362_bic.pdf
	java -jar tmp/tabula.jar --pages 2-$(shell grep --text /Count tmp/iso9362_bic.pdf | sed 's/\/Count //') --format CSV tmp/iso9362_bic.pdf -o tmp/iso.csv

upload::
	gsutil cp tmp/* "gs://internal-data.opensanctions.org/iso9362_bic/$(TS)/"
