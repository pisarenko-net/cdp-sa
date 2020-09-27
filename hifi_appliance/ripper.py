
'''

daemon, just like the playback component.

triggered by command "query"

need to know whether the disc has been previously ripped, so db access
but we want db to be used in one place only, or?

don't want to retrieve meta information one more time -- get it from playback
module

but is this a good separation? why does ripper need to know so much about playback?

disc querying and meta extraction can be put into a separate module -- commander? then
commander would receive command "disc" and call query and look-up. ripper and playback
would receive the results

once, triggered, need to process tracks one by one:
 - create folder according to naming template (VA vs one artist)
 - name files according to naming template
 - store disc_id

send an update after processing each file, with complete track list

process tracks in order

store tracks in the library folder

NEXT:
 1. extract disc identification and querying into controller; commander
 triggers playback
 2. ripper scaffolding, assuming it is triggered by commander

'''