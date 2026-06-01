import requests

API_KEY = "SyBQ06H2yR2RIEJn3"
URL = "https://api.seniverse.com/v3/weather/now.json"

def get_now_weather(city):
    params = {
        "key": API_KEY,
        "location": city,
        "language": "zh-Hans",
        "unit": "c"
    }
    res = requests.get(URL, params=params)
    data = res.json()
    if data.get("results"):
        now = data["results"][0]["now"]
        loc = data["results"][0]["location"]
        return {
            "城市": loc["name"],
            "天气": now["text"],
            "温度": now["temperature"],
            "湿度": now["humidity"],
            "风速": now["wind_speed"]
        }
    else:
        return None

# 测试
print(get_now_weather("伦敦"))
print(get_now_weather("tokyo"))
print(get_now_weather("纽约"))