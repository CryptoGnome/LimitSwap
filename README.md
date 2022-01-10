# LimitSwap
LimitSwap is a trading bot for UniSwap & Many Other DEXs. It has the ability to scan multiple pairs on uniswap and grab the price in realtime and make automated trading decisions based on the users settings [AKA: Limit Orders]


*This bot was built as a learning project for me to learn how to use Web.py, Erc20, & improve my coding skills please use at your own risk!*

&nbsp;
&nbsp;

## HOW TO INSTALL LimitSwap
There are 3 ways to install LimitSwap : 

&nbsp;


### 1. Run The Python Code Locally [*this is most ideal and can work on any OS*]
Here is a tutorial step-by-step: 

&nbsp;

----------------------------------------

**FIRST PART : PRE-REQUISITES** 

----------------------------------------

- [x] Install Python on your computer : https://www.python.org/downloads/ 

**PLEASE ADD IT TO PATH BY CHECKING THIS OPTION:**

<img src="https://user-images.githubusercontent.com/70858574/145738124-e724c843-82d5-410d-b0b4-d7a9dda92258.png" width="500">

- [x] Install Visual Studio : https://visualstudio.microsoft.com/thank-you-downloading-visual-studio/?sku=Community&rel=17

Please install the default package and all those options :
![image](https://user-images.githubusercontent.com/70858574/145580447-bd648d6d-c3ce-4dd9-8527-84ecfb5f30cc.png)

- [x] NEW : LimitSwap now has colors to better display errors / success / etc. 

Follow this tutorial to activate colors on your Windows Command :
  - 1/ Launch "Regedit"
  - 2/ Go to [HKEY_CURRENT_USER \ Console]
  - 3/ Right click on white space / create new DWORD 32 bit key called `VirtualTerminalLevel` and set it to 1

<img src="https://user-images.githubusercontent.com/70858574/148842282-285a4c22-a569-44f3-9b93-ee7ff951c6ff.png" width="500">

&nbsp;

----------------------------------------

**SECOND PART : DOWNLOAD BOT AND INSTALL DEPENDENCIES** 

----------------------------------------

- [x] Download last LimitSwap code on the "Code" page https://github.com/tsarbuig/LimitSwap by clicking on Code > Download Zip : 
<img src="https://user-images.githubusercontent.com/70858574/148130738-ef447465-511a-41b8-bcf2-6766a41fdbb8.png" width="300">


- [x] Unzip file
  - [X] Go into the unzipped folder
  - [X] In the folder, push "Shift" on your keyboard, then do a right-click
  - [X] Click on "Open command windows here" or "Open Powershell windows here"
  
<img src="https://user-images.githubusercontent.com/70858574/148840931-ed9ae3d8-e045-43a8-a000-2a52e6f2b4c5.png" width="700">


- [x] It will open Windows command (or Powershell) in the right place, where all the files are located:

![image](https://user-images.githubusercontent.com/70858574/148841299-bfa53046-a8c5-4dd9-9fbe-dddc8f76877e.png)


- [x] Run command: `pip install -r requirements.txt`  
--> this will install all the packages needed to run LimitSwap


(🔥 if you have an error here, double check you have selected "Add Python to PATH" on the Python step. If you did not, uninstall Python and reinstall it checking the option "Add Python to PATH")

&nbsp;

✅ ✅ ✅ And it's done! ✅ ✅ ✅

&nbsp;

----------------------------------------

**LAST PART : RUN THE BOT** 

----------------------------------------
There are 2 ways to do that : 

- [x] Simply **double-click on "LimitSwap.py"** and it will run, since you've installed Python 👍👍

- [x] Or, in the Windows Command, run command: `python LimitSwap.py`  

This second option allows you to use parameters. For example, if you have several .json files and you want to choose which one to use :

`python LimitSwap.py -s settingsBSC.json -t tokensBSC.json`  

or

`python LimitSwap.py --benchmark`  

&nbsp;
&nbsp;

### 2. Download the pre-compiled package [*This can lag behind current version*]
That we provide on the Release page : it's a .exe file that you can run on your computer.
https://github.com/tsarbuig/LimitSwap/releases


- [x] Download last Zip file, for instance :

<img src="https://user-images.githubusercontent.com/70858574/145737351-c659185f-e1f5-4ede-b81e-3b03d0f900f9.png" width="200">

- [x] Unzip it
- [x] Open "tokens.json - Shortcut" and configure it for your needs
- [x] Open "Start LimitSwap.cmd" --> it will configure your settings.json

✅ ✅ ✅ And it's done! ✅ ✅ ✅

&nbsp; 

#### Pros and cons
🟢 : very easy to setup

🔴 : it's pre-compiled, so you cannot check the Source Code

&nbsp;
&nbsp;


### 3. With Docker

#### Requirements
MacOS and Windows users require Docker for Desktop https://www.docker.com/products/docker-desktop
Ubuntu Linux require Docker installed `sudo apt-get install docker.io`

#### Usage
Navigate into the bot directory and build the Docker image by executing the following command:

`docker build -t limit_swap_v4 .`

(For MacOS and Linux) Still within the main directory you can run Docker via:

`docker run --rm --name limit-swap_v4 -it -v $(pwd)/settings.json:/app/settings.json -v $(pwd)/tokens.json:/app/tokens.json limit_swap_v4`

(For Windows with Powershell)

`docker run --rm --name limit-swap_v4 -it -v $PWD/settings.json:/app/settings.json -v $PWD/tokens.json:/app/tokens.json limit_swap_v4`

If you wish to run the container in the background please include -d for detached.

The streaming container logs can be visualised with `docker logs -f limit_swap_v4`

To stop the bot `docker stop limit_swap_v4`


&nbsp;

&nbsp;


## Developers 🔧
Want to help contribute to LimitSwap, reach out on telegram all you need to do is make changes or fix bugs and we will pay developer bounties in $LIMIT for helping make the bot batter!


## Links & Socials

#### WiKi
https://limitswapv3.gitbook.io/limitswap/

#### Website:
https://www.limitswap.com/

#### Twitter:
https://twitter.com/LimitSwap

#### Telegram:
https://t.me/LimitSwap
