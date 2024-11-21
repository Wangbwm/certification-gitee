#
FROM python:3.10

#
WORKDIR /code

ENV ENV=pro

#
COPY ./requirements.txt /code/requirements.txt

#
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

#
COPY ./app /code/app

#
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8081"]