"""
Name pools for adventurer generation.

Each class has a list of first names. Combined with the shared surname list,
this produces 10,000+ unique name combinations per class.

Clerics use a title + given name + surname pattern.
"""

FIGHTER_NAMES = [
    "Valerius", "Galen", "Rurik", "Thaddeus", "Elira", "Brynn", "Kord", "Sigrid",
    "Aldric", "Marta", "Brom", "Cassian", "Hilde", "Tormund", "Freya", "Gareth",
    "Iona", "Lucan", "Petra", "Wulfric", "Astrid", "Corwin", "Desmond", "Gunhild",
    "Harald", "Leofric", "Moira", "Osric", "Rowena", "Sven", "Ulf", "Yara",
    "Baldric", "Cedric", "Dunstan", "Eirik", "Fenris", "Greta", "Helga", "Ingrid",
    "Jarl", "Katla", "Lothar", "Magnus", "Nessa", "Orla", "Ragnar", "Solveig",
    "Thyra", "Viggo",
]

CLERIC_TITLES = [
    "Brother", "Sister", "Father", "Mother", "Deacon", "Priestess",
    "Friar", "Acolyte", "Prior", "Abbess", "Confessor", "Elder",
]

CLERIC_GIVEN_NAMES = [
    "Malric", "Mirabel", "Seraphine", "Aldric", "Theron", "Yara",
    "Cedric", "Isolde", "Anselm", "Brigid", "Clement", "Daria",
    "Erasmus", "Felicity", "Godric", "Helena", "Ivo", "Juliana",
    "Konrad", "Livia", "Marius", "Nerissa", "Osmund", "Perpetua",
    "Quentin", "Rosalind", "Simeon", "Theodora", "Ulric", "Verity",
    "Wren", "Ximena", "Yorick", "Zelda", "Ambrose", "Beatrix",
    "Cassius", "Dorothea", "Edmund", "Fiona", "Gertrude", "Hugh",
    "Iris", "Jerome", "Katarina", "Lazarus", "Magdalena", "Norbert",
    "Ottilia", "Prudence",
]

MAGIC_USER_NAMES = [
    "Kael", "Vespera", "Tamsin", "Mordecai", "Isolde", "Zephyr", "Arcanus",
    "Thalassa", "Oberon", "Selene", "Balthazar", "Circe", "Demetrius", "Elara",
    "Faust", "Gwendolyn", "Hesper", "Ignatius", "Jinx", "Kallistos",
    "Lysander", "Morgana", "Nocturne", "Ophelia", "Prospero", "Quintessa",
    "Ravenna", "Silas", "Thessaly", "Umbra", "Vivienne", "Wystan",
    "Xanthus", "Ysolde", "Zenobia", "Alduin", "Bellatrix", "Corvus",
    "Desdemona", "Endymion", "Faelan", "Grimoire", "Hypatia", "Icarus",
    "Jadis", "Kairos", "Lucasta", "Melisande", "Nephele", "Orryn",
]

ELF_NAMES = [
    "Lirael", "Sylwen", "Eldrin", "Aelindra", "Thalion", "Caelum", "Elowen",
    "Arannis", "Betharian", "Celenya", "Daelith", "Eryndor", "Faelivrin",
    "Galadhon", "Hestiel", "Ildraneth", "Jessamine", "Kaelithar", "Lorindar",
    "Mirethiel", "Naelindra", "Orophin", "Phaedril", "Quelindra", "Rethilion",
    "Saelorien", "Tinariel", "Uruvion", "Vaelindra", "Wynessil", "Xilanthiel",
    "Yavaniel", "Zephiriel", "Aerendyl", "Brethilwen", "Cirthandor", "Duilinel",
    "Ecthelion", "Finduilas", "Gilraen", "Halethiel", "Idhrindel", "Jennaril",
    "Kelariel", "Luthindel", "Maethoriel", "Nimrodel", "Orenthil", "Pelendur",
    "Quessariel",
]

DWARF_NAMES = [
    "Borin", "Durgan", "Helga", "Thorin", "Gimra", "Brokk", "Dagna",
    "Balin", "Cruach", "Dolgrim", "Embla", "Fargrim", "Grunda", "Harbek",
    "Ilga", "Jarnbjorn", "Korvek", "Lofar", "Muradin", "Nori",
    "Orsik", "Piktra", "Rukhash", "Skaldi", "Thrain", "Ulfhild",
    "Vondal", "Whurbin", "Yurga", "Zarek", "Audild", "Bruenora",
    "Cattibrie", "Duergar", "Eitri", "Flintara", "Glorin", "Hergrim",
    "Ingra", "Jothra", "Kelda", "Lothbrok", "Magni", "Njala",
    "Okri", "Pyrite", "Quartzin", "Rogni", "Stonilda", "Torunn",
]

HOBBIT_NAMES = [
    "Milo", "Fira", "Pip", "Rosie", "Tuck", "Bramble",
    "Aldagrim", "Belladonna", "Celandine", "Drogo", "Eglantine", "Folco",
    "Goldenberry", "Hamfast", "Iris", "Jolly", "Kira", "Lobelia",
    "Marigold", "Nob", "Odo", "Peony", "Robin", "Samwise",
    "Tansy", "Ulmo", "Violet", "Willow", "Yarrow", "Zinnia",
    "Adelard", "Bungo", "Camellia", "Dodinas", "Esmeralda", "Ferumbras",
    "Gorbadoc", "Hilda", "Isembold", "Jago", "Lalia", "Merimas",
    "Nymphadora", "Otto", "Primula", "Rosamunda", "Sancho", "Tolman",
    "Wilibald", "Pansy",
]

