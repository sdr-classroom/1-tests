# SDR - Tests for lab 1

## Running tests

Pour exécuter les tests fournis dans ce repo sur votre projet SDR, exécutez la commande suivante depuis la racine de ce repo:

```bash
python3 run_tests.py <path_to_your_project_root>
```

## Description du design des tests

Un test-case est défini par une fonction qui se contentera généralement d'appeler `run_command_blocks` avec une série de blocs à éxecuter. Un bloc est en gros un ensemble de commandes à exécuter sur un client donné, avec une fonction pensée pour vérifier que le résultat de ces commandes est bien celui attendu. Le fichier `command_block.py` contient la définition de la classe `CommandBlock` et la décrit plus en détail.

Le fichier `blocks.py` fourni un certain nombre de blocs de base, par exemple pour exécuter une commande de paiement, ou pour vérifier que l'état actuel du graphe de dettes est bien simplifié et valide par rapport aux paiements effectués.

Le fichier `run_tests.py` contient un certain nombre de fonction permettant ce fonctionnement, et une fonction `run_all_tests` qui exécute tous les test-cases fournis dans `test_cases.py`.