FROM python:3
ADD requirements.txt /
RUN pip install -r requirements.txt
ADD toDO.py /
CMD [ "python", "./toDO.py" ]
