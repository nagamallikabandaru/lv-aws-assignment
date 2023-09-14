# AWS ASG and instance metrics

OS: Mac
Install Python 3.8 version on local - https://www.python.org/downloads/release/python-380/ Command to ensure that python3.8 is properly installed: python3 --version

Create Virtual Environment with Specific Python Version: python3.8 -m venv {env_name} </br>

Command for Eg: python3.8 -m venv env The virtual environment is now created and ready to use

Command to activate the environment: source env/bin/activate

Next step is the use pip to download all the required dependent libraries for your code When you install Python 3.8, pip should be automatically installed along with it. However, if you find that pip is missing or you need to reinstall it manually.

Command to ensure that pip is properly installed: pip3 --version

# Getting Started

pip3 install -r /path/to/requirements.txt


# Running the application 
python ecs.py <access_key> <secret_key>


Input required: aws_access_key and aws_secret_key

O/p: 

< Prints the running instance details >
**************TestCaseA-3*******************
< Prints if the running instance details are matching with the >
**************TestCaseA-1******************
< Verifies and prints whether the runnign instance count matched the desired capacity of the asg>
*********************************************
*****************TestCaseA-2********************
< prints whether instances are running in multi az>
*****************TestCaseB-1********************
< prints the next scheduled action of the given asg>
*********************************************
**************TestCaseB-2*******************
< Error or the asg instacnce metrcics>
*********************************************


