"""Clean the DATAtourisme POI file for the school-trip agent.

Usage: python clean_pois.py
Input:  data/datatourisme-reg-occ.csv
        data/descriptions_redigees.json  (optional: {URI: description} written by hand / after web research)
Output: data/datatourisme-reg-occ-clean.csv, same columns plus:
        - Categories_de_POI: French labels extracted from the ontology URLs ("Château ; Site culturel")
        - Description: original, hand-written, or generated from the POI data when missing
        - Source_description: originale | redigee | generee
        - Mots_cles: themes useful to find the place from a school-trip topic
"""
import json
import os
import re
import unicodedata

import pandas as pd

SRC = "data/datatourisme-reg-occ.csv"
HAND = "data/descriptions_redigees.json"
OUT = "data/datatourisme-reg-occ-clean.csv"

# Generic ontology classes that carry no information.
SKIP = {"PointOfInterest", "PlaceOfInterest", "Product", "Practice", "OrderedList"}

CAT_FR = {
    "Accommodation": "Hébergement", "RentalAccommodation": "Hébergement locatif",
    "SelfCateringAccommodation": "Meublé / gîte", "EntertainmentAndEvent": "Fête et manifestation",
    "FoodEstablishment": "Restauration", "CulturalSite": "Site culturel",
    "SportsAndLeisurePlace": "Lieu de sport et loisirs", "Store": "Commerce", "Tour": "Itinéraire touristique",
    "Restaurant": "Restaurant", "TastingProvider": "Lieu de dégustation", "AccommodationProduct": "Offre d'hébergement",
    "ActivityProvider": "Prestataire d'activités", "Guesthouse": "Chambre d'hôtes",
    "CampingAndCaravanning": "Hôtellerie de plein air", "Apartment": "Appartement",
    "ConvenientService": "Service pratique", "LeisureSportActivityProvider": "Prestataire d'activités sportives et de loisirs",
    "WalkingTour": "Itinéraire pédestre", "HotelTrade": "Hôtellerie", "Hotel": "Hôtel", "House": "Maison",
    "SportsEvent": "Événement sportif", "SocialEvent": "Événement social", "ReligiousSite": "Édifice religieux",
    "ShowEvent": "Spectacle", "Camping": "Camping", "TechnicalHeritage": "Patrimoine technique",
    "NaturalHeritage": "Patrimoine naturel", "CollectiveAccommodation": "Hébergement collectif",
    "CraftsmanShop": "Artisan", "SaleEvent": "Vente / braderie", "Concert": "Concert", "Producer": "Producteur",
    "HotelRestaurant": "Hôtel-restaurant", "RemarkableBuilding": "Bâtiment remarquable",
    "CityHeritage": "Patrimoine urbain", "CyclingTour": "Itinéraire cyclable", "TheaterEvent": "Théâtre (événement)",
    "Church": "Église", "Market": "Marché", "Tasting": "Dégustation", "Visit": "Visite",
    "TouristInformationCenter": "Point d'information touristique", "CamperVanArea": "Aire de camping-cars",
    "Museum": "Musée", "LocalAnimation": "Animation locale", "Exhibition": "Exposition",
    "ChildrensEvent": "Événement jeune public", "BarOrPub": "Bar / pub", "ServiceProvider": "Prestataire de services",
    "StopOverOrGroupLodge": "Gîte d'étape / de groupe", "FreePractice": "Pratique libre",
    "FastFoodRestaurant": "Restauration rapide", "Traineeship": "Stage", "Festival": "Festival",
    "LocalTouristOffice": "Office de tourisme", "BoutiqueOrLocalShop": "Boutique", "Cinema": "Cinéma",
    "PublicLavatories": "Toilettes publiques", "Castle": "Château", "Library": "Bibliothèque / médiathèque",
    "Transport": "Transport", "PicnicArea": "Aire de pique-nique", "Rental": "Location", "Rambling": "Randonnée",
    "BrasserieOrTavern": "Brasserie / taverne", "Cellar": "Cave", "AccompaniedPractice": "Pratique encadrée",
    "Conference": "Conférence", "Beach": "Plage", "SportsCompetition": "Compétition sportive",
    "GroupLodging": "Hébergement de groupe", "DefenceSite": "Site défensif",
    "CulturalActivityProvider": "Prestataire d'activités culturelles", "Course": "Cours / atelier",
    "ScreeningEvent": "Projection", "Theater": "Théâtre", "SwimmingPool": "Piscine", "GourmetRestaurant": "Restaurant gastronomique",
    "WaterSource": "Point d'eau", "HolidayResort": "Résidence de tourisme", "ParkAndGarden": "Parc et jardin",
    "EquipmentRental": "Location de matériel", "Chapel": "Chapelle", "Farmer": "Agriculteur",
    "ClubOrHolidayVillage": "Village vacances", "TraditionalCelebration": "Fête traditionnelle", "PlayArea": "Aire de jeux",
    "Farm": "Ferme", "ArcheologicalSite": "Site archéologique", "BistroOrWineBar": "Bistrot / bar à vin",
    "EducationalTrail": "Sentier pédagogique", "EquestrianCenter": "Centre équestre",
    "ElectricVehicleChargingPoint": "Borne de recharge électrique", "PointOfView": "Point de vue", "Room": "Salle",
    "ArtGalleryOrExhibitionGallery": "Galerie d'art", "LeisureComplex": "Complexe de loisirs", "ServiceArea": "Aire de services",
    "SelfServiceCafeteria": "Cafétéria", "ThemePark": "Parc à thème", "BusinessEvent": "Événement professionnel",
    "RoadTour": "Itinéraire routier", "BusinessPlace": "Lieu d'affaires", "Game": "Jeu", "NonHousingRealEstateRental": "Location de salle",
    "CafeOrTeahouse": "Café / salon de thé", "Lake": "Lac", "Tower": "Tour", "ViaFerrata": "Via ferrata", "Parking": "Parking",
    "FairOrShow": "Foire / salon", "OpenDay": "Portes ouvertes", "IceCreamShop": "Glacier", "SightseeingBoat": "Bateau promenade",
    "TaxiCompany": "Taxi", "Reading": "Lecture", "Bridge": "Pont", "Stadium": "Stade", "GarageSale": "Vide-grenier",
    "ClimbingWall": "Mur d'escalade", "FortifiedSet": "Ensemble fortifié", "Ruins": "Ruines", "InterpretationCentre": "Centre d'interprétation",
    "RemarkableHouse": "Maison remarquable", "Mill": "Moulin", "CastleAndPrestigeMansion": "Château et demeure de prestige",
    "BoulesPitch": "Boulodrome", "IndustrialSite": "Site industriel", "FitnessCenter": "Salle de sport",
    "EquipmentRentalShop": "Magasin de location", "Marina": "Port de plaisance", "Temple": "Temple",
    "RemembranceSite": "Lieu de mémoire", "MedicalPlace": "Lieu médical", "BricABrac": "Brocante",
    "ZooAnimalPark": "Zoo / parc animalier", "TennisComplex": "Tennis", "Mountain": "Montagne", "RacingCircuit": "Circuit",
    "TrackRollerOrSkateBoard": "Skatepark", "TableHoteGuesthouse": "Table d'hôtes", "TeachingFarm": "Ferme pédagogique",
    "Orchard": "Verger", "Col": "Col", "FarmhouseInn": "Ferme-auberge", "HolidayCentre": "Centre de vacances", "Cirque": "Cirque naturel",
    "AntiqueAndSecondhandGoodDealer": "Antiquaire / brocanteur", "ConventionCentre": "Centre de congrès", "HorseTour": "Itinéraire équestre",
    "VisualArtsEvent": "Arts visuels", "Harvest": "Récolte / vendanges", "FortifiedCastle": "Château fort", "Cloister": "Cloître",
    "Abbey": "Abbaye", "TouristTrain": "Train touristique", "Bastide": "Bastide", "AdventurePark": "Parc aventure / accrobranche",
    "MiniGolf": "Minigolf", "GolfCourse": "Golf", "Gymnasium": "Gymnase", "Hammam": "Hammam", "Transporter": "Transporteur",
    "River": "Rivière", "Chalet": "Chalet", "Spa": "Spa", "Dungeon": "Donjon", "FitnessPath": "Parcours de santé",
    "CircusPlace": "Cirque (spectacle)", "CaveSinkholeOrAven": "Grotte / gouffre / aven", "BalneotherapyCentre": "Balnéothérapie",
    "Fountain": "Fontaine", "MultiActivity": "Multi-activités", "GarageOrAirPump": "Garage", "BikeStationOrDepot": "Station vélo",
    "RestStop": "Aire de repos", "ResidentialLeisurePark": "Parc résidentiel de loisirs", "FirstPractice": "Initiation",
    "Monastery": "Monastère", "Gorge": "Gorges", "Casino": "Casino", "Forest": "Forêt", "Opera": "Opéra", "Competition": "Compétition",
    "Collegiate": "Collégiale", "IncomingTravelAgency": "Agence réceptive", "CarpoolArea": "Aire de covoiturage", "KidsClub": "Club enfants",
    "Pond": "Étang", "Cathedral": "Cathédrale", "TrainStation": "Gare", "FarmCamping": "Camping à la ferme", "BowlingAlley": "Bowling",
    "MultiPurposeRoomOrCommunityRoom": "Salle polyvalente", "NightClub": "Discothèque", "Hut": "Cabane", "TreeHouse": "Cabane dans les arbres",
    "Auditorium": "Auditorium", "StreetFood": "Cuisine de rue", "MegalithDolmenMenhir": "Mégalithe / dolmen / menhir", "Stone": "Pierre remarquable",
    "EquipmentRepairShop": "Réparation de matériel", "FluvialTour": "Itinéraire fluvial",
    "YouthHostelAndInternationalCenter": "Auberge de jeunesse", "LocalProductsShop": "Produits locaux", "Bakery": "Boulangerie",
    "NaturalCuriosity": "Curiosité naturelle", "Valley": "Vallée", "Causse": "Causse", "RiverPort": "Port fluvial",
    "DevelopmentCourse": "Perfectionnement", "Fort": "Fort", "Cooperative": "Coopérative", "Parade": "Défilé", "WashHouse": "Lavoir",
    "Source": "Source", "Commanderie": "Commanderie", "ATM": "Distributeur de billets", "MilitaryCemetery": "Cimetière militaire",
    "Chartreuse": "Chartreuse", "ArtistSigning": "Dédicace", "District": "Quartier", "Airfield": "Aérodrome", "Trampoline": "Trampoline",
    "Recital": "Récital", "Waterfall": "Cascade", "Stream": "Ruisseau", "Carnival": "Carnaval", "NaturalCampingArea": "Aire naturelle de camping",
    "DownhillSkiRun": "Piste de ski alpin", "CollectiveHostel": "Gîte collectif", "NauticalCentre": "Base nautique",
    "ReligiousEvent": "Événement religieux", "CoveredMarket": "Halle / marché couvert", "Aqueduct": "Aqueduc", "Tipi": "Tipi",
    "CrossCountrySkiTrail": "Piste de ski de fond", "LaunchingRamp": "Rampe de mise à l'eau", "TrainingWorkshop": "Atelier de formation",
    "Arena": "Arènes", "RomanPath": "Voie romaine", "Mine": "Mine", "HealthcareProfessional": "Professionnel de santé",
    "BilliardRoom": "Billard", "ChildrensGite": "Gîte d'enfants", "TobogganBobsleigh": "Luge / bobsleigh", "Commemoration": "Commémoration",
    "Canal": "Canal", "TouristBus": "Bus touristique", "Palace": "Palais", "IntroductionCourse": "Cours d'initiation", "Yurt": "Yourte",
    "HealthcarePlace": "Établissement de santé", "BeachClub": "Club de plage", "RailBike": "Vélorail", "Bog": "Tourbière",
    "VivariumAquarium": "Aquarium / vivarium", "Convent": "Couvent", "Calvary": "Calvaire", "BusStop": "Arrêt de bus",
    "ThalassotherapyCentre": "Thalassothérapie", "SquashCourt": "Squash", "Swamp": "Marais", "TourismCableCar": "Téléphérique touristique",
    "Cinematheque": "Cinémathèque", "HouseBoat": "Péniche / bateau-logement", "IceSkatingRink": "Patinoire",
    "TourOperatorOrTravelAgency": "Agence de voyages", "CarOrBikeWash": "Station de lavage", "Tent": "Tente", "PigeonLoft": "Pigeonnier",
    "YachtClub": "Club nautique", "Brewery": "Brasserie artisanale", "RVServiceArea": "Aire de services camping-cars",
    "Cabaret": "Cabaret", "SportsDemonstration": "Démonstration sportive", "Velodrome": "Vélodrome", "Racetrack": "Hippodrome",
    "ShoppingCentreAndGallery": "Centre commercial", "SummerToboggan": "Luge d'été", "MountainRestaurant": "Restaurant d'altitude",
    "ElectricBycicleChargingPoint": "Borne de recharge vélo", "WifiHotSpot": "Point wifi", "Plain": "Plaine", "Synagogue": "Synagogue",
    "UnderwaterRoute": "Sentier sous-marin", "AlpinePasture": "Estive", "DepartementTourismCommittee": "Comité départemental du tourisme",
    "CableCarStation": "Station de téléphérique", "Plateau": "Plateau", "Peak": "Sommet", "CivilCemetery": "Cimetière",
    "Canyon": "Canyon", "CulturalEvent": "Événement culturel",
}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s).lower())
    return "".join(c for c in s if not unicodedata.combining(c))


