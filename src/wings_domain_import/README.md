# Wings Domain Import
## Introduction
The Wings Domain Import is a simplified command line tool to import domains (workflows and tools) to existing Wings users,
simply by specifying:
* the path to the wings domain (containing the workflows and tools definition)
* the file containg the list of tools to be deployed (*NOTE:* this step is required because for unknown reasons the tools
are not correctly defined during the domain import).
* the tomcat XML file with the list of Wings users to deploy  

## Usage
1. Invoke the `wings_domain_import.py` script
`python wings_domain_import.py --wurl <wings_url> --idomain <path_to_zipped_domain> --ilist_tools <path_to_list_tools> --iusers <path_to_list_users>`

## Example
'python wings_domain_import.py --wurl https://wings.coresyf.eu/wings --idomain wings_domain_coresyf_user_pristine_2018_08.zip --ilist_tools list_tools_to_ship.txt --iusers tomcat-users.xml'
