import aiohttp
import urllib.parse
import json
from datetime import datetime
import logging

_LOGGER = logging.getLogger(__name__)

CONST_KOMMUNE_NUMMER = "Kommunenr"
CONST_APP_KEY = "RenovasjonAppKey"
CONST_URL_FRAKSJONER = (
    "https://norkartrenovasjon.azurewebsites.net/proxyserver.ashx?server="
    "https://komteksky.norkart.no/MinRenovasjon.Api/api/fraksjoner/"
)
CONST_URL_TOMMEKALENDER = (
    "https://norkartrenovasjon.azurewebsites.net/proxyserver.ashx?server="
    "https://komteksky.norkart.no/MinRenovasjon.Api/api/tommekalender?"
    "kommunenr=[kommunenr]&gatenavn=[gatenavn]&gatekode=[gatekode]&husnr=[husnr]"
)
CONST_APP_KEY_VALUE = "AE13DEEC-804F-4615-A74E-B4FAC11F0A30"

class MinRenovasjon:

    _calendar_list = []
    _fraction_types = {}

    def __init__(self, gatenavn, gatekode, husnr, kommunenr, date_format):
        self._gatenavn = self._url_encode(gatenavn)
        self._gatekode = gatekode
        self._husnr = husnr
        self._kommunenr = kommunenr
        self._date_format = date_format

    @staticmethod
    def _url_encode(string):
        string_decoded_encoded = urllib.parse.quote(urllib.parse.unquote(string))
        if string_decoded_encoded != string:
            string = string_decoded_encoded
        return string

    async def refresh_calendar(self):
        try:
            _LOGGER.debug("Starting calendar refresh")
            self.calender_list = await self._get_calendar_list()
            _LOGGER.debug("Calendar refresh completed successfully")
            _LOGGER.debug("Calendar list: %s", self.calender_list)
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to connect to Min Renovasjon API: %s", err)
            raise ConnectionError(f"Failed to connect to Min Renovasjon API: {err}") from err
        except json.JSONDecodeError as err:
            _LOGGER.error("Failed to parse response from Min Renovasjon API: %s", err)
            raise ValueError(f"Invalid response from Min Renovasjon API: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error occurred: %s", err)
            raise

    async def _get_from_web_api(self, url):
        header = {
            CONST_KOMMUNE_NUMMER: self._kommunenr,
            CONST_APP_KEY: CONST_APP_KEY_VALUE,
        }
        _LOGGER.debug("Requesting URL: %s", url)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=header, timeout=10) as response:
                _LOGGER.debug("API response status code: %s", response.status)
                response.raise_for_status()
                return await response.json(content_type=None)

    async def get_fraction_types(self):
        _LOGGER.debug("Fetching fractions")
        fractions_data = await self._get_from_web_api(CONST_URL_FRAKSJONER)
        self._fraction_types = {
            fraction['Id']: fraction
            for fraction in fractions_data
        }

    def get_fraction_name(self, fraction_id):
        return self._fraction_types.get(int(fraction_id), {}).get("Navn", f"Unknown fraction {fraction_id}")

    def get_fraction_icon(self, fraction_id):
        return self._fraction_types.get(int(fraction_id), {}).get("Ikon", "")

    async def _get_calendar_list(self):
        url = CONST_URL_TOMMEKALENDER.replace("[kommunenr]", self._kommunenr)
        url = url.replace("[gatenavn]", self._gatenavn)
        url = url.replace("[gatekode]", self._gatekode)
        url = url.replace("[husnr]", self._husnr)

        data = await self._get_from_web_api(url)
        _LOGGER.debug("Received calendar data: %s", json.dumps(data, indent=2))

        calendar_list = []
        for entry in data:
            try:
                fraction_id = entry["FraksjonId"]
                fraction_name = self.get_fraction_name(fraction_id)
                icon = self.get_fraction_icon(fraction_id)
                
                pickup_dates = entry.get('Tommedatoer', [])
                next_pickup = datetime.strptime(pickup_dates[0], "%Y-%m-%dT%H:%M:%S") if pickup_dates else None
                next_next_pickup = datetime.strptime(pickup_dates[1], "%Y-%m-%dT%H:%M:%S") if len(pickup_dates) > 1 else None

                calendar_entry = (
                    fraction_id,
                    fraction_name,
                    icon,
                    next_pickup,
                    next_next_pickup
                )
                calendar_list.append(calendar_entry)
                _LOGGER.debug("Processed calendar entry: %s", calendar_entry)
            except KeyError as e:
                _LOGGER.error(f"KeyError processing entry: {e}. Entry data: {entry}")
            except Exception as e:
                _LOGGER.error(f"Error processing entry: {e}. Entry data: {entry}")

        _LOGGER.debug("Processed %d calendar entries", len(calendar_list))
        return calendar_list

    def get_calender_for_fraction(self, fraksjon_id):
        for entry in self.calender_list:
            if entry[0] == int(fraksjon_id):
                _LOGGER.debug("Found calendar entry for fraction %s: %s", fraksjon_id, entry)
                return entry
        _LOGGER.warning("No calendar entry found for fraction %s", fraksjon_id)
        return None

    def format_date(self, date):
        if self._date_format == "None" or date is None:
            return date
        formatted_date = date.strftime(self._date_format)
        _LOGGER.debug("Formatted date %s to %s", date, formatted_date)
        return formatted_date