SURNAMES = [
    # Original 20
    "Swiftblade", "Stonefist", "Dawnstar", "Underbough", "Moonshadow",
    "Starfall", "Oakenshield", "Silverleaf", "Stonehammer", "Nightshade",
    "Axeborn", "Ironbeard", "Quickfoot", "Firebrand", "Stormcrow",
    "Brightwater", "Shadowmend", "Thornwall", "Willow", "Bramblewood",
    # Nature
    "Ashford", "Birchhollow", "Cedarfall", "Deeproot", "Elmgrove",
    "Fernwalker", "Glenmore", "Hawthorne", "Ivywood", "Juniper",
    "Knotwood", "Larchfield", "Mossbank", "Nettlecroft", "Oakheart",
    "Pinecrest", "Reedmere", "Sedgewick", "Thornbury", "Willowmere",
    # Stone & metal
    "Anvilstrike", "Boulderback", "Coppermine", "Dustforge", "Embersteel",
    "Flintlock", "Granitejaw", "Hammersong", "Ironvein", "Jasperhold",
    "Keystrike", "Leadenfoot", "Mithrilhand", "Nickelbright", "Obsidianward",
    "Pewtermark", "Quartzridge", "Rusthelm", "Steelmantle", "Tinderbox",
    # Combat & war
    "Battleborn", "Coldsteel", "Dreadmace", "Edgewalker", "Fireshield",
    "Grimward", "Halfsworn", "Ironwill", "Javelin", "Knightsbane",
    "Lanceguard", "Morningstar", "Nightwatch", "Oathkeeper", "Pikeworth",
    "Quiverfull", "Razorwind", "Shieldwall", "Trueshot", "Valorheart",
    # Mystical
    "Arcwright", "Banewhisper", "Crystalveil", "Dreamweaver", "Enchantwood",
    "Frostmantle", "Gloomspell", "Hexward", "Inkbloom", "Jadecaster",
    "Kindlespark", "Lorekeeper", "Moonweave", "Nether", "Oraclebloom",
    "Prismlight", "Quietstorm", "Runecarver", "Spellforge", "Twilightmere",
    # Geography
    "Blackmoor", "Cliffhanger", "Dalewood", "Eastmarch", "Fallcrest",
    "Greenvale", "Hilltopper", "Isleborn", "Knollcroft", "Lakeside",
    "Marshwalker", "Northwind", "Overhill", "Plainrider", "Ridgewood",
    "Southgate", "Tallfield", "Underdale", "Valekeeper", "Westford",
    # Character
    "Alesinger", "Braveheart", "Cleverhand", "Dawnriser", "Everjoy",
    "Fairweather", "Goodbarrel", "Hearthstone", "Idlebrook", "Jestwind",
    "Kindlewick", "Lightfoot", "Merrydale", "Nimblefingers", "Oddstone",
    "Proudfoot", "Quietbrook", "Reddawn", "Strongbow", "Truepenny",
    # Dark & mysterious
    "Ashenbane", "Blackthorn", "Crowfeather", "Darkhollow", "Evenfall",
    "Fogbane", "Gravewind", "Hollowborn", "Ironmask", "Jackalward",
    "Knightfall", "Longbarrow", "Mourncrest", "Nightveil", "Omenborn",
    "Plagueward", "Ravenscroft", "Shadowglen", "Tombward", "Umbralith",
    # Creature
    "Bearmantle", "Crowsong", "Dragonbane", "Eaglecrest", "Foxglove",
    "Griffonclaw", "Hawkstone", "Ivoryhorn", "Jackalope", "Krakenborn",
    "Lionheart", "Mothwing", "Nighthawk", "Owlwatch", "Phoenixash",
    "Ravenmark", "Serpentcoil", "Tigerseye", "Unicornmane", "Vipersting",
    # Craft & trade
    "Barrelmaker", "Candlewright", "Dyemaker", "Farrier", "Gemcutter",
    "Hornblower", "Inkwell", "Jeweler", "Kettleblack", "Loomweaver",
    # Misc
    "Blackwood", "Coldharbour", "Duskwalker", "Emberglow", "Frostborn",
    "Goldleaf", "Highcrown", "Ironside", "Jadeheart", "Kindlewood",
]

# Hobbit-specific whimsical surnames (used in addition to shared surnames)
HOBBIT_SURNAMES = [
    "Baggins", "Bolger", "Brandybuck", "Burrows", "Chubb",
    "Diggle", "Fairbairn", "Gamgee", "Goodbody", "Greenhill",
    "Hayward", "Hornblower", "Longbottom", "Mugwort", "Noakes",
    "Puddifoot", "Rumble", "Sackville", "Thistlewool", "Whitfoot",
    "Appledore", "Boffin", "Brownlock", "Clayhanger", "Deepdelver",
    "Elfstone", "Foxburr", "Goold", "Heathertoes", "Ivybottom",
    "Kettlebottom", "Leafcutter", "Maggot", "Nutbrown", "Oldbuck",
    "Pimpernel", "Quillback", "Ropertwist", "Stumbletoe", "Twofoot",
]
