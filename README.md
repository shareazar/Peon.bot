# **Peon.bot** <a href="https://emoji.gg/emoji/SMOrc"><img src="https://cdn3.emoji.gg/emojis/SMOrc.png" width="32px" height="32px" alt="SMOrc"></a>
**Chatbot made with <a href="https://github.com/rasaHQ/rasa">Rasa</a> that collects logs, troubleshoots problems, and provides a list of the requested commands.**


## Features

### Collecting [mx utilization logs](https://documentation.meraki.com/MX/Monitoring_and_Reporting/Device_Utilization):
![](gifs/mx-logs.gif)

### Collecting [mr logs](https://documentation.meraki.com/Meraki_Internal/Support/Mules/INTERNAL%3A_Troubleshoot_Wireless_Clients_Activity):
![](gifs/mr-logs.gif)

### Tshooting mx/mr/ms being unreachable in the dashboard:
![](gifs/unreachable.gif)

### (in progress) Listing the commands:
![](gifs/find_commands.gif)


## Installation:
1) To get started, you'll need to make sure that Microsoft Visual C++ is installed for Windows or Xcode for MacOS. 
The full guide for Microsoft Visual C++ can be found [here](https://learn.microsoft.com/en-US/cpp/windows/latest-supported-vc-redist?view=msvc-160).<br>
Xcode can be downloaded [here](https://apps.apple.com/us/app/xcode/id497799835?mt=12)
2) Next, you'll want to have anaconda. You can download this from [here](https://www.anaconda.com/download#downloads);
3) Once these tools are installed you can install Rasa Open Source with the following commands:<br>
conda create --name TEST python==3.8<br>
conda activate TEST<br>
python -m pip uninstall pip<br>
python -m ensurepip<br>
python -m pip install -U pip<br>
pip install rasa==3.5.10<br>

You should now be able to confirm that Rasa is installed with the following command:<br>
rasa -h<br>

4) Once the above is done, open settings.txt in Peon.bot folder and add your username (firstname.lastname) into the "user=" field.
5) Ensure that your id_rsa key is in ~/.ssh/id_rsa folder. On Windows systems the full path of the file is usually C:\Users\\<firstname.lastname>\\.ssh\id_rsa"


## How to launch:
The chatbot consists of back-end (RASA + action server) and front-end (simple js run on python web server):
![](architecture.png)

You will need to run three servers on the computer in order to launch the bot.

RASA server:
1) open cmd.exe/terminal;
2) cd <path_to_the_peon.bot_folder>;
3) run the command 'conda actiavate TEST'
4) run the command 'rasa run --cors "*"'

Actions server:
1) open cmd.exe/terminal;
2) cd <path_to_the_peon.bot_folder>;
3) run the command 'conda actiavate TEST'
4) run the command 'rasa run actions'

Front-end server:
1) open cmd.exe/terminal;
2) cd <path_to_the_peon.bot_folder>;
3) run the command 'python -m http.server 8080'

Once the above is done, launch your web-browser and open localhost:8080 and have at it!
