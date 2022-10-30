# nr7101 heat pump data to influx db

Scrappy script to pull data from my nr7101 7000i heat pumps and dump it to influx

Leverages [nr7101-thermostat-client-python](https://github.com/nr7101-thermostat/nr7101-thermostat-client-python) for scraping data and then mutates it from json to valid influx format