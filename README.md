# Min Renovasjon Integration for Home Assistant

This custom integration allows you to integrate Min Renovasjon waste collection data into your Home Assistant instance. It provides sensors for each waste fraction, showing the next collection date.

## Features

- Automatically fetches waste collection data from Min Renovasjon API
- Creates sensors for each waste fraction (e.g., paper, residual waste, food waste)
- Displays the next collection date for each fraction
- Updates data periodically (configurable: 1-168 hours, default: 24 hours)
- Calendar integration showing upcoming collection events
- Cached fraction types to reduce API calls
- Optimized event processing to avoid redundant calculations

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=actstorms&repository=ha-min-renovasjon&category=integration)

### Manual Installation

1. Download the `min_renovasjon` folder from this repository.
2. Copy the folder to your `custom_components` directory in your Home Assistant configuration directory.
3. Restart Home Assistant.

## Configuration

To add Min Renovasjon to your Home Assistant instance:

1. Go to **Settings** -> **Devices & services**.
2. Click the **"+ ADD INTEGRATION"** button.
3. Search for "Min Renovasjon" and select it.
4. Enter your address (e.g., `Mingate 10`).
5. If multiple addresses match, select the correct one from the list.
6. Confirm the address and optionally adjust the update interval (default: 24 hours).
7. Click "Submit" to add the integration.

The integration will automatically look up your street code, county ID, and other required information using the official Norwegian address database (Geonorge).

## Usage

After configuration, the integration will create:

### Sensors
Individual sensors for each waste fraction showing next collection date:
- `sensor.min_renovasjon_[fraction_name]`

### Calendar
A calendar entity showing upcoming waste collection events:
- `calendar.min_renovasjon_collection`

The state of each sensor will be the date of the next collection for that fraction. Additional attributes include days until collection and next collection date.

## Configuration Options

- **Update Interval**: Control how often the integration fetches new data (1-168 hours). Default is 24 hours.
- **Address Lookup**: The integration uses the official Norwegian address database (Geonorge) to automatically find your street code and municipality ID.

## Troubleshooting

If you encounter any issues:

1. Check the Home Assistant logs for any error messages related to Min Renovasjon.
2. Ensure that your address is entered correctly and can be found in the Norwegian address database.
3. Try searching for your address at [https://ws.geonorge.no/adresser/v1/sok?sok=your+address](https://ws.geonorge.no/adresser/v1/sok?sok=Min+Gate+12) to verify it exists.
4. Verify that your municipality is supported by the Min Renovasjon service.
5. Try adjusting the update interval if you're experiencing issues.

## Contributing

Contributions to improve the integration are welcome! Please feel free to submit pull requests or open issues for any bugs or feature requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration is not officially associated with or endorsed by Min Renovasjon or Norkart AS. It is a community-driven project to integrate Min Renovasjon data with Home Assistant.