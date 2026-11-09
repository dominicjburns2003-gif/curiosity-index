"""
Curiosity Index - step 22b: drafted product pages for the broad universe.

A first draft, from general knowledge, of the best-known products of the new
S&P 500 and Nasdaq-100 companies, in the same format as the drafts for the
original 68 and the 44 added on 8 Nov 2026. It is only a draft: every row is
then checked automatically (src/check_universe.py: does the page exist, is it
a redirect, enough views, clicks to the company page, prices) and the flagged
rows are reviewed by hand. Companies with no product pages are still tracked
by their company page alone (see docs/broad_universe_plan.md).

Writes data/mapping/broad_draft.csv.
"""

from pathlib import Path

import pandas as pd

MAPPING_DIR = Path(__file__).resolve().parent.parent / "data" / "mapping"

PRODUCTS = {
    # Communication services
    "APP": ["AppLovin_MAX"], "T": ["AT&T_Mobility", "Cricket_Wireless", "DirecTV"],
    "CHTR": ["Spectrum_(brand)"], "ECHO": ["Dish_Network", "Boost_Mobile", "Sling_TV"],
    "FOXA": ["Fox_News", "Fox_Broadcasting_Company", "Tubi", "Fox_Sports_(United_States)"],
    "OMC": ["BBDO", "DDB_Worldwide", "TBWA_Worldwide"], "RDDT": ["Reddit"],
    "SKYD": ["Paramount+", "CBS", "MTV", "Nickelodeon", "Pluto_TV"],
    "TMUS": ["Metro_by_T-Mobile", "Mint_Mobile"], "TKO": ["Ultimate_Fighting_Championship", "WWE"],
    "VZ": ["Verizon_(wireless_service)", "Fios", "Visible_(wireless_service)"],
    # Consumer discretionary
    "ABNB": ["Airbnb"], "AZO": ["AutoZone"], "BBY": ["Geek_Squad"], "CVNA": ["Carvana"],
    "CMG": ["Chipotle_Mexican_Grill"], "DPZ": ["Domino's"], "DASH": ["Wolt", "Caviar_(company)"],
    "EBAY": ["StubHub"], "LVS": ["Marina_Bay_Sands", "The_Venetian_Macao"],
    "LOW": ["Kobalt_(tools)"], "LULU": ["Mirror_(company)"], "MGM": ["Bellagio_(resort)", "MGM_Grand_Las_Vegas",
                                                                     "BetMGM"],
    "RL": ["Polo_Ralph_Lauren"], "ROST": ["Ross_Dress_for_Less", "DD's_Discounts"],
    "TJX": ["TJ_Maxx", "Marshalls", "HomeGoods", "TK_Maxx"], "TSCO": ["Petsense"],
    "ULTA": ["Ulta_Beauty"], "WSM": ["Pottery_Barn", "West_Elm", "Williams_Sonoma"],
    "WYNN": ["Wynn_Las_Vegas", "Encore_Las_Vegas", "Encore_Boston_Harbor"], "MELI": ["Mercado_Pago"],
    "PDD": ["Temu"], "HD": ["Husky_(tools)", "Ryobi"],
    # Consumer staples
    "STZ": ["Corona_(beer)", "Modelo_Especial", "Pacifico_(beer)", "Robert_Mondavi_Winery"],
    "COST": ["Kirkland_Signature", "Costco_hot_dog"], "DG": ["Dollar_General"],
    "DLTR": ["Dollar_Tree", "Family_Dollar"], "KR": ["Ralphs", "Fred_Meyer", "Harris_Teeter", "King_Soopers"],
    "TGT": ["Target_Circle", "Up_&_Up"], "TSN": ["Jimmy_Dean", "Hillshire_Brands", "Ball_Park_Franks",
                                                  "Tyson_chicken_nuggets"],
    "CASY": ["Casey's"], "CCEP": ["Coca-Cola"], "VYLR": ["Pioneer_Hi-Bred"],
    # Energy
    "CVX": ["Texaco", "Chevron_with_Techron"], "XOM": ["Esso", "Mobil", "Mobil_1"],
    "MPC": ["ARCO", "Speedway_LLC"], "PSX": ["76_(gas_station)", "Conoco"], "VLO": ["Valero_(gas_station)"],
    # Financials
    "AFL": ["Aflac_Duck"], "ALL": ["Esurance", "Allstate_Mayhem"], "AXP": ["American_Express_Platinum_Card",
                                                                         "American_Express_Gold_Card"],
    "BRK-B": ["GEICO", "Dairy_Queen", "Duracell", "See's_Candies", "NetJets"],
    "BLK": ["IShares", "Aladdin_(BlackRock)"], "COF": ["Capital_One_Venture"],
    "SCHW": ["TD_Ameritrade", "Thinkorswim"], "COIN": ["Coinbase_Wallet", "Base_(blockchain)"],
    "JPM": ["Chase_Bank", "Chase_Sapphire"], "MA": ["Maestro_(debit_card)", "Cirrus_(interbank_network)"],
    "PGR": ["Flo_(Progressive)"], "HOOD": ["Robinhood_(app)"], "V": ["Visa_Electron", "Visa_Debit", "Plus_(interbank_network)"],
    "SYF": ["CareCredit"], "TRV": ["Travelers_umbrella"], "WFC": ["Wells_Fargo_Advisors"],
    "SPGI": ["S&P_500", "Dow_Jones_Industrial_Average"], "MSCI": ["MSCI_World", "MSCI_EAFE"],
    "NDAQ": ["Nasdaq-100", "Nasdaq_Composite"], "ICE": ["New_York_Stock_Exchange"],
    "CME": ["Chicago_Mercantile_Exchange", "E-mini"], "MCO": ["Moody's_Analytics"],
    
    # Health care
    "ALGN": ["Invisalign", "iTero"], "BSX": ["Watchman_(medical_device)"], "DXCM": ["Dexcom_G7"],
    "EW": ["Sapien_3"], "PODD": ["Omnipod"], "JNJ": ["Tylenol", "Listerine", "Band-Aid", "Stelara", "Darzalex"],
    "MDT": ["MiniMed", "Micra_(pacemaker)"], "MRNA": ["Moderna_COVID-19_vaccine", "MRNA-1283"],
    "RMD": ["AirSense"], "SYK": ["Mako_robot"], "UNH": ["Optum", "UnitedHealthcare"],
    "CVS": ["CVS_Pharmacy", "Aetna", "MinuteClinic"], "CI": ["Express_Scripts", "Evernorth"],
    "ELV": ["Anthem_Blue_Cross"], "HUM": ["Humana_Military"], "INCY": ["Ruxolitinib"],
    "VTRS": ["EpiPen", "Viagra"], "ZTS": ["Apoquel", "Simparica", "Revolution_(medication)"],
    "IDXX": ["SNAP_test"], "ILMN": ["Illumina_dye_sequencing"], "DHR": ["Beckman_Coulter", "Cepheid_(company)"],
    "TMO": ["Fisher_Scientific", "Applied_Biosystems", "Invitrogen"], "ALNY": ["Patisiran", "Vutrisiran"],
    "GEHC": ["Vscan"], "SOLV": ["Littmann_(stethoscope)"],
    # Industrials
    "MMM": ["Post-it_note", "Scotch_Tape", "Scotch-Brite", "N95_respirator", "Thinsulate"],
    "AXON": ["Taser", "Axon_Body"], "CAT": ["Caterpillar_D9", "Caterpillar_797", "Caterpillar_D11"],
    "CTAS": ["Cintas_uniforms"], "CPRT": ["Copart"], "DE": ["John_Deere_tractors", "John_Deere_4020"],
    "DAL": ["Delta_SkyMiles", "Delta_Connection"], "FDX": ["FedEx_Express", "FedEx_Ground", "FedEx_Office"],
    "GE": ["General_Electric_GE9X", "CFM_International_LEAP", "General_Electric_GE90"],
    "GEV": ["Haliade-X"], "GNRC": ["Generac_generator"], "HON": ["Honeywell_thermostat"],
    "HII": ["Newport_News_Shipbuilding", "Ingalls_Shipbuilding"], "LHX": ["AN/PRC-152", "L3Harris_EA-37B_Compass_Call"],
    "OTIS": ["Otis_Elevator_Company"], "PCAR": ["Kenworth", "Peterbilt", "DAF_Trucks"],
    "RTX": ["Pratt_&_Whitney", "Collins_Aerospace", "Raytheon", "FIM-92_Stinger", "MIM-104_Patriot"],
    "SNA": ["Snap-on_tools"], "LUV": ["Rapid_Rewards"], "SWK": ["DeWalt", "Craftsman_(tools)", "Black_&_Decker"],
    "TXT": ["Cessna", "Bell_Textron", "Beechcraft", "Cessna_Citation"], "TT": ["Trane", "Thermo_King"],
    "UBER": ["Uber_Eats"], "UAL": ["MileagePlus", "United_Express"], "UPS": ["UPS_Airlines", "The_UPS_Store"],
    "CARR": ["Carrier_air_conditioner", "Kidde"], "LII": ["Lennox_furnace"],
    "MAS": ["Behr_Process_Corporation", "Delta_Faucet_Company"], "WAB": ["Evolution_Series"],
    "WM": ["Waste_Management_Phoenix_Open"], "RKLB": ["Rocket_Lab_Electron", "Rocket_Lab_Neutron"],
    "SPCX": ["Falcon_9", "SpaceX_Starship", "Starlink", "SpaceX_Dragon_2", "Falcon_Heavy"],
    "TRI": ["Reuters", "Westlaw"], "ROL": ["Orkin"],
    "ADP": ["ADP_National_Employment_Report"],
    "HONA": ["Honeywell_HTF7000"],
    # Information technology
    "AVGO": ["VMware", "Broadcom_Tomahawk"], "CRWD": ["CrowdStrike_Falcon", "2024_CrowdStrike-related_IT_outages"],
    "DELL": ["Alienware", "Dell_XPS", "Dell_Inspiron", "Dell_Latitude", "PowerEdge"],
    "FTNT": ["FortiGate"], "GEN": ["Norton_AntiVirus", "Avast_Antivirus", "LifeLock", "CCleaner"],
    "GDDY": ["GoDaddy"], "HPE": ["Aruba_Networks", "Frontier_(supercomputer)", "El_Capitan_(supercomputer)"],
    "HPQ": ["HP_Spectre", "HP_Pavilion", "HP_LaserJet", "HP_Envy", "HP_Omen"],
    "IBM": ["IBM_Watson", "IBM_Z", "Red_Hat", "Red_Hat_Enterprise_Linux", "IBM_Quantum_System_One"],
    "MSI": ["Motorola_Solutions_APX"], "MU": ["Crucial_Technology"], "PLTR": ["Palantir_Gotham", "Palantir_Foundry"],
    "PANW": ["Prisma_Cloud"], "SNDK": ["SanDisk_Extreme", "SD_card"], "STX": ["Seagate_Barracuda"],
    "NOW": ["ServiceNow"], "SMCI": ["Supermicro"], "TXN": ["TI-84_Plus_series", "TI-83_series", "TI-Nspire_series"],
    "WDC": ["WD_Black"], "ASML": ["Extreme_ultraviolet_lithography"], "ARM": ["ARM_Cortex-A", "ARM_architecture_family"],
    "SHOP": ["Shop_Pay"], "TRMB": ["SketchUp"], "GLW": ["Gorilla_Glass", "Pyrex",
                                                                                 "CorningWare"],
    "ACN": ["Accenture_Song"], "ANET": ["Arista_EOS"], "AMAT": ["Applied_Materials"], "TWLO": ["SendGrid"],
    "VRSN": [".com"], "ZBRA": ["Zebra_printers"], "OKTA": ["Auth0"], "CDNS": ["Cadence_Allegro"],
    "SNPS": ["Synopsys_Design_Compiler"], "PTC": ["Creo_(software)", "Onshape"], "WDAY": ["Workday,_Inc."],
    "DDOG": ["Datadog"], "CRWV": ["CoreWeave"],
    # Materials
    "AVY": ["Avery_Dennison_labels"], "BALL": ["Ball_jar"], "DOW": ["Styrofoam", "Saran_(plastic)"],
    "DD": ["Kevlar", "Tyvek", "Nomex", "Corian"], "SHW": ["Dutch_Boy_Paints", "Valspar", "Krylon"],
    "PPG": ["Glidden", "Olympic_paint"], "IFF": ["International_Flavors_&_Fragrances"], "ECL": ["Nalco_Water"],
    "IP": ["Hammermill_paper"], "NEM": ["Boddington_Gold_Mine"], "FCX": ["Grasberg_mine"],
    # Real estate
    "SPG": ["King_of_Prussia_(mall)", "Woodbury_Common_Premium_Outlets", "The_Forum_Shops_at_Caesars"],
    "HST": ["Hotel_del_Coronado"],
    "PSA": ["Public_Storage"], "EXR": ["Extra_Space_Storage"], "IRM": ["Iron_Mountain_(company)"],
    "EQIX": ["Equinix"],
    # Utilities
    "CEG": ["Calvert_Cliffs_Nuclear_Power_Plant"], "NEE": ["Florida_Power_&_Light"],
    "DUK": ["Duke_Energy_Florida"], "SO": ["Vogtle_Electric_Generating_Plant", "Georgia_Power"],
    "ED": ["Con_Edison_steam_system"], "VST": ["Comanche_Peak_Nuclear_Power_Plant"],
    "AES": ["AES_Andes"], "EXC": ["Commonwealth_Edison", "PECO_Energy_Company"],
}


def main() -> None:
    companies = pd.read_csv(MAPPING_DIR / "broad_companies.csv")
    rows = []
    for c in companies.itertuples():
        for product in PRODUCTS.get(c.ticker, []):
            rows.append({"ticker": c.ticker, "company": c.company, "sector": c.sector,
                         "company_article": c.company_article, "product_article": product})
    draft = pd.DataFrame(rows)
    draft = draft[draft["product_article"] != draft["company_article"]]  # the company page itself is not a product
    draft.to_csv(MAPPING_DIR / "broad_draft.csv", index=False)
    unknown = set(PRODUCTS) - set(companies["ticker"])
    print(f"{len(draft)} product rows for {draft['ticker'].nunique()} of {len(companies)} new companies"
          + (f"; tickers not in the list: {sorted(unknown)}" if unknown else ""))


if __name__ == "__main__":
    main()
