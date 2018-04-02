# Intro
The coresyftools provide an easy and standard way to build, test and deploy tools for the Co-ReSyf platform.
It includes a packager that enables the user to test and pack (into a zip file) the tool files (run, manifest and other files).

## How to build and install coresyftools locally:
sudo python2.7 setup.py install

## How to create a new tool
1. Create a new folder with tool name;
2. Add the execution main script/executable and name it "run";
3. Create a manifest file and name it "[TOOL_NAME].manifest.json";
4. Create a "examples.sh" file with an example of a passing execution;
4. Add other files or dependencies required to run the tool.

## Example for testing and packaging tools:
Run the following command to execute the tool packager. If "examples.sh" includes a non local test product with the
respective URL from Sentinel Scientific Data Hub, the scihub credentials are used to retrieve it.

python2.7 coresyftools/coresyftools/packager.py --tool_dir coresyf_tool_folder/ --target_dir coresyftools/target --scihub_user [USERNAME] --scihub_pass [PASSWORD]
