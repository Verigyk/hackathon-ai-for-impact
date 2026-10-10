import unittest
from unittest.mock import AsyncMock, patch
from backend.agents import chat
from backend.models import ChatMessage

KNOWN={'origin':'Toulouse','date':'2026-11-06','students':28,'companions':2,'theme':'Moyen Âge','trip_type':'round_trip','earliest':'08:00','latest':'19:00'}

class OllamaDialogueTests(unittest.IsolatedAsyncioTestCase):
    async def test_ready_message_names_the_actual_interface_button(self):
        mock=AsyncMock(return_value={'fields':{},'reply':"Les informations sont complètes. Cliquez sur le bouton 'Vérifier le voyage'."})
        with patch('backend.agents.llm_enabled',return_value=True),patch('backend.agents.llm_json',new=mock):
            result=await chat(ChatMessage(message='merci',fields=KNOWN))
        self.assertIn('Découvrir les sorties possibles',result['reply'])
        self.assertNotIn('sous le formulaire',result['reply'])
        self.assertNotIn('Vérifier le voyage',result['reply'])

    async def test_optional_model_guesses_do_not_block_guided_project(self):
        result_json={'fields':{'destination_id':'Destination non précisée','visit_minutes':'11h','students':99},'reply':'Nous avons besoin de la destination et du niveau.'}
        with patch('backend.agents.llm_enabled',return_value=True),patch('backend.agents.llm_json',new=AsyncMock(return_value=result_json)):
            result=await chat(ChatMessage(message='Toulouse le 6 novembre 2026, 28 élèves et 2 accompagnateurs, Moyen Âge, de 8h à 19h'))
        self.assertNotIn('destination_id',result['fields'])
        self.assertEqual(result['fields']['students'],28)
        self.assertEqual(result['missing'],[])
        self.assertIsNone(result['warning'])
        self.assertIn('Votre projet est prêt',result['reply'])

    async def test_ambiguous_change_preserves_all_values(self):
        with patch('backend.agents.llm_enabled',return_value=True), patch('backend.agents.llm_json',new=AsyncMock(return_value={'fields':{'date':'2026-11-20'},'reply':'Que voulez-vous modifier ?'})):
            result=await chat(ChatMessage(message='je veux changer ça',fields=KNOWN))
        self.assertEqual(result['fields']['date'],KNOWN['date'])
        self.assertIn('Que souhaitez-vous modifier',result['reply'])

    async def test_history_is_forwarded_and_model_reply_used(self):
        mock=AsyncMock(return_value={'fields':{'date':'2026-11-20'},'reply':'La date est mise à jour. Souhaitez-vous garder les horaires ?'})
        with patch('backend.agents.llm_enabled',return_value=True),patch('backend.agents.llm_json',new=mock):
            result=await chat(ChatMessage(message='le vingt novembre 2026',fields=KNOWN,history=[{'role':'assistant','text':'Quelle nouvelle date ?'}]))
        self.assertEqual(result['fields']['date'],'2026-11-20')
        self.assertTrue(result['reply'].startswith('La date est mise à jour'))
        self.assertEqual(mock.call_args.args[1]['history'][0]['text'],'Quelle nouvelle date ?')

    async def test_invalid_model_fields_do_not_enter_project(self):
        with patch('backend.agents.llm_enabled',return_value=True),patch('backend.agents.llm_json',new=AsyncMock(return_value={'fields':{'students':-10},'reply':'OK'})):
            result=await chat(ChatMessage(message='bonjour',fields=KNOWN))
        self.assertEqual(result['fields']['students'],28)
        self.assertEqual(result['provider'],'demo')
        self.assertIsNotNone(result['warning'])
