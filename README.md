# hifi-appliance

The goal is to build a custom Hi-Fi appliance with a CD transport and additional custom features, such as an interface to NetMD Minidisc devices. This is similar to many other DIY network streamers. A commercial example of this is https://www.brennan.co.uk/.

## Design principles

 - small independent modules exchanging messages over a message queue
 - stateless (with allowance for caching)
 - relevant context is always passed along with a message
 - driven by state transitions
