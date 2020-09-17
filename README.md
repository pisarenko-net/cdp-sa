# hifi-appliance

The goal is to build a custom Hi-Fi appliance in a Sony chassis with a CD transport and additional custom features, such as an interface to NetMD Minidisc devices. This is similar to many other DIY network streamers. A commercial example of this is https://www.brennan.co.uk/.

*This is work in progress and does not function yet* (to be removed when no longer true).

## Design principles

 - small independent modules exchanging messages over a message queue
 - stateless (with allowance for caching)
 - relevant context is always passed along with a message
 - driven by state transitions
 - resilient to lost messages

## Major modules

Modules interact with each other via ZMQ topics. There two topics: `state` (state updates for all modules) and `command`.

 - playback -- controls playback and CD state transitions
 - ripper -- controls ripping process and its state transitions
 - commander -- accepts commands and decides whether to forward them depending on the state of other modules
 - display -- displays the most relevant information based on overall state
 - hci -- receives hardware interactions and turns them into commands
 - lirc -- receives infrared signals and turns them into commands
 - md\_search -- keeps looking for queued playlists to download to NetMD
 - md\_selector -- chooses a playlist to download given what's in the queue
 - md\_download -- downloads tracks to the NetMD device


## Dependencies

 - python-zmq
 - python-tornado

## Attribution

I'm reusing other people's work in here.
 - [codplayer](https://github.com/petli/codplayer) -- does almost exactly what I'm doing here. I've borrowed the ZMQ code and quite a few ideas.


## License

TBD
