import requests
from lxml import html
from itertools import chain
import json
import datetime as DT
import argparse


class departureCityError(Exception):
    pass


class arrivalCityError(Exception):
    pass


class departureDateError(Exception):
    pass


class Scraper():
    path = 'http://www.flybulgarien.dk'

    def __init__(self, departureCity, arrivalCity, departureDate, adultsAndChildren=1):
        self.departureCity = departureCity
        self.arrivalCity = arrivalCity
        self.departureDate = DT.datetime.strptime(departureDate, "%d-%m-%Y").date()
        self.adulsAndChildren = adultsAndChildren

    class flyghts():
        def __init__(self, departure, outTime, inTime, fromFly, toFly, price, arrival):
            self.departure = departure
            self.outTime = outTime
            self.inTime = inTime
            self.fromFly = fromFly
            self.toFly = toFly
            self.price = price
            self.arrival = arrival

        def __str__(self):
            return 'Departure: {}, OutTime: {}, InTime: {}, FromFly: {}, ToFly: {}, Price: {}'.format(
                self.departure,
                self.outTime,
                self.inTime,
                self.fromFly,
                self.toFly,
                self.price
            )

    def getFlyghts(self):
        url_quote = self.path + '/en/search'
        params_quote = {
            'lang': 2,
            'departure-city': self.departureCity,
            'arrival-city': self.arrivalCity,
            'departure-date': DT.date.strftime(self.departureDate, "%d.%m.%Y"),
            'adults-children': self.adulsAndChildren
        }
        r_quote = requests.get(url=url_quote, params=params_quote)
        html_format = html.fromstring(r_quote.text)
        apiUrl = html_format.xpath('//iframe/@src')[0]
        r_api = requests.get(url=apiUrl)
        html_api = html.fromstring(r_api.text)
        listFlyghts = []

        table = html_api.xpath('//table[@id="flywiz_tblQuotes"]')[0]
        rows = iter(table.xpath('.//tr[count(td)>1]'))
        zip_rows = zip(rows, rows)
        for tr1, tr2 in chain(zip_rows):
            td1, td2 = tr1.xpath('.//td'), tr2.xpath('.//td')
            listFlyghts.append(Scraper.flyghts(td1[1].text, td1[2].text, td1[3].text, td1[4].text, td1[5].text,
                                               td2[1].text.split(':')[1].lstrip(), td2[2].text.split(',')[1].lstrip()))

        for i in listFlyghts:
            print(i)

    def getDepartureCity(self):
        Cities = ['CPH', 'BLL', 'PDV', 'BOJ', 'SOF', 'VAR']
        return sorted(Cities)

    def getCityArrival(self, departureCity):
        response = requests.get(self.path + '/script/getcity/2-' + departureCity)
        return json.loads(response.text)

    def getDates(self, departureCity, arrivalCity):
        dates = []
        data = {'code1': departureCity, 'code2': arrivalCity}
        response = requests.post(self.path + '/script/getdates/2-departure', data).text
        cleanResponse = response.split('-')[0].replace('[', ' ').replace(']', '').lstrip()
        for text in cleanResponse.split(' '):
            dates.append(DT.datetime.strptime(text[:-1], '%Y,%m,%d').date())
        return [i.isoformat() for i in dates]

    def startScraper(self):
        try:
            if self.departureCity not in self.getDepartureCity():
                raise departureCityError("This city in missing")
            if self.arrivalCity not in self.getCityArrival(self.departureCity):
                raise arrivalCityError("There is no flight to this city")
            if self.departureDate.isoformat() not in self.getDates(self.departureCity, self.arrivalCity):
                raise departureDateError("There are no dates on this route")
            self.getFlyghts()
        except (departureCityError, arrivalCityError, departureDateError) as errors:
            if isinstance(errors, departureCityError):
                print("This city in missing. Use the airport IATA from the list: " + str(self.getDepartureCity()))
            elif isinstance(errors, arrivalCityError):
                print("There is no flight to this city. Use the airport IATA from the list: " + str(
                    self.getCityArrival(self.departureCity)))
            elif isinstance(errors, departureDateError):
                print("There are no dates on this route. List of available dates: " + str(
                    self.getDates(self.departureCity, self.arrivalCity)))


def parse_user_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("departure", help="Departure airport IATA code")
    parser.add_argument("arrival", help="Arrival airport IATA code")
    parser.add_argument("departure_date", help="Departure date. Correct date format: %d-%m-%Y")
    parser.add_argument("child", nargs='?', default=1, help="Adults and children (default: 1)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_user_arguments()
    scraper = Scraper(args.departure, args.arrival, args.departure_date, args.child)
    scraper.startScraper()
