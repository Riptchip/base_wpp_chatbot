import os

RESPONSES = {
    'base': {
        'registered': [
            {
                'type': 'text',
                'base_content':
                    'Oi {name}, tudo bem? Vimos que você já ' \
                    'se cadastrou com a gente, assim ' \
                    'que possível eu já falo com você. Vou ' \
                    'fazer de tudo para te ajudar nesse ' \
                    'seu novo objetivo.',
                'parent_content': '',
                'athlete_content': '',
                'other_content': ''
            },
            {
                'type': 'text',
                'base_content':
                    'Enquanto isso, você já conhece o nosso Instagram?\n' \
                    f'www.instagram.com/{os.environ["INSTAGRAM_ACC"]}',
                'parent_content': '',
                'athlete_content': '',
                'other_content': ''
            }
        ],
        'site_follow_up_yes': [
            {
                'type': 'text',
                'base_content':
                    'Perfeito, {name}! Vamos lá então',
                'parent_content': '',
                'athlete_content': '',
                'other_content': ''
            }
        ],
        'site_follow_up_no': [
            {
                'type': 'text',
                'base_content':
                    'Certo, {name}. Em breve entraremos em contato!',
                'parent_content': '',
                'athlete_content': '',
                'other_content': ''
            }
        ],
        'initial': [
            {
                'type': 'text',
                'base_content':
                    f'Olá, tudo bem? Aqui é o {os.environ["ATTENDANT_NAME"]}.',
                'parent_content': '',
                'athlete_content': '',
                'other_content': ''
            }
        ],
        'questions': [
            {
                'type': 'text',
                'base_content': 
                    'Olá {name}, seja bem vindo. ' \
                    'Estou aqui para ajudar ',
                'parent_content':
                    'você e o seu filho a desenvolver o ' \
                    'potencial máximo e alcançar os seus ' \
                    'sonhos.',
                'athlete_content':
                    'a desenvolver o seu potencial máximo ' \
                    'e alcançar os seus sonhos.',
                'other_content':
                    'pessoas a desenvolver o potencial ' \
                    'máximo e alcançar os seus sonhos.'
            },
            {
                'type': 'text',
                'base_content':
                    'Para darmos sequência, poderia ' \
                    'me responder algumas perguntas? ' \
                    'São apenas {n_missing_info}. Vamos lá?',
                'parent_content': '',
                'athlete_content': '',
                'other_content': ''
            }
        ],
        'final': [
            {
                'type': 'text',
                'base_content':
                    'Ótimo {name}, muito obrigado. Vou ' \
                    'verificar nossas disponibilidades e ' \
                    'falo com você. Ok?',
                'parent_content': '',
                'athlete_content': '',
                'other_content': ''
            },
            {
                'type': 'text',
                'base_content':
                    'Ou se tiver alguma dúvida já pode me ' \
                    'perguntar direto mandando mensagem para ' \
                    'o meu número pessoal.',
                'parent_content': '',
                'athlete_content': '',
                'other_content': ''
            },
            {
                'type': 'contacts',
                'contacts': [{
                    "name": {
                        "first_name": os.environ["ATTENDANT_NAME"].split(' ')[0],
                        "last_name": os.environ["ATTENDANT_NAME"].split(' ')[-1],
                        "formatted_name": os.environ["ATTENDANT_NAME"]
                    },
                    "phones": [{
                        "phone": os.environ["ATTENDANT_NUMBER_FORMATTED"],
                        "wa_id": os.environ["ATTENDANT_NUMBER"],
                        "type": "MOBILE"
                    }]
                }]
            }
        ]
    },
    'info': {
        'role': [
            {
                'type': 'interactive',
                'base_content': 'Você é:',
                'parent_content': '',
                'athlete_content': '',
                'other_content': '',
                'options': ['Pai ou responsável', 'Atleta-estudante', 'Outro']
            }
        ],
        'name': [
            {
                'type': 'text',
                'base_content': 'Como você gostaria que eu te chamasse?',
                'parent_content': '',
                'athlete_content': '',
                'other_content': '',
            }
        ],
        'athlete_name': [
            {
                'type': 'text',
                'base_content': '',
                'parent_content': 'Nome completo do Atleta/Estudante',
                'athlete_content': 'Seu nome completo',
                'other_content': 'Nome completo do Atleta/Estudante',
            }            
        ],
        'athlete_birth': [
            {
                'type': 'text',
                'base_content': 'Data de Nascimento',
                'parent_content': ' do Atleta/Estudante',
                'athlete_content': '',
                'other_content': ' do Atleta/Estudante',
            }            
        ],
        'sport': [
            {
                'type': 'interactive',
                'base_content': 'Qual esporte?',
                'parent_content': '',
                'athlete_content': '',
                'other_content': '',
                'options': ['Futebol', 'Tênis', 'Basquete', 'Vôlei', 'Futebol Americano', 'Atletismo', 'Golfe', 'Beisebol', 'Cross Country', 'Lacrosse', 'Performance']
            }
        ],
        'email': [
            {
                'type': 'text',
                'base_content': 'Seu melhor email',
                'parent_content': '',
                'athlete_content': '',
                'other_content': ''
            }            
        ],
        'date_to_go': [
            {
                'type': 'text',
                'base_content': 'Qual é a data que ',
                'parent_content': 
                    'seu filho está ' \
                    'pensando em ir para o centro de treinamento?',
                'athlete_content':
                    'você está ' \
                    'pensando em ir para o centro de treinamento?',
                'other_content': 
                    'você está ' \
                    'pensando para o Atleta/Estudante ' \
                    'ir o centro de treinamento?'
            }            
        ]
    },
    'instruction': {
        'role': [
            {
                'type': 'text',
                'base_content': 'Opção inválida, por favor responda com um número entre 1 e 3',
                'parent_content': '',
                'athlete_content': '',
                'other_content': ''
            }
        ],
        'name': [
            {
                'type': 'text',
                'base_content': 'Certo, mas antes de tudo, como você gostaria que eu te chamasse?',
                'parent_content': '',
                'athlete_content': '',
                'other_content': ''
            } 
        ],
        'athlete_name': [
            {
                'type': 'text',
                'base_content': 'Por favor, responda somente com o ',
                'parent_content': 'nome completo do atleta',
                'athlete_content': 'seu nome completo',
                'other_content': 'nome completo do atleta'
            }
        ],
        'athlete_birth': [
            {
                'type': 'text',
                'base_content': 'Por favor, responda com a data no formato dia/mês/ano. Ex: 01/01/2010.\nO atleta deve ter entre 5 e 20 anos',
                'parent_content': '',
                'athlete_content': '',
                'other_content': ''
            }
        ],
        'sport': [
            {
                'type': 'text',
                'base_content': 'Opção inválida, por favor responda com um número entre 1 e 11',
                'parent_content': '',
                'athlete_content': '',
                'other_content': ''
            }
        ],
        'email': [
            {
                'type': 'text',
                'base_content': 'Mande um email válido, por favor',
                'parent_content': '',
                'athlete_content': '',
                'other_content': ''
            }
        ]
    }
} 

INFO_TRANSLATION = {
    'logger': 'logger',
    'id': 'id',
    'role': 'Papel',
    'name': 'Nome/Apelido',
    'phone': 'Telefone',
    'email': 'E-mail',
    'athlete_name': 'Nome Completo do atleta',
    'athlete_birth': 'Data de Nascimento do atleta',
    'sport': 'Esporte',
    'date_to_go': 'Data que pretende ir',
    'gender': 'Sexo',
    'n_missing_info': 'n_missing_info',
    'representant': 'ID do representante no Agendor'
}