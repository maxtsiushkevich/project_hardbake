# Project Harbake
## Hardbake is a powerful component easy-customizable intrusion detection system.

### To generate keys for Auth
``` openssl ecparam -genkey -name prime256v1 -noout -out private_key.pem ```

``` openssl ec -in private_key.pem -pubout -out public_key.pem ```
