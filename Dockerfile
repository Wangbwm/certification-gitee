FROM python:3.10

# 设置环境变量，这里假设我们总是构建生产环境的镜像
ENV ENV=pro

WORKDIR /app

RUN pip install --no-cache-dir --upgrade -r ../requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8081"]