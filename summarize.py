from redis import Redis
import ujson


client = Redis('downloader')

keys = client.keys('listing:*')

"""
P337A: M Sports package
P7MPA: Sports package
S1CAA: Selection of COP relevant vehicles
S205A: Automatic transmission
S223A: Electronic Damper Control (EDC)
S229A: Dynamic Drive
S248A: Steering wheel heater
S255A: Sports leather steering wheel
S258A: Tire with run-flat functionality
S2NDA: BMW LA wheel, M Double Spoke 351
S2NNA: BMW alloy wheel, M double spoke 172
S2TBA: Sport automatic transmission
S2VAA: Chassis & suspens. setup"Adaptive Drive"
S2VBA: Tyre pressure control (TPC)
S2VHA: Integral active steering
S2WCA: BMW LM Rad W-Speiche 332
S300A: Emergency spare wheel
S316A: automatic trunk lid mechanism
S319A: Integrated universal remote control
S322A: Comfort access
S323A: Soft-Close-Automatic doors
S339A: Shadow-Line
S3AGA: Reversing camera
S403A: Glass roof, electrical
S415A: Sun-blind, rear
S416A: Roller sun vizor, rear lateral
S423A: Floor mats, velours
S428A: Warning triangle and first aid kit
S430A: Interior/outside mirror with auto dip
S431A: Interior mirror with automatic-dip
S441A: Smoker package
S453A: Climatised fornt seats
S455A: Active seat for driver and passenger
S456A: Comfort seat with memory
S464A: Ski bag
S465A: Through-loading system
S488A: Lumbar support, driver and passenger
S494A: Seat heating driver/passenger
S496A: Seat heating, rear
S4B5A: Fine wood ash grain, high-gloss
S4B9A: Interieurleisten Alu Feinschliff
S4BYA: Real Bamboo wood-grain trim, anthracite
S4CEA: Fine woodgrain vers., Fineline anthrac.
S4MRA: Interior strips, aluminum hexagon
S4NBA: Autom. climate control with 4-zone ctrl
S502A: Headlight cleaning system
S508A: Park Distance Control (PDC)
S522A: Xenon Light
S524A: Adaptive Headlights
S575A: Supplementary 12V sockets
S5ACA: High-beam assistant
S5ADA: Lane departure warning
S5AGA: Lane-change warning
S5DLA: Surround View
S5DPA: Park Assistent
S609A: Navigation system Professional
S610A: Head-up display
S615A: Expanded BMW Online Information
S620A: Voice control
S639A: Preparation f mobile phone cpl. USA/CDN
S655A: Satellite tuner
S677A: HiFi System Professional DSP
S693A: Preparation BMW satellite radio
S694A: Provisions for BMW 6 CD changer
S697A: Area-Code 1 for DVD
S6AAA: BMW TeleServices
S6ABA: Control for Teleservices
S6FGA: Rear-compartment entertainment
S6FLA: USB/Audio interface
S6NFA: Music interface for Smartphone
S6NRA: Apps
S6UHA: Traffic Information
S6VAA: CIC-Zusteuerung
S6VCA: Control for Combox
S6WAA: Instrument cluster, expanded equipment
S704A: M Sports suspension
S710A: M leather steering wheel
S715A: M Aerodynamics package
S760A: High gloss shadow line
S775A: Headlining anthracite
S818A: Battery master switch
S840A: High speed synchronisation
S880A: On-board vehicle literature English
S8S4A: Decoding variable light distribution
S8SCA: Telematics access request,country-spec.
S8SPA: Control unit COP
S902A: Special inspection press vehicles
S925A: Transport protection package
S9AAA: Outer skin protection
"""

required_options = {
    'S322A',    # Comfort access
    'S456A',    # comfort seat
    'P337A',    # M Sports package
    'S2VAA',    # adaptive drive, counteracts body roll
    'S229A',    # dynamic drive, aka Dynamic Handling Package
}

scored_options = {
    'S610A',    # heads up display
}

rejected_options = {
    'S2VHA',    # integral active steering
}

options = {}
scores = []
for key in keys:
    info = ujson.loads(client.get(key))

    for key in info['options']:
        if key not in options:
            options[key] = info['options'][key]

    transmission = None
    for vehicle_info in info['vehicle']:
        key, value = vehicle_info
        if key == 'Getriebe':
            transmission = value

    if transmission != 'manuell':
        continue

    mileage = info['mileage']
    if not isinstance(mileage, int):
        mileage = int(mileage.replace(',', ''))
    if mileage > 75000:
        continue

    is_match = True
    for key in required_options:
        if key not in info['options']:
            is_match = False
            break
    if not is_match:
        continue

    for key in rejected_options:
        if key in info['options']:
            is_match = False
    if not is_match:
        continue

    score = 0
    for key, value in info['options'].items():
        if key not in options:
            options[key] = value
        if key in required_options:
            score += 1

    scores.append((score, info))

# for key, value in sorted(options.items()):
#     print "%s: %s" % (key, value)

for score, item in reversed(sorted(scores, key=lambda x: x[0])):
    print "${price}\t{mileage}\t{url}".format(
        price=item['price'],
        mileage=item['mileage'],
        url=item['url'],
    )
    for key in required_options.union(scored_options):
        if key in item['options']:
            print "\t%s" % item['options'][key]