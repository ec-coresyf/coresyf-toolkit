# Wings Shipper
## Introduction
The Wings Shipper is a simplified command line tool to deploy applications to Wings, simply by specifying the path to the tool.

## Usage
1. Fill the `wings_config.json` file with the URL, Domain, Username and Password to access wings
2. Alternatively, you can pass these parameters by input;
3. Invoke the `wings_shipper.py` script (see invokation examples for details)
4. The component should be available through wings

## Invokation Examples
### Specifying configuration in the Config File
`python wings_shipper.py --ipath <path_to_zipped_tool>`

### Specifying configuration in command line
`python wings_shipper.py --ipath <path_to_zipped_tool> --wurl <wings_url> --wdomain <wings_domain> --wuser <wings_username> --wpass <wings_password>`