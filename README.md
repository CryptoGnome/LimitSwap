# LimitSwap
LimitSwap is a trading bot for UniSwap & Many Other DEXs. It has the ability to scan multiple pairs on uniswap and grab the price in realtime and make automated trading decisions based on the users settings [AKA: Limit Orders]


*This bot was built as a learning project for me to learn how to use Web.py, Erc20, & improve my coding skills please use at your own risk!*

&nbsp;
&nbsp;

## HOW TO INSTALL LimitSwap
There are 3 ways to install LimitSwap : 

&nbsp;
&nbsp;


### 1. Run The Python Code Locally [*this is most ideal and can work on any OS*]
Here is a tutorial step-by-step: 
- Download last LimitSwap code here : 
<img src="https://user-images.githubusercontent.com/70858574/145568534-e22c2887-d761-4fba-8dd0-f765b4300a6c.png" width="300">

- Unzip file
- Install Python on your computer : https://www.python.org/downloads/ 

**PLEASE ADD IT TO PATH BY CHECKING THIS OPTION:**

<img src="https://user-images.githubusercontent.com/70858574/145692350-b2cb248a-8888-4471-8a63-2b6654e9b671.png" width="500">

- Install Visual Studio : https://visualstudio.microsoft.com/fr/thank-you-downloading-visual-studio/?sku=Community&rel=17

Please install the default package and all those options :
![image](https://user-images.githubusercontent.com/70858574/145580447-bd648d6d-c3ce-4dd9-8527-84ecfb5f30cc.png)

- Open **Windows Powershell** (or Mac Terminal on MacOs)
- Navigate into the unzipped folder 
- Run command: `pip install -r requirements.txt`  --> this will install all the packages needed to run LimitSwap

==> And it's done! ✅

Simply **double-click on "LimitSwap.py"** and it will run, since you've installed Python 👍👍

&nbsp;

#### Pros and cons
🟢 : you are sure of the code that is running on your computer

🔴 : little bit complicated

&nbsp;
&nbsp;

### 2. Download the pre-compiled package [*This can lag behind current version*]
That we provide on the Release page : it's a .exe file that you can run on your computer.
https://github.com/CryptoGnome/LimitSwap/releases

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

#### Pros and cons
🟢 : easy to setup if you know Docker

🔴 : needs Docker

&nbsp;

&nbsp;

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
