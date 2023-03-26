# Собрать контейнер
docker-build:
	docker build -t speakerpy .

# Запустить контейнер
docker-run:
	docker run -it -v "$(PWD)/mp3:/app/mp3" -v "$(PWD)/books:/app/books" speakerpy

# Собрать документацию в Html
doc_to_html:
	cd ./docs/docs; make html

# Собрать документацию в TXT
doc_to_txt:
	lynx -dump ./docs/docs/build/html/index.html > ./docs/docs/build/html/index.txt
