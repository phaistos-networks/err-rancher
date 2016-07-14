# Errbot Rancher module #
This is a basic module for managing rancher via chatops, namely using errbor.

## Setup ##
You need to set 3 env variables.  
- RANCHER_URL (i.e. http://my.server:8080)
- RANCHER_USER (User needs to have Owner permissions on Environments. Use API tab to generate)
- RANCHER_PASS

## Usage ##
Initial options: upgrade, finishupgrade, rollback, status  
To see available options / commands:
> !rancher help  


## License ##
WTFPL
