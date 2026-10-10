import unittest
from backend.conversation import demo_extract, response
from backend.models import Project

class ConversationTests(unittest.TestCase):
    def test_french_dates(self):
        for value in ('14 septembre 2026','14 sept. 2026','14/09/2026','14/09/26','14-09-2026','14.09.2026','2026-09-14'):
            with self.subTest(value=value):
                self.assertEqual(demo_extract(value,{})['date'],'2026-09-14')

    def test_invalid_date_not_accepted(self):
        self.assertNotIn('date',demo_extract('31 février 2026',{}))

    def test_users_complete_conversation(self):
        fields={}
        for text in ('moyen age','Je souhaite travailler avec ma classe de 5e sur le moyen age. Nous sommes 42 eleves et 4 accompagnateurs. Nous souhaitons faire une sortie sur une journée, en train lio, avec un départ le matin et un retour avant 19h','Toulouse le 14 septembre 2026','2026-10-14','allez simple','allez retour , 9h du matin'):
            fields=demo_extract(text,fields)
        self.assertEqual(fields['date'],'2026-10-14')
        self.assertEqual(fields['trip_type'],'round_trip')
        self.assertEqual(fields['earliest'],'09:00')
        self.assertEqual(fields['latest'],'19:00')
        self.assertEqual(fields['students']+fields['companions'],46)
        self.assertEqual(response(fields)[1],[])

    def test_trip_typos_and_hours(self):
        for phrase in ('allez retour','aller-retour','aller et retour','A/R','AR'):
            self.assertEqual(demo_extract(phrase,{})['trip_type'],'round_trip')
        self.assertEqual(demo_extract('allez simple',{})['trip_type'],'one_way')
        self.assertEqual(demo_extract('aller-retour dès 08h00 et retour avant 19h00',{})['earliest'],'08:00')
        self.assertEqual(demo_extract('départ à 9 heures 30, retour à 6h du soir',{})['latest'],'18:00')

    def test_optional_details_never_block(self):
        fields=demo_extract('Toulouse le 14/09/2026, 46 personnes, Moyen Âge, 9h à 19h',{})
        values,missing,_=response(fields)
        self.assertEqual(missing,[])
        self.assertEqual(values['visit_minutes'],120)
        self.assertEqual(Project(**values).group_size,46)

    def test_arrival_does_not_replace_departure(self):
        fields=demo_extract('de Toulouse à Carcassonne',{})
        self.assertEqual(fields['origin'],'Toulouse')
        self.assertEqual(fields['destination_station'],'Carcassonne')
        fields=demo_extract('destination Albi',fields)
        self.assertEqual(fields['origin'],'Toulouse')
        self.assertEqual(fields['destination_station'],'Albi')
