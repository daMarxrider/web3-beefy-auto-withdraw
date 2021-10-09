# Setup

## contract abi's

either:

 - put the abi of the contracts you want to use/query/whatever into a file in networks/whatever-chain-you're-using/abi_{contract_address}

 - add a api that gives you raw abi's of your chain into network_configs.json, you can check polygon and bsc for examples

        "abiUrl":"http://api.bscscan.com/api?module=contract&action=getabi&address=$address&format=raw"

    use $address as the uri-argument, the script will do the rest

# USAGE

place all the tokens you want to auto-withdraw, in case their beefy-strategy changes, into config.json.

## config fields

 - chainId
 - address: the address of the token you want to auto-withdraw
 - privateKey: you don't have to add one if you only want to listen for changes, HOWEVER if you want to withdraw the token automatically, you obviously need to it.
 - method: same as above + the method of the token you want to call, most likely "withdrawAll"
