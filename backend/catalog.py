"""Curated demo catalogue. Access/opening values are explicitly demo assumptions."""
PLACES = [
    {'id':'carcassonne','city':'Carcassonne','title':'Les remparts racontent le Moyen Âge',
     'site':'Cité de Carcassonne','station':'Carcassonne','themes':['Moyen Âge','Histoire','Patrimoine'],
     'description':'Une journée pour lire une ville fortifiée, comprendre ses défenses et observer son architecture.',
     'activity':'Parcours des fortifications et carnet d’observation en équipe',
     'lat':43.2066,'lon':2.3637,'walk_minutes':32,'urban_minutes':18,'open_from':9,'open_to':17,
     'source':'https://www.remparts-carcassonne.fr/','art':'castle','color':'ochre'},
    {'id':'toulouse','city':'Toulouse','title':'L’histoire au cœur de la ville rose',
     'site':'Musée des Augustins','station':'Toulouse Matabiau','themes':['Moyen Âge','Histoire','Arts','Patrimoine'],
     'description':'Explorer les traces de l’histoire et relier les œuvres, les bâtiments et la vie de la cité.',
     'activity':'Observation du patrimoine et atelier pédagogique à confirmer auprès du lieu',
     'lat':43.5997,'lon':1.4488,'walk_minutes':19,'urban_minutes':12,'open_from':10,'open_to':17,
     'source':'https://www.augustins.org/','art':'city','color':'rose'},
    {'id':'albi','city':'Albi','title':'Une cité épiscopale à ciel ouvert',
     'site':'Cité épiscopale d’Albi','station':'Albi Ville','themes':['Moyen Âge','Histoire','Arts','Patrimoine'],
     'description':'Lire les façades, comparer les matériaux et découvrir le patrimoine monumental de la cité.',
     'activity':'Parcours d’architecture et découverte de la cathédrale Sainte-Cécile',
     'lat':43.9282,'lon':2.1427,'walk_minutes':17,'urban_minutes':12,'open_from':9,'open_to':17,
     'source':'https://www.albi-tourisme.fr/','art':'cathedral','color':'brick'},
    {'id':'montpellier','city':'Montpellier','title':'La science se découvre en chemin',
     'site':'Centre historique de Montpellier','station':'Montpellier Saint-Roch','themes':['Sciences','Nature','Histoire','Patrimoine'],
     'description':'Observer la ville, ses espaces végétalisés et son patrimoine autour d’un parcours d’enquête.',
     'activity':'Parcours urbain et scientifique construit avec l’enseignant',
     'lat':43.6119,'lon':3.8772,'walk_minutes':15,'urban_minutes':None,'open_from':9,'open_to':17,
     'source':'https://www.montpellier-tourisme.fr/','art':'garden','color':'sage'},
    {'id':'nimes','city':'Nîmes','title':'Sur les traces de l’Antiquité',
     'site':'Musée de la Romanité','station':'Nîmes Centre','themes':['Antiquité','Histoire','Arts'],
     'description':'Relier les vestiges romains à la vie quotidienne et comprendre l’organisation d’une cité antique.',
     'activity':'Découverte des collections et lecture du patrimoine romain',
     'lat':43.8345,'lon':4.3597,'walk_minutes':10,'urban_minutes':None,'open_from':10,'open_to':17,
     'source':'https://museedelaromanite.fr/','art':'arena','color':'sand'},
]


def get_place(place_id):
    return next((dict(p) for p in PLACES if p['id']==place_id),None)
