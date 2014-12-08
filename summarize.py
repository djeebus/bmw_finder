import itertools
import ujson

from collections import defaultdict
from redis import Redis
from urlparse import urlparse

from bmw_finder.spiders import MAX_MILES, MAX_PRICE


"""
550i options:

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

"""
M3 options

P337A: M Sports package
S1CAA: Selection of COP relevant vehicles
S1CCA: Auto start/stop function
S223A: Electronic Damper Control (EDC)
S229A: Dynamic Drive
S248A: Steering wheel heater
S258A: Tire with run-flat functionality
S2MDA: M Drive
S2NDA: BMW LA wheel, M Double Spoke 351
S2VAA: Chassis & suspens. setup"Adaptive Drive"
S2VBA: Tyre pressure control (TPC)
S302A: Alarm system
S313A: Fold-in outside mirror
S316A: automatic trunk lid mechanism
S319A: Integrated universal remote control
S322A: Comfort access
S323A: Soft-Close-Automatic doors
S3AGA: Reversing camera
S403A: Glass roof, electrical
S415A: Sun-blind, rear
S416A: Roller sun vizor, rear lateral
S423A: Floor mats, velours
S430A: Interior/outside mirror with auto dip
S431A: Interior mirror with automatic-dip
S441A: Smoker package
S453A: Climatised fornt seats
S455A: Active seat for driver and passenger
S456A: Comfort seat with memory
S459A: Seat adjuster, electric, with memory
S465A: Through-loading system
S488A: Lumbar support, driver and passenger
S490A: Adjuster, backrest width
S494A: Seat heating driver/passenger
S496A: Seat heating, rear
S497A: Centre armrest, rear
S4AEA: Armrest front, retractable
S4CEA: Fine woodgrain vers., Fineline anthrac.
S4MRA: Interior strips, aluminum hexagon
S4MYA: Int.trim,leather,carbon struct.,black
S4MZA: Edelholz Platane Spiegelmaser anthrazit
S4NAA: Interior mirror with digital compass
S4NBA: Autom. climate control with 4-zone ctrl
S502A: Headlight cleaning system
S507A: Park Distance Control (PDC), rear
S508A: Park Distance Control (PDC)
S521A: Rain sensor
S522A: Xenon Light
S524A: Adaptive Headlights
S563A: Light package
S575A: Supplementary 12V sockets
S5DCA: Rear-seat headrests, folding
S609A: Navigation system Professional
S615A: Expanded BMW Online Information
S616A: BMW Online
S620A: Voice control
S639A: Preparation f mobile phone cpl. USA/CDN
S655A: Satellite tuner
S676A: HiFi speaker system
S677A: HiFi System Professional DSP
S693A: Preparation BMW satellite radio
S697A: Area-Code 1 for DVD
S6AAA: BMW TeleServices
S6ABA: Control for Teleservices
S6FLA: USB/Audio interface
S6NFA: Music interface for Smartphone
S6NRA: Apps
S6UHA: Traffic Information
S6VCA: Control for Combox
S710A: M leather steering wheel
S715A: M Aerodynamics package
S752A: Individual audio system
S760A: High gloss shadow line
S775A: Headlining anthracite
S7MAA: Competition Paket
S840A: High speed synchronisation
S8S4A: Decoding variable light distribution
S8SCA: Telematics access request,country-spec.
S8SPA: Control unit COP
S8TLA: Tagfahrlicht Front und Hech aktiv
S925A: Transport protection package
"""

my_options_config = {
    'BMW M3': {
        'interesting': {
            'P337A',    #: M Sports package
            'S2VAA',    #: Chassis & suspens. setup"Adaptive Drive"
            'S2MDA',    #: M Drive
            'S322A',    #: Comfort access
            'S323A',    #: Soft-Close-Automatic doors
            'S403A',    #: Glass roof, electrical
            'S453A',    #: Climatised fornt seats
            'S456A',    #: Comfort seat with memory
            'S459A',    #: Seat adjuster, electric, with memory
            'S488A',    #: Lumbar support, driver and passenger
            'S494A',    #: Seat heating driver/passenger
            'S496A',    #: Seat heating, rear
            'S4NBA',    #: Autom. climate control with 4-zone ctrl
            'S507A',    #: Park Distance Control (PDC), rear
            'S508A',    #: Park Distance Control (PDC)
            'S524A',    #: Adaptive Headlights
            'S609A',    #: Navigation system Professional
            'S620A',    #: Voice control
            'S676A',    #: HiFi speaker system
            'S677A',    #: HiFi System Professional DSP
            'S6FLA',    #: USB/Audio interface
            'S6NFA',    #: Music interface for Smartphone
            'S6NRA',    #: Apps
            'S710A',    #: M leather steering wheel
            'S715A',    #: M Aerodynamics package
            'S752A',    #: Individual audio system
            'S7MAA',    #: Competition Paket
        },
        'required': set(),
        'scored': set(),
        'rejected': set(),
    },
    'BMW 550I': {
        'interesting': {
            'P337A',    # M Sports package
            'P7MPA',    # Sports package

            'S248A',    # Steering wheel heater
            'S255A',    # Sports leather steering wheel
            'S229A',    # dynamic drive, aka Dynamic Handling Package, dynamic damper control
            'S2NDA'     #: BMW LA wheel, M Double Spoke 351
            'S2NNA',    #: BMW alloy wheel, M double spoke 172

            'S2VAA',    # adaptive drive, anti roll stabilization bars, counteracts body roll
            'S2WCA',    #: BMW LM Rad W-Speiche 332
            'S322A',    # Comfort access
            'S323A',    #: Soft-Close-Automatic doors
            'S339A',    #: Shadow-Line
            'S3AGA',    #: Reversing camera
            'S403A',    #: Glass roof, electrical
            'S415A',    #: Sun-blind, rear
            'S416A',    #: Roller sun vizor, rear lateral
            'S453A',    #: Climatised fornt seats
            'S455A',    #: Active seat for driver and passenger
            'S456A',    #: Comfort seat with memory
            'S488A',    #: Lumbar support, driver and passenger
            'S494A',    #: Seat heating driver/passenger
            'S496A',    #: Seat heating, rear
            'S4NBA',    #: Autom. climate control with 4-zone ctrl

            'S508A',    #: Park Distance Control (PDC)
            'S522A',    #: Xenon Light
            'S524A',    #: Adaptive Headlights

            'S5DLA',    #: Surround View
            'S5DPA',    #: Park Assistent

            'S609A',    #: Navigation system Professional
            'S610A',    # heads up display
            'S677A',    #: HiFi System Professional DSP
            'S6FGA',    #: Rear-compartment entertainment
            'S6FLA',    #: USB/Audio interface
            'S6NFA',    #: Music interface for Smartphone
            'S6NRA',    #: Apps

            'S6WAA',    #: Instrument cluster, expanded equipment
            'S704A',    #: M Sports suspension
            'S710A',    #: M leather steering wheel
            'S715A',    #: M Aerodynamics package
            'S760A',    #: High gloss shadow line
        },
        'required': {
            'S322A',    # Comfort access
            #'S456A',    # comfort seat
            'P337A',    # M Sports package
            #'S704A',    # m sports suspension
        },
        'scored': {
            'S610A',    # heads up display
            'S229A',    # dynamic drive, aka Dynamic Handling Package, dynamic damper control
            'S2VAA',    # adaptive drive, anti roll stabilization bars, counteracts body roll
            'P337A',    # M Sports package
            'S322A',    # Comfort access
        },
        'rejected': {
            'S2VHA',    # integral active steering
        }
    },

}

def get_options_config(info):
    key = '{make} {model}'.format(
        make=info['make'],
        model=info['model'].split()[0].upper(),
    )
    return my_options_config[key]


all_options = {}
scores = []

client = Redis('downloader')
keys = client.keys('listing:*')
total_keys = len(keys)
keys = sorted(keys)

infos = map(lambda key: ujson.loads(client.get(key)), keys)
get_vin = lambda info: info['vin']
sorted_infos = sorted(infos, key=get_vin)
infos_by_vin = itertools.groupby(sorted_infos, key=get_vin)


def clean_number(number):
    if isinstance(number, int):
        return number

    return int(number.replace(',', '').replace('$', ''))


total_cars = 0
cars_by_domain = defaultdict(lambda: 0)
for vin, vin_infos in infos_by_vin:
    vin_infos = list(vin_infos)

    total_cars += 1
    for vin_info in vin_infos:
        domain = urlparse(vin_info['url']).hostname
        cars_by_domain[domain] += 1

    if not vin:
        print "No vin number!!"
        continue

    info = vin_infos[0]

    this_options_config = get_options_config(info)

    # if info['model'].upper() == 'M3':
    #     for key in info['options']:
    #         if key not in all_options:
    #             all_options[key] = info['options'][key]

    # ensure car is a manual
    transmission = None
    for vehicle_info in info['vehicle']:
        key, value = vehicle_info
        if key == 'Getriebe':
            transmission = value
    if transmission != 'manuell':
        continue

    mileage = info['mileage'] = clean_number(info['mileage'])
    if mileage > MAX_MILES:
        continue

    price = info['price'] = clean_number(info['price'])
    if price > MAX_PRICE:
        continue

    is_match = True
    for key in this_options_config['required']:
        if key not in info['options']:
            is_match = False
            break
    if not is_match:
        continue

    for key in this_options_config['rejected']:
        if key in info['options']:
            is_match = False
    if not is_match:
        continue

    score = 0
    for key, value in info['options'].items():
        if key not in all_options:
            all_options[key] = value
        if key in this_options_config['scored']:
            score += 1

    scores.append((score, info, map(lambda i: i['url'], vin_infos)))

# for key, value in sorted(all_options.items()):
#     print "%s: %s" % (key, value)


matched_cars = 0
for score, item, urls in reversed(sorted(scores, key=lambda x: x[0])):
    this_options_config = get_options_config(item)
    printable_options_codes = list(this_options_config['required']) + \
                              list(this_options_config['interesting']) + \
                              list(this_options_config['scored'])
    printable_options_codes = set(printable_options_codes)

    matched_cars += 1
    print "{year} {make} {model}\t${price:,}\t\t{mileage:,} miles\t{score} points".format(
        year=item['year'],
        make=item['make'],
        model=item['model'],
        price=item['price'],
        mileage=item['mileage'],
        score=score,
    )
    for url in sorted(urls):
        print "%s" % url

    printable_options = [item['options'][key] for key in printable_options_codes if key in item['options']]
    for option in sorted(printable_options):
        print "\t%s" % option

    print


print """total matches: {results} [{domains}]
total cars: {cars}
matched cars: {matches}

""".format(
    domains=' '.join('%s:%s' % (domain, count) for domain, count in cars_by_domain.items()),
    results=total_keys,
    cars=total_cars,
    matches=matched_cars,
)