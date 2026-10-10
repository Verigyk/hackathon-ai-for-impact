"""Enrichit top-des-sites-touristiques-2021.csv (mots-clés, adresse, coordonnées) et exporte en JSON."""
import csv
import json
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "top-des-sites-touristiques-2021.csv"
DST = HERE / "top-des-sites-touristiques-2021-enrichi.json"

# nom du site -> (mots-clés, adresse, latitude, longitude)
ENRICH = {
    "ESPACE NAUTIQUE ATLANTIS": (
        ["sport", "aquatique", "piscine", "baignade", "loisirs", "natation", "détente", "bien-être", "toboggans", "famille", "activité physique", "intérieur"],
        "Rue Lavazière, 81000 Albi", 43.9239, 2.1319),
    "Réserve africaine de Sigean": (
        ["animaux", "zoo", "safari", "faune sauvage", "nature", "biodiversité", "sciences de la vie", "Afrique", "protection des espèces", "plein air", "éducatif", "famille"],
        "19 Chemin du Hameau du Lac, 11130 Sigean", 43.0486, 2.9672),
    "LES JACOBINS": (
        ["historique", "religieux", "gothique", "architecture", "couvent", "patrimonial", "Moyen Âge", "monument historique", "art sacré", "cloître", "Thomas d'Aquin", "culturel"],
        "Rue Lakanal, 31000 Toulouse", 43.6036, 1.4401),
    "PLANETOCEANWORLD": (
        ["aquarium", "océan", "biodiversité marine", "animaux", "sciences de la vie", "planétarium", "astronomie", "éducatif", "environnement", "écologie", "famille", "intérieur"],
        "Odysseum, Allée Ulysse, 34000 Montpellier", 43.6037, 3.9188),
    "AQUARIUM ONIRIA": (
        ["aquarium", "biodiversité marine", "poissons", "animaux", "Méditerranée", "océan", "sciences de la vie", "écologie", "éducatif", "environnement", "famille", "intérieur"],
        "Boulevard de la Jetée, 66140 Canet-en-Roussillon", 42.7042, 3.0383),
    "MUSEE TOULOUSE LAUTREC": (
        ["musée", "art", "peinture", "beaux-arts", "Toulouse-Lautrec", "affiches", "XIXe siècle", "culturel", "patrimonial", "palais de la Berbie", "UNESCO", "histoire de l'art"],
        "Palais de la Berbie, Place Sainte-Cécile, 81000 Albi", 43.9285, 2.1424),
    "Cathédrale": (
        ["historique", "religieux", "gothique", "cathédrale", "architecture", "patrimonial", "monument historique", "art sacré", "lieu de culte", "Moyen Âge", "grès rose", "culturel"],
        "Place d'Armes, 12000 Rodez", 44.3507, 2.5744),
    "ABBATIALE": (
        ["historique", "religieux", "roman", "abbaye", "UNESCO", "chemins de Compostelle", "Moyen Âge", "plus beaux villages de France", "patrimonial", "art sacré", "pèlerinage", "architecture"],
        "Place de la Liberté, 34150 Saint-Guilhem-le-Désert", 43.7334, 3.5496),
    "CATHEDRALE SAINT PIERRE DE MAGUELONE": (
        ["historique", "religieux", "roman", "cathédrale", "Moyen Âge", "patrimonial", "nature", "lagune", "littoral", "art sacré", "monument historique", "architecture"],
        "Domaine de Maguelone, 34750 Villeneuve-lès-Maguelone", 43.5133, 3.8611),
    "OBALIA": (
        ["thermalisme", "bien-être", "détente", "spa", "aquatique", "santé", "relaxation", "eau thermale", "loisirs", "balnéothérapie", "étang de Thau", "intérieur"],
        "Allée des Sources, 34540 Balaruc-les-Bains", 43.4417, 3.6775),
    "MAISON CARREE  -  NIMES": (
        ["historique", "Antiquité", "romain", "temple", "UNESCO", "architecture", "monument historique", "patrimonial", "archéologie", "culturel", "civilisation romaine", "histoire"],
        "Place de la Maison Carrée, 30000 Nîmes", 43.8384, 4.3561),
    "AEROSCOPIA": (
        ["aéronautique", "aviation", "musée", "sciences", "technologie", "Concorde", "Airbus", "industrie", "innovation", "histoire des techniques", "ingénierie", "éducatif"],
        "1 Allée André Turcat, 31700 Blagnac", 43.6595, 1.3687),
    "CATHEDRALE SAINT NAZAIRE": (
        ["historique", "religieux", "gothique", "cathédrale", "architecture", "patrimonial", "Moyen Âge", "art sacré", "lieu de culte", "panorama", "monument historique", "culturel"],
        "Plan des Albigeois, 34500 Béziers", 43.3405, 3.2101),
    "ESPACE GRAND BLEU": (
        ["sport", "aquatique", "piscine", "natation", "baignade", "loisirs", "détente", "bien-être", "activité physique", "famille", "littoral", "intérieur"],
        "195 Avenue du Golf, 34280 La Grande-Motte", 43.5655, 4.0700),
    "LES PETITS FERMIERS AU PAYS DE L'OR": (
        ["ferme pédagogique", "animaux", "agriculture", "nature", "ruralité", "éducatif", "jeunes enfants", "famille", "élevage", "plein air", "découverte", "sciences de la vie"],
        "Mas de Saint-Gilles, 34130 Lansargues", 43.6550, 4.0700),
    "VISITEURS DES 9 ECLUSES DE FONSERANES-": (
        ["patrimoine fluvial", "canal du Midi", "UNESCO", "ingénierie", "Pierre-Paul Riquet", "histoire des techniques", "XVIIe siècle", "navigation", "promenade", "patrimonial", "plein air", "génie civil"],
        "Rue du Canal, 34500 Béziers", 43.3364, 3.1956),
    "PONT DU GARD": (
        ["historique", "Antiquité", "romain", "aqueduc", "UNESCO", "ingénierie", "architecture", "nature", "patrimonial", "monument historique", "plein air", "civilisation romaine"],
        "400 Route du Pont du Gard, 30210 Vers-Pont-du-Gard", 43.9475, 4.5353),
    "Remparts et Château Comtal de Carcassonne": (
        ["historique", "Moyen Âge", "château", "remparts", "fortifications", "UNESCO", "catharisme", "architecture militaire", "patrimonial", "monument historique", "chevaliers", "culturel"],
        "1 Rue Viollet-le-Duc, 11000 Carcassonne", 43.2067, 2.3636),
    "L’ARCHIPEL PISCINE": (
        ["sport", "aquatique", "piscine", "natation", "baignade", "loisirs", "toboggans", "détente", "bien-être", "activité physique", "famille", "intérieur"],
        "Avenue du Sidobre, 81100 Castres", 43.6047, 2.2580),
    "Centre historique": (
        ["historique", "Antiquité", "romain", "Via Domitia", "Moyen Âge", "palais des Archevêques", "cathédrale", "patrimonial", "architecture", "urbain", "canal de la Robine", "culturel"],
        "Place de l'Hôtel de Ville, 11100 Narbonne", 43.1840, 3.0040),
    "MUSEUM": (
        ["sciences naturelles", "muséum", "biodiversité", "préhistoire", "paléontologie", "dinosaures", "animaux", "évolution", "sciences de la vie", "éducatif", "environnement", "intérieur"],
        "35 Allées Jules Guesde, 31000 Toulouse", 43.5940, 1.4497),
    "Aven Armand": (
        ["grotte", "spéléologie", "géologie", "stalagmites", "nature", "souterrain", "Causses", "UNESCO", "sciences de la Terre", "patrimoine naturel", "karst", "Lozère"],
        "Aven Armand, 48150 Hures-la-Parade", 44.2228, 3.3586),
    "SITE DES ORGUES": (
        ["géologie", "nature", "cheminées de fées", "érosion", "paysage", "randonnée", "sciences de la Terre", "patrimoine naturel", "plein air", "balade", "Pyrénées-Orientales", "découverte"],
        "Chemin des Orgues, 66130 Ille-sur-Têt", 42.6772, 2.6156),
    "CITE DE L ESPACE": (
        ["espace", "astronomie", "sciences", "technologie", "fusée", "planétarium", "conquête spatiale", "parc à thème", "éducatif", "innovation", "astronaute", "famille"],
        "Avenue Jean Gonord, 31500 Toulouse", 43.5866, 1.4934),
    "CHÂTEAU ROYAL": (
        ["historique", "château", "fortifications", "Moyen Âge", "rois de Majorque", "architecture militaire", "monument historique", "patrimonial", "littoral", "Méditerranée", "Vauban", "culturel"],
        "Quai de l'Amirauté, 66190 Collioure", 42.5254, 3.0838),
    "MUSÉE DU BONBON HARIBO  -  UZES": (
        ["musée", "confiserie", "bonbons", "industrie", "gourmandise", "famille", "jeunes enfants", "ludique", "histoire de l'entreprise", "fabrication", "découverte", "intérieur"],
        "Pont des Charrettes, 30700 Uzès", 44.0013, 4.4103),
    "TRAIN À VAPEUR DES CÉVÉNNES  -  ANDUZE": (
        ["train", "chemin de fer", "locomotive à vapeur", "patrimoine ferroviaire", "Cévennes", "nature", "paysage", "histoire des techniques", "balade", "famille", "transport", "découverte"],
        "38 Place de la Gare, 30140 Anduze", 44.0518, 3.9853),
    "Cité médiévale de Carcassonne": (
        ["historique", "Moyen Âge", "cité médiévale", "remparts", "fortifications", "UNESCO", "château", "catharisme", "Viollet-le-Duc", "patrimonial", "architecture militaire", "culturel"],
        "La Cité, 11000 Carcassonne", 43.2061, 2.3640),
    "RETENUE DE LA RAHO": (
        ["lac", "nature", "plein air", "baignade", "sport nautique", "randonnée", "vélo", "pêche", "loisirs", "pique-nique", "famille", "environnement"],
        "Route du Lac, 66180 Villeneuve-de-la-Raho", 42.6383, 2.9156),
    "BASILIQUE SAINT SERNIN": (
        ["historique", "religieux", "roman", "basilique", "UNESCO", "chemins de Compostelle", "pèlerinage", "Moyen Âge", "art sacré", "lieu de culte", "architecture", "monument historique"],
        "Place Saint-Sernin, 31000 Toulouse", 43.6083, 1.4421),
    "Grottes de Bétharram": (
        ["grotte", "spéléologie", "géologie", "stalactites", "souterrain", "petit train", "barque", "nature", "sciences de la Terre", "patrimoine naturel", "Pyrénées", "famille"],
        "Grottes de Bétharram, 65270 Saint-Pé-de-Bigorre", 43.1040, -0.1870),
    "TOUR MAGNE  -  NIMES": (
        ["historique", "Antiquité", "romain", "tour", "remparts", "panorama", "jardins de la Fontaine", "monument historique", "patrimonial", "archéologie", "civilisation romaine", "plein air"],
        "Jardins de la Fontaine, Mont Cavalier, 30000 Nîmes", 43.8414, 4.3497),
    "MOISSAC Cloître": (
        ["historique", "religieux", "roman", "cloître", "abbaye", "UNESCO", "chemins de Compostelle", "sculpture", "Moyen Âge", "art sacré", "patrimonial", "architecture"],
        "6 Place Durand de Bredon, 82200 Moissac", 44.1056, 1.0853),
    "BAIE DE PAULILLES": (
        ["nature", "littoral", "Méditerranée", "plage", "espace naturel protégé", "biodiversité", "histoire industrielle", "dynamite", "randonnée", "environnement", "Conservatoire du littoral", "plein air"],
        "Route Départementale 914, 66660 Port-Vendres", 42.5025, 3.1272),
    "BAMBOUSERAIE DE PRAFRANCE SAS  -  GENERARGUES": (
        ["jardin", "botanique", "bambous", "nature", "exotisme", "végétal", "Asie", "promenade", "sciences de la vie", "Cévennes", "plein air", "paysage"],
        "552 Rue de Montsauve, 30140 Générargues", 44.0731, 3.9914),
    "GROTTE DE LA COCALIERE - COURRY": (
        ["grotte", "spéléologie", "géologie", "souterrain", "concrétions", "petit train", "préhistoire", "nature", "sciences de la Terre", "patrimoine naturel", "Cévennes", "famille"],
        "Route D904, 30500 Courry", 44.3069, 4.1500),
    "ABATTOIRS": (
        ["musée", "art moderne", "art contemporain", "exposition", "Picasso", "culturel", "création", "arts plastiques", "FRAC", "architecture industrielle", "histoire de l'art", "intérieur"],
        "76 Allées Charles de Fitte, 31300 Toulouse", 43.6000, 1.4294),
    "CAP DECOUVERTE PARC DE LOISIRS": (
        ["loisirs", "sport", "parc", "plein air", "lac", "baignade", "glisse", "aventure", "patrimoine minier", "famille", "activités nautiques", "nature"],
        "Cap'Découverte, 81450 Le Garric", 44.0233, 2.1550),
    "LE JARDIN DES MARTELS": (
        ["jardin", "botanique", "fleurs", "nature", "jardin remarquable", "végétal", "paysage", "promenade", "petit train", "ferme", "sciences de la vie", "plein air"],
        "Les Martels, 81500 Giroussens", 43.7578, 1.7703),
    "Sanctuaire de Lourdes": (
        ["historique", "religieux", "culturel", "patrimonial", "architectural", "touristique", "spirituel", "pèlerinage", "monument historique", "lieu de culte", "art sacré", "patrimoine culturel"],
        "1 Avenue Monseigneur Théas, 65100 Lourdes", 43.0975, -0.0581),
    "MUSEE FABRE": (
        ["musée", "beaux-arts", "peinture", "sculpture", "art", "Soulages", "histoire de l'art", "culturel", "patrimonial", "collections", "exposition", "intérieur"],
        "39 Boulevard Bonne Nouvelle, 34000 Montpellier", 43.6119, 3.8810),
    "LES ARÈNES DE NÎMES  -  NIMES": (
        ["historique", "Antiquité", "romain", "amphithéâtre", "gladiateurs", "architecture", "monument historique", "patrimonial", "archéologie", "spectacles", "civilisation romaine", "culturel"],
        "Boulevard des Arènes, 30000 Nîmes", 43.8350, 4.3597),
    "MUSEE DE LA ROMANITE - NIMES": (
        ["musée", "Antiquité", "romain", "archéologie", "histoire", "mosaïques", "civilisation romaine", "multimédia", "patrimonial", "culturel", "éducatif", "intérieur"],
        "16 Boulevard des Arènes, 30000 Nîmes", 43.8343, 4.3608),
    "CATHÉDRALE STE CECILE Le Chœur": (
        ["historique", "religieux", "gothique méridional", "cathédrale", "UNESCO", "brique", "art sacré", "fresques", "Moyen Âge", "lieu de culte", "architecture", "patrimonial"],
        "Place Sainte-Cécile, 81000 Albi", 43.9286, 2.1430),
    "TOURS ET REMPARTS D'AIGUES MORTES  -  AIGUES MORTES": (
        ["historique", "Moyen Âge", "remparts", "fortifications", "Saint Louis", "croisades", "architecture militaire", "Camargue", "monument historique", "patrimonial", "salins", "culturel"],
        "Place Anatole France, 30220 Aigues-Mortes", 43.5662, 4.1912),
    "SEAQUARIUM - GRAU DU ROI": (
        ["aquarium", "biodiversité marine", "requins", "phoques", "animaux", "Méditerranée", "océan", "sciences de la vie", "protection des espèces", "éducatif", "famille", "intérieur"],
        "Avenue du Palais de la Mer, 30240 Le Grau-du-Roi", 43.5268, 4.1376),
    "Abbaye de Flaran": (
        ["historique", "religieux", "abbaye", "cistercien", "Moyen Âge", "cloître", "art", "collection Simonow", "jardins", "patrimonial", "architecture", "monument historique"],
        "Abbaye de Flaran, 32310 Valence-sur-Baïse", 43.8608, 0.3961),
    "AQUALAND": (
        ["parc aquatique", "toboggans", "baignade", "loisirs", "sensations", "été", "plein air", "famille", "aquatique", "détente", "jeux", "sport"],
        "Avenue Armand Lanoux, 66750 Saint-Cyprien", 42.6219, 3.0306),
    "MAISON DE LA NATURE": (
        ["nature", "espace naturel protégé", "étangs", "zones humides", "oiseaux", "ornithologie", "biodiversité", "environnement", "éducation à l'environnement", "sentier", "plein air", "sciences de la vie"],
        "Chemin de l'Estelle, 34970 Lattes", 43.5560, 3.9180),
    "Pic du Midi de Bigorre": (
        ["montagne", "observatoire", "astronomie", "sciences", "Pyrénées", "panorama", "téléphérique", "altitude", "nature", "climat", "météorologie", "patrimoine naturel"],
        "Pic du Midi, 65200 Bagnères-de-Bigorre", 42.9364, 0.1425),
    "RESERVE MAS LARRIEU": (
        ["nature", "réserve naturelle", "biodiversité", "littoral", "embouchure du Tech", "zones humides", "oiseaux", "environnement", "espace naturel protégé", "sentier", "plein air", "écologie"],
        "Mas Larrieu, 66700 Argelès-sur-Mer", 42.5800, 3.0400),
    "VISITEURS DU PIC SAINT LOUP (ECO COMPTEUR)": (
        ["randonnée", "montagne", "nature", "panorama", "garrigue", "plein air", "sport", "géologie", "ermitage", "paysage", "patrimoine naturel", "effort physique"],
        "Pic Saint-Loup, 34270 Saint-Mathieu-de-Tréviers", 43.7797, 3.8131),
    "Montain Luge Hautacam": (
        ["luge", "sensations", "loisirs", "montagne", "Pyrénées", "plein air", "glisse", "sport", "famille", "panorama", "nature", "attraction"],
        "Station Hautacam, 65400 Beaucens", 43.0080, -0.0120),
    "Le Parc Animalier des Pyrénées": (
        ["animaux", "zoo", "faune pyrénéenne", "montagne", "nature", "ours", "loups", "sciences de la vie", "protection des espèces", "plein air", "famille", "éducatif"],
        "60 Avenue des Pyrénées, 65400 Ayzac-Ost", 43.0153, -0.0950),
    "GROTTE DES DEMOISELLES": (
        ["grotte", "spéléologie", "géologie", "stalagmites", "souterrain", "funiculaire", "nature", "sciences de la Terre", "patrimoine naturel", "karst", "Cévennes", "découverte"],
        "Hameau des Lauriers, 34190 Saint-Bauzille-de-Putois", 43.8806, 3.7550),
    "FORT LIBERIA": (
        ["historique", "Vauban", "fortifications", "UNESCO", "architecture militaire", "XVIIe siècle", "montagne", "panorama", "monument historique", "patrimonial", "Pyrénées", "culturel"],
        "Fort Libéria, 66500 Villefranche-de-Conflent", 42.5900, 2.3678),
    "ERMITAGE SAINT ANTOINE": (
        ["historique", "religieux", "ermitage", "gorges de Galamus", "nature", "randonnée", "spirituel", "paysage", "patrimonial", "montagne", "plein air", "lieu de culte"],
        "Gorges de Galamus, 66220 Saint-Paul-de-Fenouillet", 42.8417, 2.4700),
    "CENTRE BALNEAIRE RAOUL FONQUERNE": (
        ["sport", "aquatique", "piscine", "natation", "baignade", "loisirs", "bien-être", "détente", "activité physique", "famille", "littoral", "intérieur"],
        "Avenue Jean Mermoz, 34200 Sète", 43.4011, 3.6814),
}


def main():
    with SRC.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    out = []
    for r in rows:
        name = r["SITES TOURISTIQUES"]
        kw, addr, lat, lon = ENRICH[name]
        total = r["TOTAL"].strip()
        out.append({
            "site": name,
            "commune": r["commune"],
            "total_visites": int(float(total)) if total else None,
            "mots_cles": kw,
            "adresse": addr,
            "latitude": lat,
            "longitude": lon,
        })
    DST.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(out)} sites -> {DST.name}")


if __name__ == "__main__":
    main()