# Themes: (keyword, categories that imply it, regex on normalized text).
# Regexes are deliberately strict (word boundaries) to avoid false positives.
THEMES = [
    ("préhistoire", {"MegalithDolmenMenhir"}, r"prehistor|neolith|paleolith|dolmens?\b|menhirs?\b|megalith|cro-magnon|neandert|peintures? (rupestres?|parietales?)|art parietal|tautavel|\bsilex"),
    ("archéologie", {"ArcheologicalSite"}, r"archeolog|fouilles|oppidum|site antique"),
    ("antiquité romaine", {"Aqueduct", "RomanPath"}, r"\bromaine?s?\b|gallo-romain|antiquite|aqueduc|amphitheatre|via domitia|pont du gard"),
    ("moyen âge", {"FortifiedCastle", "Dungeon", "Bastide", "Commanderie", "FortifiedSet"}, r"moyen[- ]age|medieva|feodal|chevaliers?\b|templiers?\b|donjon|remparts|bastide|chateau fort|cite de carcassonne"),
    ("catharisme", set(), r"cathare|albigeois|montsegur|peyrepertuse|queribus"),
    ("château", {"Castle", "FortifiedCastle", "CastleAndPrestigeMansion", "Palace"}, r"^chateau|\bchateau (de|du|des)\b|forteresse|citadelle"),
    ("patrimoine religieux", {"ReligiousSite", "Church", "Chapel", "Abbey", "Cathedral", "Cloister", "Monastery", "Convent", "Collegiate", "Chartreuse", "Temple", "Synagogue", "Calvary"}, r"\beglise|abbaye|cathedrale|chapelle|cloitre|monastere|basilique|prieure|couvent|collegiale|compostelle"),
    ("architecture", {"RemarkableBuilding", "RemarkableHouse", "Bridge", "Tower"}, r"architectur|monument historique|hotel particulier|patrimoine bati"),
    ("histoire moderne", set(), r"renaissance|xviie|xviiie|louis xiv|revolution francaise|camisard"),
    ("guerres mondiales et mémoire", {"RemembranceSite", "MilitaryCemetery", "Commemoration"}, r"guerre mondiale|grande guerre|resistance|deportation|memorial|monument aux morts|maquis|shoah|rivesaltes|retirada|harkis"),
    ("patrimoine industriel et techniques", {"TechnicalHeritage", "IndustrialSite", "Mill", "Mine", "WashHouse"}, r"industriel|usine|manufacture|moulins?\b|\bmines?\b|\bforges?\b|filature|tannerie|verrerie|canal du midi|ecluse"),
    ("sciences et techniques", set(), r"scientifique|\bsciences?\b|astronom|planetarium|aeronaut|aviation|airbus|cite de l'espace|robot|laboratoire"),
    ("géologie", {"CaveSinkholeOrAven", "Gorge", "Cirque", "Canyon", "NaturalCuriosity", "Causse"}, r"geolog|grottes?\b|gouffre|\bavens?\b|stalact|stalagm|fossile|mineralo|volcan|karst|\bgorges\b|chaos rocheux"),
    ("dinosaures et paléontologie", set(), r"dinosaur|paleonto|fossile"),
    ("animaux", {"ZooAnimalPark", "VivariumAquarium", "TeachingFarm", "EquestrianCenter"}, r"animal|animaux|\bzoo|\bfaune|oiseaux?\b|ornitho|\bloups?\b|\bours\b|vautour|rapace|aquarium|reptile|insecte|abeilles?\b|chevaux|\bcheval\b|poneys?\b|\banes?\b|chevres?\b|brebis|bisons?\b|cigogne|flamants?\b|dauphins?\b|tortues?\b|papillons?\b"),
    ("biodiversité et nature", {"NaturalHeritage", "Forest", "Bog", "Swamp", "Pond", "Lake", "River", "Stream", "Waterfall", "Valley", "Plateau", "Mountain", "Peak", "Col", "AlpinePasture", "Plain"}, r"biodivers|\bfaune|\bflore\b|espace naturel|reserve naturelle|parc naturel|zone humide|\betangs?\b|marais|tourbiere|\bforets?\b|\blacs?\b"),
    ("botanique et jardins", {"ParkAndGarden", "Orchard"}, r"jardins?\b|botani|arboretum|roseraie|herbier"),
    ("environnement et développement durable", {"EducationalTrail"}, r"developpement durable|recycl|dechets|energies? renouvelables?|eolien|sentier (pedagogique|decouverte|d'interpretation)|education a l'environnement"),
    ("mer et littoral", {"Beach", "Marina", "UnderwaterRoute", "BeachClub", "YachtClub"}, r"\bmer\b|littoral|plages?\b|lagune|etang de thau|\bport\b|maritime|ocean|coquillage|huitres?\b|\bphare|\bdunes?\b"),
    ("montagne", {"Mountain", "Peak", "Col", "AlpinePasture", "DownhillSkiRun", "CrossCountrySkiTrail", "TobogganBobsleigh"}, r"montagnes?\b|\bsommet|canigou|\bestive|\bski\b"),
    ("eau et rivières", {"River", "Stream", "Canal", "RiverPort", "FluvialTour", "Source", "Waterfall", "Fountain"}, r"riviere|fleuve|\bcanal\b|cours d'eau|navigation fluviale|thermal|cascade"),
    ("agriculture et terroir", {"Farm", "Farmer", "Producer", "TeachingFarm", "Orchard", "Harvest", "FarmhouseInn", "Cooperative"}, r"agricult|elevage|maraich|fromagerie|oliveraie|safran|apicult|paysan|ferme pedagogique"),
    ("vigne et vin", {"Cellar", "BistroOrWineBar"}, r"\bvins?\b|\bvignes?\b|vignoble|viticult|domaine viticole|\bchais?\b|vendange|oenolog"),
    ("gastronomie", {"GourmetRestaurant", "Tasting", "TastingProvider", "LocalProductsShop", "Market", "CoveredMarket"}, r"gastronom|culinaire|degustation|chocolat|confiserie|produits? locaux"),
    ("art et peinture", {"ArtGalleryOrExhibitionGallery", "VisualArtsEvent"}, r"art contemporain|beaux-arts|artistes?\b|peintures?\b|peintres?\b|sculpt|galerie|soulages|matisse|fresque|street art|photograph|ceramique|exposition"),
    ("musique", {"Concert", "Recital", "Opera"}, r"musique|musical|concert|orchestre|chorale|\bopera|\bjazz"),
    ("théâtre et spectacle vivant", {"Theater", "TheaterEvent", "ShowEvent", "CircusPlace", "Cabaret"}, r"theatre|spectacle|\bdanse|marionnette|\bcontes?\b|comedie"),
    ("cinéma et image", {"Cinema", "ScreeningEvent", "Cinematheque"}, r"cinema|\bfilms?\b|audiovisuel"),
    ("littérature et lecture", {"Library", "Reading", "ArtistSigning"}, r"\blivres?\b|lecture|litterat|bibliotheque|mediatheque|ecrivain|poete|poesie|bande dessinee"),
    ("traditions et culture occitane", {"TraditionalCelebration", "Carnival"}, r"occitan|folklore|fete votive|\bferia|tauromachie|joutes|patrimoine immateriel|traditions? (locales?|populaires?)"),
    ("métiers et artisanat", {"CraftsmanShop"}, r"artisan|metiers? d'art|poterie|potier|souffleur de verre|tisserand|forgeron|ebeniste|savoir-faire|coutellerie"),
    ("sport et activités de plein air", {"LeisureSportActivityProvider", "SportsEvent", "ClimbingWall", "ViaFerrata", "AdventurePark", "NauticalCentre", "SwimmingPool", "EquestrianCenter", "Stadium", "Gymnasium"}, r"escalade|canoe|kayak|rafting|\bvtt\b|accrobranche|via ferrata|speleo|equitation|paddle|plongee|course d'orientation|tir a l'arc"),
    ("randonnée et balade", {"WalkingTour", "Rambling", "CyclingTour", "HorseTour", "EducationalTrail", "FitnessPath"}, r"randonnee|sentier|\bgr ?\d+\b"),
    ("loisirs et parc d'attractions", {"ThemePark", "LeisureComplex", "PlayArea", "MiniGolf", "BowlingAlley", "Trampoline", "SummerToboggan", "AdventurePark"}, r"parc d'attraction|parc de loisirs|aire de jeux|escape game|labyrinthe|laser ?game"),
    ("musée", {"Museum", "InterpretationCentre"}, r"\bmusee|museum|ecomusee|centre d'interpretation"),
    ("visite guidée", {"Visit"}, r"visites? guidees?|visites? commentees?|guide conferencier"),
    ("atelier pédagogique et jeune public", {"ChildrensEvent", "TeachingFarm", "EducationalTrail", "KidsClub", "ChildrensGite"}, r"pedagog|scolaires?\b|jeune public|ateliers? (pour )?enfants?|apprendre"),
    ("astronomie", set(), r"astronom|observatoire|planetarium|nuit des etoiles"),
    ("transports et patrimoine ferroviaire", {"TouristTrain", "RailBike", "TrainStation", "TourismCableCar"}, r"ferroviaire|locomotive|chemin de fer|velorail|train touristique"),
    ("ville et urbanisme", {"District", "CityHeritage"}, r"centre historique|vieille ville|urbanisme|ville d'art et d'histoire"),
    ("hébergement de groupe", {"GroupLodging", "CollectiveAccommodation", "StopOverOrGroupLodge", "CollectiveHostel", "YouthHostelAndInternationalCenter", "HolidayCentre", "ClubOrHolidayVillage", "ChildrensGite"}, r"classes? de decouverte|classes? vertes|centre de vacances|accueil de groupes"),
    ("hébergement", {"Accommodation"}, None),
    ("restauration", {"FoodEstablishment"}, None),
    ("services pratiques", {"ConvenientService", "PublicLavatories", "Parking", "ElectricVehicleChargingPoint", "ElectricBycicleChargingPoint", "ATM", "WifiHotSpot", "ServiceArea", "RestStop", "CamperVanArea", "RVServiceArea", "CarpoolArea", "BusStop", "TouristInformationCenter", "LocalTouristOffice", "PicnicArea"}, None),
    ("accessibilité handicap", set(), r"tourisme et handicap|\bpmr\b|mobilite reduite|handicap"),
]
THEMES = [(k, c, re.compile(p) if p else None) for k, c, p in THEMES]

