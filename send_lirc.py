import sys
import lirc

if len(sys.argv) < 3 or len(sys.argv) > 5:
    sys.stderr.write("Usage: simulate.py <remote> <key> [repeat [code ]]")
    sys.exit(1)

code = sys.argv[4] if len(sys.argv) >= 5 else 9
repeat = sys.argv[3] if len(sys.argv) >= 4 else 1
key = sys.argv[2]
remote = sys.argv[1]

with lirc.CommandConnection() as conn:
    reply = lirc.SimulateCommand(conn, remote, key, repeat, code).run()
if not reply.success:
    print(reply.data[0])
