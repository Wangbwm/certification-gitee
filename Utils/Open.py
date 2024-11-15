# 请求地址
from datetime import datetime
import requests

url = "http://213.113.250.175:4200/api/realtime/ActiveControl"
# 默认账号
username = "lc"
password = "Siteweb@2024"
# 请求标头
headers = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-cn,zh;q=1",
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiLnu7XpmLPmnY7otoUiLCJnZW5lcmF0ZVRpbWUiOjE3MjU0MTQzNTM2MjQsInVzZXJJZCI6MjkwMDAwMDk5LCJsb2dvbklkIjoibGMiLCJyb2xlIjoiMjkwMDAwMDIxIiwicGVyc29uSWQiOjI5MDAwMDA5OSwibmVlZFJlc2V0UHdkIjpmYWxzZSwibG9naW5UeXBlIjoid2ViIn0.V26NdEqo46ZVbxND-MePGGfYIjIZhhf-uPq6lzypbitgg9NlM1EnzVSUqX7W4o-JS-qSHrS4wCsyR4DvHlChDgSWg85kZrD_55YRo7V91oh17cHBLCBc2JPL5FDf9k2AdeyvfHbGbn2HZPLqrF-oDimNwrY-1EdM79VbVB4TlmhFmeyi1tYuIsbEgjKLUuKOLB5TrZ2XGu-YZFP1JBqs9oVJfUL2b1YwKHmWzj6KRUnLDb1ZfJ2QlbBdOqNna4bpz9ub2unnv63pF30sUkbc8c-3otXZmrTYiWQSSRLBOUEMXjIM5TddWm4cIvDdi3362Sm08nEeZgxPSazlX597xQ",
    "Cache-Control": "no-cache",
    "Content-Type": "application/json",
    "Host": "213.113.250.175:4200",
    "Origin": "http://213.113.250.175:4200",
    "Pragma": "no-cache",
    "Proxy-Connection": "keep-alive",
    "Referer": "http://213.113.250.175:4200/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}


def send_open_request(stationId, equipmentId, controlid, setvalue):
    # 获取当前时间
    current_time = datetime.now()
    # 格式化时间为指定格式2024-10-12T17:08:12
    formatted_time = current_time.strftime("%Y-%m-%dT%H:%M:%S")
    params = {
        "stationId": stationId,
        "equipmentId": equipmentId,
        "controlid": controlid,
        "setvalue": setvalue,
        "startTime": formatted_time,
        "description": "李超测试开门",
        "username": username,
        "password": password
    }
    # 发送POST请求
    response = requests.post(url, headers=headers, params=params)

    # 打印响应结果
    print(str(stationId) + "--" + str(equipmentId) + "--" + str(response.status_code) + "--" + response.text)
    response.close()
    if response.status_code == 200:
        return True, "开门成功"
    return False, "开门失败"
