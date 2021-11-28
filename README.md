
# LimitSwap
LimitSwap is a trading bot for UniSwap & Many Other DEXs. It has the ability to scan multiple pairs on uniswap and grab the price in realtime and make automated trading decisions based on the users settings [AKA: Limit Orders]


*This bot was built as a learning project for me to learn how to use Web.py, Erc20, & improve my coding skills please use at your own risk!*

#### Grab the Latest Release:
https://github.com/CryptoGnome/LimitSwap/releases



## 2021-11-28 Change (yaqub0r)

#### Added encryption of private keys in settings.json
No changes to current configuration file is necessary. When executing LimitSwap you will be asked if you want to encrypt your private keys:
- If you answer no you will get a warning reminding you of the danger of leaving your private keys unencrypted on disk. You will never be asked if you want to encrypt them again, but you will get warned on every run. If you change you mind later on, change the "ENCRYPTPRIVATEKEYS" setting to "true". On the next run you'll be prompted for a password and your keys will be encrypted.
- If you answer yes, you'll be prompted for a password. Your private keys will be encrypted and written to settings.json. After that you will need to supply the same password every time you run LimitSwap. 

#### Added ZERO trust private key recording
- If settings.json is using the default WALLET and PRIVATEKEY variables, or the variables are empty, LimitSwap will request you to enter your wallet and private key information and will optionally, but immediately, encrypt the private key and write the encrypted string to disk. Your private key is never written to disk in an unecrypted format.




## Developers 🔧
Want to help contribute to LimitSwap, reach out on telegram all you need to do is make changes or fix bugs and we will pay developer bounties in $LIMIT for helping make the bot batter!

## Links & Socials:

#### WiKi
https://limitswapv3.gitbook.io/limitswap/

#### Website:
https://www.limitswap.com/

#### Twitter:
https://twitter.com/LimitSwap

#### Telegram:
https://t.me/LimitSwap
