#!/usr/bin/env python3

"""Weather from OpenWeatherMap."""

import os
import requests
import json
from datetime import datetime
from dateutil import tz
from dataclasses import dataclass, asdict
from pprint import pprint


class Weather:
    def __init__(self, current: tuple, forecast: tuple, *args, **kwargs):
        self.current = current
        self.forecast = forecast


class WeatherData:
    """Weather from OpenWeatherMap."""

    def __init__(self, units="imperial"):
        self.weather_api_key = os.environ['OPEN_WEATHER_API']
        self.postal_code = os.environ['POSTAL_CODE']
        self.base_url = 'https://api.openweathermap.org/data/2.5'
        self.units = units

        self.url = "".join(
            [f"{self.base_url}",
             "{}",
             f"?zip={self.postal_code},us&",
             f"APPID={self.weather_api_key}",
             f"&units={self.units}", ])

        self.current = self.current_data()
        self.forecast_hourly = self.forecast_hourly_data()
        self.forecast_daily = self.forecast_daily_data()

    def request_data(self, url):
        response = requests.get(url)
        results = json.loads(response.content)

        return results

    def current_data(self):
        url = self.url.format("/weather")
        return self.request_data(url)

    def forecast_hourly_data(self):
        url = self.url.format("/forecast")
        return self.request_data(url)

    def forecast_daily_data(self):
        url = self.url.format("/forecast/daily")
        return self.request_data(url)


@dataclass
class WeatherDataDay:
    """Weather Data for a given day."""

    datetime_utc: str
    datetime_local: datetime
    temp_current: float
    temp_hi_low: dict
    wind: float
    sun: dict
    humidity: int
    main_description: str
    description: str
    icon: str
    today: bool = False

    def __post_init__(self):
        self.utc_to_local()
        self.description = self.description.title()
        self.main_description = self.main_description.title()
        print(self.description)

    def todays_weather(self):
        return datetime.today().date() == self.datetime_local.date()

    def utc_to_local(self):
        from_zone = tz.tzutc()
        to_zone = tz.tzlocal()
        utc = datetime.utcfromtimestamp(int(self.datetime_utc))
        utc = utc.replace(tzinfo=from_zone)
        self.datetime_local = utc.astimezone(to_zone)
        self.today = self.todays_weather()
        self.datetime_local = self.datetime_local.strftime('%A, %B %d')


def parse_weather_data(data):
    datetime_utc = data['dt']
    datetime_local = data['dt']
    main_description = data['weather'][0]['main']
    description = data['weather'][0]['description']
    icon = data['weather'][0]['icon']
    try:
        temp_current = data['temp']['day']
        temp_hi_low = {'high': data['temp']['max'],
                       'low': data['temp']['min'], }
        wind = data['speed']
        sun = None
        humidity = data['humidity']
    except KeyError:
        temp_current = data['main']['temp']
        temp_hi_low = {'high': data['main']['temp_max'],
                       'low': data['main']['temp_min'], }
        wind = data['wind']['speed']
        sun = {'rise': data['sys']['sunrise'],
               'set': data['sys']['sunset'], }
        humidity = data['main']['humidity']
    wd = WeatherDataDay(
        datetime_utc=datetime_utc,
        datetime_local=datetime_local,
        main_description=main_description,
        description=description,
        icon=icon,
        temp_current=temp_current,
        temp_hi_low=temp_hi_low,
        wind=wind,
        sun=sun,
        humidity=humidity
    )
    return wd


def data(get_api_data):
    """Get Weather data.

    For testing I used pickle to
    """
    import pickle
    GET_API_DATA = get_api_data
    if GET_API_DATA:
        weather_data = WeatherData()
        with open('today_weather_data.tmp', 'wb+')as f:
            pickle.dump(weather_data, f)
    else:
        with open('today_weather_data.tmp', 'rb') as f:
            weather_data = pickle.load(f)
    return weather_data


def main():
    """Get Weather Data."""
    weather_data = data(get_api_data=False)
    current_data = parse_weather_data(weather_data.current)
    forecast_data = [asdict(parse_weather_data(data))
                     for data in weather_data.forecast_daily['list']]

    return Weather(current=asdict(current_data),
                   forecast=forecast_data)


if __name__ == "__main__":
    with open('data/data.json', 'w') as fout:
        json.dump(main().__dict__, fout, indent=4)