# For these, the description mostly talks about the surroundings: themes come from categories + name only.
BASIC = {"Accommodation", "FoodEstablishment", "ConvenientService", "Store", "ServiceProvider", "Transport", "BusinessPlace"}
FREQ = {}  # category -> count, filled in main(); rarer = more specific


def cats_of(v):
    out = []
    for x in str(v).split("|"):
        c = x.split("#")[-1]
        if "datatourisme" in x and c not in SKIP and c not in out:
            out.append(c)
    return out


def specific_first(cats):
    return sorted((c for c in cats if c in CAT_FR), key=lambda c: FREQ.get(c, 0))


def commune(v):
    return str(v).split("#")[-1].strip() if pd.notna(v) else ""


def keywords(cats, name, desc):
    cs = set(cats)
    t = norm(name if cs & BASIC else f"{name} {desc}")
    kws = [k for k, kc, rx in THEMES if (cs & kc) or (rx is not None and rx.search(t))]
    kws += [CAT_FR[c].lower() for c in specific_first(cats)[:3]]
    return " ; ".join(dict.fromkeys(kws))


def generated_description(row, cats):
    spec = specific_first(cats)
    kind = CAT_FR[spec[0]] if spec else "Lieu touristique"
    lieu = commune(row.Code_postal_et_commune)
    s = f"{kind} « {str(row.Nom_du_POI).strip()} »"
    s += f" situé à {lieu}." if lieu else "."
    if len(spec) > 1:
        s += f" Catégories : {', '.join(CAT_FR[c].lower() for c in spec)}."
    if pd.notna(row.Classements_du_POI):
        cl = sorted({p.strip() for p in str(row.Classements_du_POI).replace("|", "#").split("#") if p.strip()})
        s += f" Labels et classements : {', '.join(cl[:4])}."
    if pd.notna(row.Periodes_regroupees):
        per = str(row.Periodes_regroupees).split("|")[0].replace("<->", " au ")
        s += f" Période : du {per}."
    return s


def main():
    df = pd.read_csv(SRC)
    hand = json.load(open(HAND, encoding="utf-8")) if os.path.exists(HAND) else {}

    cats = df.Categories_de_POI.map(cats_of)
    FREQ.update(pd.Series([c for cs in cats for c in cs]).value_counts().to_dict())
    df["Categories_de_POI"] = cats.map(lambda cs: " ; ".join(CAT_FR.get(c, c) for c in cs))

    src, desc = [], []
    for row, cs in zip(df.itertuples(), cats):
        if pd.notna(row.Description) and str(row.Description).strip():
            src.append("originale"); desc.append(str(row.Description).strip())
        elif row.URI_ID_du_POI in hand:
            src.append("redigee"); desc.append(hand[row.URI_ID_du_POI])
        else:
            src.append("generee"); desc.append(generated_description(row, cs))
    df["Description"] = desc
    df["Source_description"] = src
    df["Mots_cles"] = [keywords(cs, str(r.Nom_du_POI), r.Description) for r, cs in zip(df.itertuples(), cats)]

    df.to_csv(OUT, index=False, encoding="utf-8")
    print(df.Source_description.value_counts().to_string())
    print(f"Écrit {OUT} {df.shape}")


if __name__ == "__main__":
    main()
