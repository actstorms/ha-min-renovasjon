# Min Renovasjon Integration for Home Assistant

This custom integration allows you to integrate Min Renovasjon waste collection data into your Home Assistant instance. It provides sensors for each waste fraction, showing the next collection date.

## Features

- Automatically fetches waste collection data from Min Renovasjon API
- Creates sensors for each waste fraction (e.g., paper, residual waste, food waste)
- Displays the next collection date for each fraction
- Updates data periodically (default: every hour)

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=actstorms&repository=ha-min-renovasjon&category=integration)

### Manual Installation

1. Download the `min_renovasjon` folder from this repository.
2. Copy the folder to your `custom_components` directory in your Home Assistant configuration directory.
3. Restart Home Assistant.

## Get Street code and county id
Can be found with this REST-API call.
```
https://ws.geonorge.no/adresser/v1/sok?sok=Min%20Gate%2012
```
"street_code" equals to "adressekode" and "county_id" equals to "kommunenummer".

## Configuration

To add Min Renovasjon to your Home Assistant instance:

1. Go to Configuration -> Integrations.
2. Click the "+ ADD INTEGRATION" button.
3. Search for "Min Renovasjon" and select it.
4. Enter the required information:
   - Street Name
   - Street Code
   - House Number
   - County ID
5. Click "Submit" to add the integration.

## Usage

After configuration, the integration will create sensors for each waste fraction. These sensors will show up in your Home Assistant as:

- `sensor.min_renovasjon_[fraction_name]`

The state of each sensor will be the date of the next collection for that fraction.

## Troubleshooting

If you encounter any issues:

1. Check the Home Assistant logs for any error messages related to Min Renovasjon.
2. Ensure that your address information is correct.
3. Verify that you can access the Min Renovasjon service from your location.

## Contributing

Contributions to improve the integration are welcome! Please feel free to submit pull requests or open issues for any bugs or feature requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration is not officially associated with or endorsed by Min Renovasjon or Norkart AS. It is a community-driven project to integrate Min Renovasjon data with Home Assistant.