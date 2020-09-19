from hifi_appliance.meta import LocalMeta


track_list = [
	'/mnt/music/The Many Faces of Daft Punk/01 Space - Magic Fly.flac',
	'/mnt/music/The Many Faces of Daft Punk/02 Cerrone - Supernature.flac',
	'/mnt/music/The Many Faces of Daft Punk/03 Acos CoolKAs - Free Flight (Acos Coolkas Synth Touch mix).flac',
	'/mnt/music/The Many Faces of Daft Punk/04 Whispers - And the Beat Goes On.flac',
	'/mnt/music/The Many Faces of Daft Punk/05 WaR - You Got the Power.flac',
	'/mnt/music/The Many Faces of Daft Punk/06 Space - Carry On, Turn Me On.flac',
	'/mnt/music/The Many Faces of Daft Punk/07 Sare Havlicek - White Russian (Lazy Summer).flac',
	'/mnt/music/The Many Faces of Daft Punk/08 Architeq - Christine.flac',
	'/mnt/music/The Many Faces of Daft Punk/09 Oliver Cheatham - Get Down Saturday Night.flac',
	'/mnt/music/The Many Faces of Daft Punk/10 The Sugarhill Gang - Rapper’s Delight.flac',
	'/mnt/music/The Many Faces of Daft Punk/11 Peach - D.I.S.C.O..flac',
	'/mnt/music/The Many Faces of Daft Punk/12 Gibson Brothers - Cuba.flac'
]

disc_id = 'VYyHlY0Pj.OzVIZ2O08uuzsFOdw-'

client = LocalMeta()

print(client.query(disc_id, track_list))